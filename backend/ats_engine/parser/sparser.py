"""
Resume JSON Parser — Production Ready
======================================
Parses a raw resume JSON (extracted via OCR/layout tools) into a clean,
structured schema using:
  - Regex for atomic fields (email, phone, URL, date, score/GPA)
  - Keyword-anchored section splitting (compiler-style tokenisation)
  - Sub-parsers per section (experience, projects, education, etc.)

Fixes applied
-------------
  1. Section title regex now also matches titles ending with ":" (e.g. "PROFESSIONAL SUMMARY:")
  2. Name/role extraction now falls back to the first lines of left_content when header is null
  3. Pass-through detection: if the input is already a parsed schema (has "info" key with "name"),
     the parser returns it as-is (handles Data 2 case).
  4. Experience/Projects/Education sub-parsers now also handle date formats like
     "07 March, 2031" and "2024 - 2028" (year-only ranges).
  5. "RELEVANT PROJECTS" added as a trigger phrase for projects section.

Usage
-----
    from resume_parser import ResumeParser

    with open("raw_resume.json") as f:
        raw = json.load(f)

    parser = ResumeParser(raw)
    result = parser.parse()
    print(json.dumps(result, indent=2))
"""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("resume_parser")


# ─────────────────────────────────────────────
# ① ATOMIC REGEX PATTERNS
# ─────────────────────────────────────────────
class Patterns:
    EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
    PHONE = re.compile(r"(?:\+?\d[\d\s\-().]{7,}\d)")
    URL = re.compile(
        r"(?:https?://|www\.)[^\s\"'<>\n]+"
        r"|[a-zA-Z0-9\-]+\.github\.io[^\s\"'<>\n]*",
        re.IGNORECASE,
    )
    _MONTH = r"(?:JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)"
    DATE_RANGE = re.compile(
        rf"({_MONTH}\s+\d{{4}})\s*[-–]\s*({_MONTH}\s+\d{{4}}|PRESENT)",
        re.IGNORECASE,
    )
    # FIX: also match "DD Month, YYYY - DD Month, YYYY | PRESENT" and "YYYY - YYYY"
    FULL_DATE_RANGE = re.compile(
        r"(\d{{1,2}}\s+\w+,?\s+\d{{4}}|\d{{4}})\s*[-–]\s*(\d{{1,2}}\s+\w+,?\s+\d{{4}}|\d{{4}}|PRESENT)",
        re.IGNORECASE,
    )
    SINGLE_DATE = re.compile(
        rf"(?:JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)\s+\d{{4}}",
        re.IGNORECASE,
    )
    GPA = re.compile(r"GPA\s*:\s*([\d.]+)\s*/\s*([\d.]+)", re.IGNORECASE)
    SCORE = re.compile(r"SCORE\s*:\s*([\d.]+)\s*/\s*([\d.]+)", re.IGNORECASE)
    PIPE = re.compile(r"\|")
    # Year-only range: "2024 - 2028"
    YEAR_RANGE = re.compile(r"\b(\d{4})\s*[-–]\s*(\d{4}|PRESENT)\b", re.IGNORECASE)
    # Date with day + full month name: "07 March, 2031"
    LONG_DATE = re.compile(
        r"\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4}",
        re.IGNORECASE,
    )
    LONG_DATE_RANGE = re.compile(
        r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4})\s*[-–]\s*(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4}|PRESENT)",
        re.IGNORECASE,
    )


def find_any_date_range(line: str):
    """Try all date range patterns; return (start, end, match_obj) or None."""
    for pat in [Patterns.DATE_RANGE, Patterns.LONG_DATE_RANGE, Patterns.YEAR_RANGE]:
        m = pat.search(line)
        if m:
            return m
    return None


