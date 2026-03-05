"""
ATS Resume Engine  v2.2
=======================
Extracts structured text from PDF resumes using pdfplumber.

Changes in v2.2
---------------
Bug fixed: _is_section_heading() was using a generic ALL-CAPS heuristic that
falsely matched names like "DANIEL GALLEGO" (ALL-CAPS, ≤4 words), stopping
the left-column header extraction immediately with zero results.

Root cause: font size was ignored. Names are typically 2-4x body font size.
Section headings are 1.2-1.8x. "DANIEL GALLEGO" = 35.7pt vs body = 10pt.

Fix: _is_section_heading() now checks font size via a per-page char_map.
A line is only a section heading if its avg font size ≤ SECTION_HEADING_MAX_RATIO
× median body size (default 2.0x). Names far exceed this threshold.
"""

import io
from typing import Dict, List, Optional, Tuple

import pdfplumber

# ──────────────────────────────────────────────────────────────
# Tunable constants
# ──────────────────────────────────────────────────────────────

X0_BUCKET = 5
X0_GAP_RATIO = 0.05
CENTER_TOLERANCE = 0.15
MIN_LINE_WIDTH_FRACTION = 0.15
LINE_Y_TOL = 5
MIN_HEADER_LINES = 1
SECTION_HEADING_MAX_RATIO = 2.0

SECTION_KEYWORDS = {
    "about",
    "about me",
    "summary",
    "professional summary",
    "experience",
    "work experience",
    "education",
    "skills",
    "tech skills",
    "soft skills",
    "contact",
    "certifications",
    "languages",
    "profile",
    "objective",
    "projects",
    "achievements",
}


# ──────────────────────────────────────────────────────────────
# Font-size helpers
# ──────────────────────────────────────────────────────────────


def _build_char_size_map(page) -> Dict:
    """Lookup: (round(x0,1), round(top,1)) -> font_size for first char at each position."""
    char_map = {}
    for c in page.chars:
        if c.get("size") and c.get("text", "").strip():
            key = (round(float(c["x0"]), 1), round(float(c["top"]), 1))
            if key not in char_map:
                char_map[key] = float(c["size"])
    return char_map