# ─────────────────────────────────────────────
# ② SECTION-TITLE TOKEN TABLE
# ─────────────────────────────────────────────
SECTION_TOKENS: list[tuple[str, list[str]]] = [
    ("contact", ["CONTACT"]),
    (
        "experience",
        [
            "EXPERIENCE",
            "JOB EXPERIENCE",
            "WORK EXPERIENCE",
            "PROFESSIONAL EXPERIENCE",
            "EMPLOYMENT",
        ],
    ),
    ("education", ["EDUCATION", "ACADEMIC BACKGROUND", "ACADEMICS"]),
    (
        "projects",
        [
            "PROJECTS",
            "PROJECT",
            "PERSONAL PROJECTS",
            "ACADEMIC PROJECTS",
            "SIDE PROJECTS",
            "RELEVANT PROJECTS",  # FIX: added
        ],
    ),
    (
        "skills",
        [
            "TECH SKILLS",
            "TECHNICAL SKILLS",
            "SKILLS",
            "CORE COMPETENCIES",
            "TECHNOLOGIES",
            "AREAS OF EXPERTISE",  # FIX: added
        ],
    ),
    ("soft_skills", ["SOFT SKILLS", "INTERPERSONAL SKILLS"]),
    ("languages", ["LANGUAGES", "LANGUAGE"]),
    (
        "achievements",
        [
            "ACHIEVEMENTS",
            "ACHIEVEMENTS & HACKATHONS",
            "HACKATHONS",
            "AWARDS",
            "CERTIFICATIONS",
            "ACCOMPLISHMENTS",
        ],
    ),
    (
        "objective",
        [
            "OBJECTIVE",
            "SUMMARY",
            "PROFILE",
            "PROFESSIONAL SUMMARY",
            "ABOUT ME",
            "ABOUT",
            "PROFILE SUMMARY",
        ],
    ),
]

_all_titles = [t for _, titles in SECTION_TOKENS for t in titles]
# FIX: Allow optional trailing colon on section titles (e.g. "PROFESSIONAL SUMMARY:")
_title_re_str = (
    r"^("
    + "|".join(re.escape(t) for t in sorted(_all_titles, key=len, reverse=True))
    + r"):?\s*$"  # <-- added :? here
)
SECTION_TITLE_RE = re.compile(_title_re_str, re.IGNORECASE | re.MULTILINE)


def _canonical_key(matched_title: str) -> str:
    mt = matched_title.upper().strip().rstrip(":")
    for key, triggers in SECTION_TOKENS:
        for trigger in triggers:
            if mt == trigger.upper():
                return key
    return "unknown"


# ─────────────────────────────────────────────
# ③ DATA MODELS
# ─────────────────────────────────────────────
@dataclass
class ContactInfo:
    name: str = ""
    role: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    website: str = ""


@dataclass
class ExperienceEntry:
    title: str = ""
    company: str = ""
    joined: str = ""
    left: str = ""
    description: str = ""


@dataclass
class EducationEntry:
    degree: str = ""
    institution: str = ""
    started: str = ""
    ended: str = ""
    score: str = ""
    score_max: str = ""
    score_type: str = ""


@dataclass
class ProjectEntry:
    title: str = ""
    started: str = ""
    ended: str = ""
    description: str = ""
    technologies: list[str] = field(default_factory=list)
    url: str = ""


@dataclass
class ResumeOutput:
    info: dict[str, Any] = field(default_factory=dict)
    about: str = ""
    skills: list[str] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    experience: list[dict] = field(default_factory=list)
    education: list[dict] = field(default_factory=list)
    projects: list[dict] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)
    raw_sections: dict[str, str] = field(default_factory=dict)


# ─────────────────────────────────────────────
# ④ TOKENISER
# ─────────────────────────────────────────────
def tokenise_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    lines = text.splitlines()

    current_key: str | None = None
    buffer: list[str] = []

    def flush():
        if current_key is not None:
            body = "\n".join(buffer).strip()
            if current_key in sections:
                sections[current_key] = sections[current_key] + "\n" + body
            else:
                sections[current_key] = body
        buffer.clear()

    for line in lines:
        stripped = line.strip()
        m = SECTION_TITLE_RE.match(stripped)
        if m:
            flush()
            current_key = _canonical_key(m.group(1))
            logger.debug("Section token: %s  →  key=%s", stripped, current_key)
        else:
            buffer.append(line)

    flush()
    return sections


# ─────────────────────────────────────────────
# ⑤ SUB-PARSERS
# ─────────────────────────────────────────────