def _get_median_font_size(page) -> float:
    """Median font size across all chars on the page (represents body text)."""
    sizes = [float(c["size"]) for c in page.chars if c.get("size")]
    if not sizes:
        return 10.0
    sizes.sort()
    return sizes[len(sizes) // 2]


def _line_avg_font_size(line: List[Dict], char_map: Dict) -> float:
    """Average font size of words in a line using char_map lookup."""
    sizes = []
    for w in line:
        key = (round(float(w["x0"]), 1), round(float(w["top"]), 1))
        if key in char_map:
            sizes.append(char_map[key])
    return sum(sizes) / len(sizes) if sizes else 0.0


# ──────────────────────────────────────────────────────────────
# Low-level helpers
# ──────────────────────────────────────────────────────────────


def _extract_words(page) -> List[Dict]:
    words = page.extract_words(
        x_tolerance=3,
        y_tolerance=3,
        keep_blank_chars=False,
        use_text_flow=False,
    )
    return [w for w in words if w["text"].strip()]


def _group_into_lines(words: List[Dict]) -> List[List[Dict]]:
    if not words:
        return []
    sw = sorted(words, key=lambda w: (float(w["top"]), float(w["x0"])))
    lines, cur = [], [sw[0]]
    cy = float(sw[0]["top"])
    for w in sw[1:]:
        y = float(w["top"])
        if abs(y - cy) <= LINE_Y_TOL:
            cur.append(w)
        else:
            lines.append(cur)
            cur = [w]
            cy = y
    lines.append(cur)
    return lines


def _line_text(line: List[Dict]) -> str:
    return " ".join(w["text"] for w in sorted(line, key=lambda w: float(w["x0"])))


def _lines_to_text(lines: List[List[Dict]]) -> str:
    return "\n".join(_line_text(ln) for ln in lines)


def _line_midpoint_x(line: List[Dict]) -> float:
    x0 = min(float(w["x0"]) for w in line)
    x1 = max(float(w["x1"]) for w in line)
    return (x0 + x1) / 2.0


# ──────────────────────────────────────────────────────────────
# Step A – x0-density gap detection
# ──────────────────────────────────────────────────────────────


def _find_column_split_by_x0(words: List[Dict], page_width: float) -> Optional[float]:
    if not words:
        return None
    pw = int(page_width)
    bkt = X0_BUCKET
    n_buckets = pw // bkt + 1
    hist = [0] * n_buckets
    for w in words:
        b = min(int(float(w["x0"])) // bkt, n_buckets - 1)
        hist[b] += 1
    min_zero_buckets = max(1, int((pw * X0_GAP_RATIO) / bkt))
    gaps: List[Tuple[int, int, int]] = []
    in_zero = False
    gs = 0
    for i, v in enumerate(hist):
        if v == 0 and not in_zero:
            in_zero = True
            gs = i
        elif v > 0 and in_zero:
            in_zero = False
            gaps.append((gs, i, i - gs))
    if in_zero:
        gaps.append((gs, n_buckets, n_buckets - gs))

    def has_left(s):
        return any(float(w["x0"]) < s * bkt for w in words)

    def has_right(e):
        return any(float(w["x0"]) >= e * bkt for w in words)

    candidates = [
        (gs, ge, l)
        for gs, ge, l in gaps
        if l >= min_zero_buckets and has_left(gs) and has_right(ge)
    ]
    if not candidates:
        return None
    best = max(candidates, key=lambda g: g[2])
    return ((best[0] + best[1]) / 2.0) * bkt


# ──────────────────────────────────────────────────────────────
# Step B – Centered header extraction
# ──────────────────────────────────────────────────────────────


def _extract_centered_header(
    lines: List[List[Dict]], page_width: float
) -> Tuple[Optional[str], List[List[Dict]]]:
    """Collect top lines whose midpoint is within CENTER_TOLERANCE of page center."""
    page_mid = page_width / 2.0
    tol = (page_width / 2.0) * CENTER_TOLERANCE
    header_texts: List[str] = []
    split_idx = 0
    for i, line in enumerate(lines):
        mid = _line_midpoint_x(line)
        lx0 = min(float(w["x0"]) for w in line)
        lx1 = max(float(w["x1"]) for w in line)
        lw = lx1 - lx0
        if abs(mid - page_mid) <= tol and lw >= page_width * MIN_LINE_WIDTH_FRACTION:
            header_texts.append(_line_text(line))
            split_idx = i + 1
        else:
            break
    if len(header_texts) >= MIN_HEADER_LINES:
        return "\n".join(header_texts), lines[split_idx:]
    return None, lines


# ──────────────────────────────────────────────────────────────
# Step B2 – Left-column header extraction (fallback)
# ──────────────────────────────────────────────────────────────


def _is_section_heading(line: List[Dict], char_map: Dict, median_size: float) -> bool:
    """
    True if this line is a section heading (e.g. SKILLS, CONTACT).
    False if it's a large name/title.

    Decision logic:
    1. Exact keyword match → always True.
    2. Font size > SECTION_HEADING_MAX_RATIO × median → False (it's a name).
    3. Small font + ALL-CAPS/TitleCase short line → True (section heading).
    """
    text_lower = _line_text(line).strip().lower()
    if text_lower in SECTION_KEYWORDS:
        return True

    raw = _line_text(line).strip()
    avg_size = _line_avg_font_size(line, char_map)

    if avg_size == 0:
        return False  # no size info, don't guess

    # Names/titles have large font — exclude them
    if avg_size > median_size * SECTION_HEADING_MAX_RATIO:
        return False

    # Small enough — check heading style
    is_heading_style = (raw.isupper() and len(raw.split()) <= 5) or (
        raw.istitle() and len(raw.split()) <= 4
    )
    return is_heading_style


def _extract_left_column_header(
    lines: List[List[Dict]],
    gap_centre: float,
    char_map: Dict,
    median_size: float,
) -> Tuple[Optional[str], List[List[Dict]]]:
    """
    Fallback for resumes where name/title is in the left column (not centered).
    Walks top lines collecting pure-left-column lines until a section heading,
    mixed line, or right-only line is encountered.
    Returns (header_text | None, all_lines_unchanged).
    """
    header_texts: List[str] = []
    for line in lines:
        left_words = [w for w in line if float(w["x0"]) < gap_centre]
        right_words = [w for w in line if float(w["x0"]) >= gap_centre]
        if not left_words:
            break
        if right_words:
            break
        if _is_section_heading(line, char_map, median_size):
            break
        header_texts.append(_line_text(line))
    if not header_texts:
        return None, lines
    return "\n".join(header_texts), lines  # lines UNCHANGED for column split


# ──────────────────────────────────────────────────────────────
# Step C – Assign body lines to columns
# ──────────────────────────────────────────────────────────────


def _split_lines_by_x0(
    lines: List[List[Dict]], gap_centre: float
) -> Tuple[List[List[Dict]], List[List[Dict]]]:
    left: List[List[Dict]] = []
    right: List[List[Dict]] = []
    for line in lines:
        lw = [w for w in line if float(w["x0"]) < gap_centre]
        rw = [w for w in line if float(w["x0"]) >= gap_centre]
        if lw:
            left.append(sorted(lw, key=lambda w: float(w["x0"])))
        if rw:
            right.append(sorted(rw, key=lambda w: float(w["x0"])))
    return left, right


# ──────────────────────────────────────────────────────────────
# Per-page parser
# ──────────────────────────────────────────────────────────────


def _parse_page(page) -> Dict:
    pw = float(page.width)
    words = _extract_words(page)
    if not words:
        return {
            "meta": {"layout": "single"},
            "header": None,
            "left": "",
            "right": None,
        }

    all_lines = _group_into_lines(words)
    gap_centre = _find_column_split_by_x0(words, pw)

    if gap_centre is None:
        return {
            "meta": {"layout": "single"},
            "header": None,
            "left": _lines_to_text(all_lines),
            "right": None,
        }

    # Font data for section-heading detection
    char_map = _build_char_size_map(page)
    median_size = _get_median_font_size(page)

    # Step B: centered header
    header_text, body_lines = _extract_centered_header(all_lines, pw)

    # Step B2: left-column header fallback
    if header_text is None:
        header_text, body_lines = _extract_left_column_header(
            all_lines, gap_centre, char_map, median_size
        )

    # Step C: split into columns
    left_lines, right_lines = _split_lines_by_x0(body_lines, gap_centre)

    return {
        "meta": {"layout": "two_column"},
        "header": header_text,
        "left": _lines_to_text(left_lines),
        "right": _lines_to_text(right_lines),
        "ok": True,
    }


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────


def parse_resume(pdf_bytes: bytes) -> Dict:
    """
    Parse a resume PDF and return a structured dict.
    Keys: meta, header, left_content, right_content, pages.
    """
    page = None
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page = pdf.pages[0]
        parsed = _parse_page(page)

    if not parsed:
        return {
            "meta": {"layout": "single"},
            "header": None,
            "left": "",
            "right": None,
            "ok": False,
        }

    return parsed


# ──────────────────────────────────────────────────────────────
# helper
# ──────────────────────────────────────────────────────────────


def _pretty_print(result: Dict):
    import json

    display = {k: v for k, v in result.items() if k != "pages"}
    print(json.dumps(display, indent=2, ensure_ascii=False))
    print("\n── Per-page breakdown ──")
    for i, p in enumerate(result.get("pages", []), 1):
        print("\n  Page %d: layout=%s" % (i, p["meta"]["layout"]))
        if p.get("header"):
            print("  HEADER : %r" % p["header"])
        if p.get("left"):
            print("  LEFT   : %r" % p["left"][:200].replace("\n", " | "))
        if p.get("right"):
            print("  RIGHT  : %r" % p["right"][:200].replace("\n", " | "))