# ── 5a. Header / preamble parser ──
def parse_header(header_text: str | None) -> tuple[str, str]:
    if not header_text:
        return "", ""
    lines = [l.strip() for l in header_text.strip().splitlines() if l.strip()]
    if not lines:
        return "", ""
    name = lines[0]
    role = " | ".join(lines[1:]) if len(lines) > 1 else ""
    return name, role


# FIX: Extract name/role from preamble text (lines before first section heading)
def extract_name_role_from_preamble(preamble: str) -> tuple[str, str]:
    """
    When there is no explicit header field, the first line(s) of the content
    before any section heading contain the name and role.
    Heuristic: first non-empty line = name, second = role (if it doesn't look like contact info).
    """
    lines = [l.strip() for l in preamble.splitlines() if l.strip()]
    if not lines:
        return "", ""

    name = ""
    role = ""
    for i, line in enumerate(lines):
        # Skip lines that look like contact info
        if Patterns.EMAIL.search(line):
            break
        if Patterns.PHONE.search(line):
            break
        if Patterns.URL.search(line):
            break
        if not name:
            name = line
        elif not role:
            role = line
            break

    return name, role


# ── 5b. Contact parser ──
def parse_contact(text: str) -> dict[str, str]:
    info: dict[str, str] = {}

    m = Patterns.EMAIL.search(text)
    if m:
        info["email"] = m.group(0)

    m = Patterns.PHONE.search(text)
    if m:
        info["phone"] = m.group(0).strip()

    clean_text = re.sub(r"-\n\s*", "", text)
    m = Patterns.URL.search(clean_text)
    if m:
        info["website"] = m.group(0).strip()

    addr_match = re.search(
        r"(?:^|\n)Address\s*:\s*([^\n]+(?:\n(?!(?:Website|Phone|Email|LinkedIn)\b)[^\n@][^\n]*)*)",
        text,
        re.IGNORECASE,
    )
    if addr_match:
        raw_addr = addr_match.group(1)
        addr_lines = [
            l.strip()
            for l in raw_addr.splitlines()
            if l.strip()
            and "@" not in l
            and not re.match(r"^\+?\d[\d\s\-]{6,}", l.strip())
            and not re.match(
                r"^(Website|Phone|Email|LinkedIn)\b", l.strip(), re.IGNORECASE
            )
        ]
        info["address"] = ", ".join(addr_lines)

    return info


# ── 5c. Experience sub-parser ──
# FIX: broadened date detection to include long-form dates like "07 March, 2031 - Present"
def _split_experience_entries(text: str) -> list[tuple[str, str, str]]:
    """
    Returns list of (company_title_line, date_line, body) tuples.
    Detects entry boundaries by looking for a line followed immediately by a date-range line.
    """
    lines = text.splitlines()
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        # Check if next non-empty line is a date range (entry header pattern)
        # Pattern: COMPANY\nROLE | DATE
        # or: COMPANY\nROLE | DATE\n  (all on one line separated by |)
        # Also handle: ROLE | DATE on same line
        date_m = find_any_date_range(line)
        if date_m and i > 0:
            # Date is on the current line — title is previous non-empty line
            # Collect body
            body_lines = []
            j = i + 1
            while j < len(lines):
                if find_any_date_range(lines[j].strip()) and j > i + 1:
                    # Check if the line before this is a heading (not body text)
                    prev = lines[j - 1].strip() if j > 0 else ""
                    if prev and not prev.startswith(("•", "-", "–")):
                        break
                body_lines.append(lines[j])
                j += 1
            entries.append((lines[i - 1].strip(), line, "\n".join(body_lines).strip()))
            i = j
        else:
            i += 1
    return entries


def parse_experience(text: str) -> list[dict]:
    """
    Handles two date formats:
      1. "ROLE - COMPANY\nJAN 2023 - FEB 2024"  (original)
      2. "COMPANY\nROLE | 07 March, 2031 - Present"  (new format)
    """
    entries: list[dict] = []
    lines = text.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        date_m = find_any_date_range(line)
        if date_m:
            # The date is embedded in this line — extract role and company
            # Everything before the date on this line = role info
            pre_date = line[: date_m.start()].strip().rstrip("|").strip()
            company = lines[i - 1].strip() if i > 0 else ""
            title = pre_date if pre_date else company
            if pre_date and company and pre_date != company:
                role_title = pre_date
                company_name = company
            else:
                role_title = pre_date or company
                company_name = ""

            joined = date_m.group(1).strip()
            left = date_m.group(2).strip()

            # Collect description body
            body_lines = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                # Stop when we see a new entry (non-empty line followed by date line)
                if find_any_date_range(next_line):
                    break
                if next_line:
                    body_lines.append(next_line)
                j += 1

            entries.append(
                asdict(
                    ExperienceEntry(
                        title=role_title,
                        company=company_name,
                        joined=joined,
                        left=left,
                        description="\n".join(body_lines),
                    )
                )
            )
            i = j
        else:
            i += 1

    return entries


# ── 5d. Education sub-parser ──
def parse_education(text: str) -> list[dict]:
    entries: list[dict] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        dr = find_any_date_range(line)
        if dr:
            degree_raw = line[: dr.start()].strip()
            joined = dr.group(1).strip()
            left = dr.group(2).strip()

            institution = ""
            score_val = score_max = score_type = ""
            j = i + 1
            while j < len(lines) and not find_any_date_range(lines[j]):
                candidate = lines[j].strip()
                gpa_m = Patterns.GPA.search(candidate)
                sc_m = Patterns.SCORE.search(candidate)
                if gpa_m:
                    score_val, score_max, score_type = (
                        gpa_m.group(1),
                        gpa_m.group(2),
                        "GPA",
                    )
                elif sc_m:
                    score_val, score_max, score_type = (
                        sc_m.group(1),
                        sc_m.group(2),
                        "SCORE",
                    )
                elif candidate and not institution:
                    institution = candidate
                j += 1

            entry = EducationEntry(
                degree=degree_raw,
                institution=institution,
                started=joined,
                ended=left,
                score=score_val,
                score_max=score_max,
                score_type=score_type,
            )
            entries.append({k: v for k, v in asdict(entry).items() if v})
            i = j
        else:
            i += 1

    return entries


# ── 5e. Projects sub-parser ──
def parse_projects(text: str) -> list[dict]:
    entries: list[dict] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        dr = find_any_date_range(line)
        if dr:
            title_raw = line[: dr.start()].strip().rstrip("|").strip()
            joined = dr.group(1).strip()
            left = dr.group(2).strip()

            # If title is empty, use previous line
            if not title_raw and i > 0:
                title_raw = lines[i - 1].strip()

            desc_lines: list[str] = []
            technologies: list[str] = []
            url = ""
            j = i + 1
            while j < len(lines):
                cline = lines[j].strip()
                if find_any_date_range(cline):
                    break
                tech_m = re.match(
                    r"Technologies?\s+Used\s*:\s*(.+)", cline, re.IGNORECASE
                )
                url_m = re.match(r"Project\s+Link\s*:\s*(\S+)", cline, re.IGNORECASE)
                if tech_m:
                    technologies = [
                        t.strip() for t in re.split(r",|;", tech_m.group(1))
                    ]
                elif url_m:
                    url = url_m.group(1).strip()
                elif cline:
                    desc_lines.append(cline)
                j += 1

            entry = ProjectEntry(
                title=title_raw,
                started=joined,
                ended=left,
                description="\n".join(desc_lines),
                technologies=technologies,
                url=url,
            )
            d = asdict(entry)
            entries.append({k: v for k, v in d.items() if v not in ("", [], None)})
            i = j
        else:
            i += 1

    return entries


# ── 5f. List-based sections ──
def parse_list_section(text: str) -> list[str]:
    items = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            items.append(line)
    return items


def parse_achievements(text: str) -> list[str]:
    items = []
    buf = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if buf and re.match(r"[A-Z]", line) and buf[-1][-1] in ".!,":
            items.append(" ".join(buf))
            buf = [line]
        else:
            buf.append(line)
    if buf:
        items.append(" ".join(buf))
    return items


# ─────────────────────────────────────────────
# ⑥ MAIN PARSER CLASS
# ─────────────────────────────────────────────
class ResumeParser:
    """
    Pipeline
    --------
    0. Pass-through: if input is already a parsed schema, return as-is.
    1. Concatenate all text content from the raw JSON.
    2. Tokenise into sections.
    3. Dispatch each section to the appropriate sub-parser.
    4. FIX: If header is null, extract name/role from preamble text.
    5. Assemble final ResumeOutput.
    """

    def __init__(self, raw: dict[str, Any]):
        self.raw = raw

    def _is_already_parsed(self) -> bool:
        """FIX: Detect if input is already a structured resume schema (Data 2 case)."""
        return (
            "info" in self.raw
            and isinstance(self.raw.get("info"), dict)
            and "name" in self.raw["info"]
            and "experience" in self.raw
        )

    def _gather_text(self) -> tuple[str, str, str]:
        header = self.raw.get("header") or ""
        left = self.raw.get("left") or ""
        right = self.raw.get("right") or ""
        if not (left or right):
            left = self.raw.get("content") or ""
        return header, left, right

    def parse(self) -> dict[str, Any]:
        # FIX: Pass-through for already-parsed schemas
        if self._is_already_parsed():
            logger.info("Input is already a parsed resume schema — returning as-is.")
            output = {
                "info": self.raw.get("info", {}),
                "about": self.raw.get("about", ""),
                "skills": self.raw.get("skills", []),
                "soft_skills": self.raw.get("soft_skills", []),
                "experience": self.raw.get("experience", []),
                "education": self.raw.get("education", []),
                "projects": self.raw.get("projects", []),
                "languages": self.raw.get("languages", []),
                "achievements": self.raw.get("achievements", []),
            }
            return output

        header_text, left_text, right_text = self._gather_text()
        combined_text = "\n".join(filter(None, [left_text, right_text]))

        # ── Step 1: tokenise sections ─────────
        sections = tokenise_sections(combined_text)
        logger.info("Detected sections: %s", list(sections.keys()))

        # ── Step 2: parse name/role ───────────
        name, role = parse_header(header_text)

        # FIX: If no explicit header, extract from preamble (text before first section)
        if not name:
            # The preamble is text collected under key None / before first section title
            # It will be in sections.get(None) or we can re-derive it from combined_text
            preamble = _extract_preamble(combined_text)
            name, role = extract_name_role_from_preamble(preamble)
            logger.info("Extracted name from preamble: %s | role: %s", name, role)

        # ── Step 3: build contact info ────────
        contact_raw = sections.get("contact", "")
        contact = parse_contact(contact_raw + "\n" + combined_text)

        # FIX: if role still empty, try to find it near name in preamble
        if not role:
            preamble = _extract_preamble(combined_text)
            _, role = extract_name_role_from_preamble(preamble)

        info: dict[str, Any] = {
            "name": name,
            "role": role,
            "email": contact.get("email", ""),
            "phone": contact.get("phone", ""),
            "address": contact.get("address", ""),
            "website": contact.get("website", ""),
        }

        # ── Step 4: sub-parse each section ────
        about = sections.get("objective", "").strip()
        skills = parse_list_section(sections.get("skills", ""))
        soft_skills = parse_list_section(sections.get("soft_skills", ""))
        experience = parse_experience(sections.get("experience", ""))
        education = parse_education(sections.get("education", ""))
        projects = parse_projects(sections.get("projects", ""))
        languages = parse_list_section(sections.get("languages", ""))
        achievements = parse_achievements(sections.get("achievements", ""))

        output = ResumeOutput(
            info=info,
            about=about,
            skills=skills,
            soft_skills=soft_skills,
            experience=experience,
            education=education,
            projects=projects,
            languages=languages,
            achievements=achievements,
            raw_sections=sections,
        )

        return asdict(output)


def _extract_preamble(text: str) -> str:
    """Return lines before the first recognised section heading."""
    lines = text.splitlines()
    preamble_lines = []
    for line in lines:
        if SECTION_TITLE_RE.match(line.strip()):
            break
        preamble_lines.append(line)
    return "\n".join(preamble_lines)
