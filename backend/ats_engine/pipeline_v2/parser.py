"""
parser.py  (v6 — Local SLM Extraction)
-----------------------------------------
Architecture:
  PDF text  ──► Qwen2.5-1.5B-Instruct (local, ~3GB RAM, no API cost)
             ──► field-by-field JSON extraction  (reliable at small scale)
             ──► unified schema
             ──► BAAI/bge-large-en-v1.5 embeddings

Why field-by-field instead of one big prompt:
  Tiny models (~1.5B params) reliably generate short focused JSON fragments.
  Asking for the full schema in one shot causes truncation, hallucination,
  and broken JSON.  Splitting into 5 targeted calls costs ~2s extra but
  gives near-perfect field coverage.

Extraction calls:
  1. info + about + languages
  2. skills (tech) + soft_skills
  3. experience[]
  4. education[]
  5. projects[] + achievements[]

Model options (set MODEL_NAME):
  "Qwen/Qwen2.5-0.5B-Instruct"   ~1 GB RAM  fast,  lower accuracy
  "Qwen/Qwen2.5-1.5B-Instruct"   ~3 GB RAM  good,  recommended  ← default
  "Qwen/Qwen2.5-3B-Instruct"     ~6 GB RAM  best,  needs more VRAM
  "HuggingFaceTB/SmolLM2-1.7B-Instruct"  ~3.5 GB  alternative

Install:
  pip install transformers accelerate torch pdfplumber pdfminer.six
              PyMuPDF pytesseract pillow sentence-transformers numpy
"""

from __future__ import annotations

import datetime
import io
import json
import re
import warnings
from pathlib import Path

import numpy as np
import pdfplumber
from pdfminer.high_level import extract_text as pdfminer_extract
from PIL import Image, ImageFilter, ImageOps
from sentence_transformers import SentenceTransformer

try:
    import fitz

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pytesseract

    TESSERACT_AVAILABLE = True
    TESS_CONFIG = "--oem 3 --psm 6"
except ImportError:
    TESSERACT_AVAILABLE = False

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# ─────────────────────────────────────────────────────────────────────────────
# MODEL CONFIG
# ─────────────────────────────────────────────────────────────────────────────

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
MAX_NEW_TOKENS = 768  # enough for any single field extraction
TEMPERATURE = 0.05  # near-deterministic for JSON
TOP_P = 0.9
REPETITION_PENALTY = 1.1


# ─────────────────────────────────────────────────────────────────────────────
# PDF TEXT EXTRACTION  (pdfplumber → pdfminer → Tesseract, unchanged)
# ─────────────────────────────────────────────────────────────────────────────


def _pdfplumber_text(filepath: str) -> str:
    lines = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            try:
                words = page.extract_words()
                if words:
                    rows: dict = {}
                    for w in words:
                        y = round(w["top"] / 8) * 8
                        rows.setdefault(y, []).append(w)
                    for y in sorted(rows):
                        lines.append(
                            " ".join(
                                w["text"]
                                for w in sorted(rows[y], key=lambda x: x["x0"])
                            )
                        )
                else:
                    t = page.extract_text()
                    if t:
                        lines.extend(t.split("\n"))
            except Exception:
                t = page.extract_text()
                if t:
                    lines.extend(t.split("\n"))
    return "\n".join(lines)


def _pdfminer_text(filepath: str) -> str:
    try:
        return pdfminer_extract(filepath) or ""
    except Exception:
        return ""


def _preprocess_ocr(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    if img.width < 1800:
        scale = 1800 / img.width
        img = img.resize(
            (int(img.width * scale), int(img.height * scale)), Image.LANCZOS
        )
    img = ImageOps.autocontrast(img, cutoff=2)
    img = img.filter(ImageFilter.SHARPEN)
    img = img.point(lambda p: 0 if p < 150 else 255, "1")
    return img


def _tesseract_ocr(filepath: str) -> str:
    if not TESSERACT_AVAILABLE:
        return ""
    pages = []
    try:
        if PYMUPDF_AVAILABLE:
            doc = fitz.open(filepath)
            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                pages.append(
                    pytesseract.image_to_string(
                        _preprocess_ocr(img), lang="eng", config=TESS_CONFIG
                    )
                )
            doc.close()
            return "\n".join(pages) if pages else ""
    except Exception:
        pass
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                img = page.to_image(resolution=300).original
                pages.append(
                    pytesseract.image_to_string(
                        _preprocess_ocr(img), lang="eng", config=TESS_CONFIG
                    )
                )
        return "\n".join(pages)
    except Exception:
        return ""


def extract_raw_text(filepath: str) -> str:
    t1 = _pdfplumber_text(filepath)
    if len(t1.strip()) >= 150:
        return t1
    t2 = _pdfminer_text(filepath)
    if len(t2.strip()) >= 150:
        return t2
    best = t1 if len(t1) >= len(t2) else t2
    if len(best.strip()) < 100:
        print("  ⚠️  Low text — running Tesseract OCR...")
        ocr = _tesseract_ocr(filepath)
        if len(ocr.strip()) > len(best.strip()):
            print("  ✅ OCR succeeded.")
            return ocr
    return best


# ─────────────────────────────────────────────────────────────────────────────
# JSON REPAIR UTILITIES
# ─────────────────────────────────────────────────────────────────────────────


def _extract_json_block(text: str) -> str:
    """
    Pull the first valid JSON object or array out of model output.
    Handles markdown fences, leading explanation text, trailing garbage.
    """
    # Strip markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())

    # Find first { or [
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        idx = text.find(start_char)
        if idx == -1:
            continue
        # Walk forward balancing brackets
        depth = 0
        in_str = False
        escape = False
        for i, ch in enumerate(text[idx:], start=idx):
            if escape:
                escape = False
                continue
            if ch == "\\" and in_str:
                escape = True
                continue
            if ch == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if ch == start_char:
                depth += 1
            elif ch == end_char:
                depth -= 1
                if depth == 0:
                    return text[idx : i + 1]
    return text


def _safe_parse_json(text: str, fallback):
    """Try to parse JSON; return fallback on failure."""
    try:
        block = _extract_json_block(text)
        return json.loads(block)
    except (json.JSONDecodeError, ValueError):
        # Last resort: try to fix common issues
        try:
            fixed = re.sub(r",\s*([}\]])", r"\1", block)  # trailing commas
            fixed = re.sub(r"'", '"', fixed)  # single → double quotes
            return json.loads(fixed)
        except Exception:
            return fallback


def _ensure_list(val, item_type=str) -> list:
    """
    Guarantee a clean list of strings.
    Handles dicts (SLM returns {"language":"English","proficiency":"Fluent"}),
    comma-separated strings, and nested JSON fragments.
    """
    if not val:
        return []
    if not isinstance(val, list):
        val = [val]
    result = []
    for item in val:
        if not item:
            continue
        if isinstance(item, dict):
            lang = item.get("language") or item.get("name") or item.get("lang", "")
            prof = (
                item.get("proficiency") or item.get("level") or item.get("fluency", "")
            )
            if not lang:
                values = [str(v).strip() for v in item.values() if v]
                merged = " ".join(values).strip()
                if merged:
                    result.append(merged)
            elif prof:
                result.append(f"{lang.strip()} ({prof.strip()})")
            else:
                result.append(lang.strip())
            continue
        s = str(item).strip()
        if not s or s.startswith(("{", "[")):
            continue
        result.append(s)
    seen = set()
    deduped = []
    for s in result:
        k = s.lower()
        if k not in seen:
            seen.add(k)
            deduped.append(s)
    return deduped


def _ensure_str(val) -> str:
    if isinstance(val, str):
        return val.strip()
    return str(val).strip() if val else ""


# ─────────────────────────────────────────────────────────────────────────────
# SLM EXTRACTOR  — field-by-field prompting
# ─────────────────────────────────────────────────────────────────────────────


class SLMExtractor:
    """
    Wraps Qwen2.5-Instruct (or any chat-format Hugging Face model) for
    structured resume field extraction.

    Field-by-field strategy:
      Instead of one massive prompt → unreliable long JSON output,
      we send 5 focused prompts → each returns a small, reliable JSON fragment.
      The fragments are then merged into the unified schema.
    """

    def __init__(self, model_name: str = MODEL_NAME):
        print(f"⏳ Loading extraction model: {model_name}")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32
        print(f"   Device: {device}  |  dtype: {dtype}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True,
        )
        if device == "cpu":
            self.model = self.model.to(device)

        self.model.eval()
        self.device = device
        self.model_name = model_name
        print(f"✅ Extraction model ready  ({model_name})")

    def _chat(self, system: str, user: str) -> str:
        """
        Run a single chat turn.
        Uses apply_chat_template if available, falls back to manual format.
        """
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        if hasattr(self.tokenizer, "apply_chat_template"):
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            # Manual fallback for models without chat template
            prompt = f"<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>\n"

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        input_len = inputs["input_ids"].shape[1]

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                repetition_penalty=REPETITION_PENALTY,
                do_sample=TEMPERATURE > 0,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Decode only the newly generated tokens
        generated = outputs[0][input_len:]
        return self.tokenizer.decode(generated, skip_special_tokens=True).strip()

    # ── EXTRACTION CALLS  (one per field group) ───────────────────────────────

    SYSTEM = (
        "You are a precise resume parser. "
        "Output ONLY valid JSON — no explanation, no markdown fences, no extra text."
    )

    def _extract_info_about(self, text: str) -> dict:
        prompt = f"""From this resume text extract the following and return as JSON:
{{
  "name": "candidate full name",
  "role": "job title shown in resume header (e.g. Full Stack Developer)",
  "email": "email address or empty string",
  "phone": "phone number or empty string",
  "address": "city and state/country or empty string",
  "website": "LinkedIn, GitHub, or personal site URL or empty string",
  "about": "copy the summary/objective paragraph verbatim, or empty string if not present"
}}

Resume:
{text[:2500]}

JSON:"""
        raw = self._chat(self.SYSTEM, prompt)
        result = _safe_parse_json(raw, {})
        return {
            "name": _ensure_str(result.get("name", "Unknown Candidate")),
            "role": _ensure_str(result.get("role", "")),
            "email": _ensure_str(result.get("email", "")),
            "phone": _ensure_str(result.get("phone", "")),
            "address": _ensure_str(result.get("address", "")),
            "website": _ensure_str(result.get("website", "")),
            "about": _ensure_str(result.get("about", "")),
        }

    def _extract_skills(self, text: str) -> dict:
        prompt = f"""From this resume text extract skills and return as JSON:
{{
  "skills": ["list of TECHNICAL skills only: programming languages, frameworks, tools, databases, cloud platforms"],
  "soft_skills": ["list of SOFT skills only: teamwork, leadership, communication, time management etc"],
  "languages": ["PLAIN STRINGS ONLY e.g. English (Fluent) or Tamil (Native) — NO objects, NO dicts"]
}}

Rules:
- skills = only tech (Python, React, Docker, MySQL etc)
- soft_skills = only interpersonal (Teamwork, Leadership etc)
- Do NOT mix tech and soft skills
- languages must be plain strings like "English (Fluent)" NOT objects like {{"language":"English"}}

Resume:
{text[:2500]}

JSON:"""
        raw = self._chat(self.SYSTEM, prompt)
        result = _safe_parse_json(raw, {})
        return {
            "skills": _ensure_list(result.get("skills", [])),
            "soft_skills": _ensure_list(result.get("soft_skills", [])),
            "languages": _ensure_list(result.get("languages", [])),
        }

    def _extract_experience(self, text: str) -> list:
        prompt = f"""From this resume text extract ALL work experience entries.
Return a JSON array. Each entry:
{{
  "title": "job title",
  "company": "company name",
  "joined": "start date e.g. JAN 2023 or 2023",
  "left": "end date or PRESENT",
  "description": "job description verbatim"
}}

If no work experience exists return [].

Resume:
{text[:2500]}

JSON array:"""
        raw = self._chat(self.SYSTEM, prompt)
        result = _safe_parse_json(raw, [])
        if not isinstance(result, list):
            return []
        cleaned = []
        for e in result:
            if not isinstance(e, dict):
                continue
            cleaned.append(
                {
                    "title": _ensure_str(e.get("title", "")),
                    "company": _ensure_str(e.get("company", "")),
                    "joined": _ensure_str(e.get("joined", "")),
                    "left": _ensure_str(e.get("left", "")),
                    "description": _ensure_str(e.get("description", "")),
                }
            )
        return cleaned

    def _extract_education(self, text: str) -> list:
        prompt = f"""From this resume text extract ALL education entries.
Return a JSON array. Each entry:
{{
  "degree": "degree name e.g. Bachelor of Computer Science",
  "institution": "school or university name",
  "started": "start year e.g. 2020",
  "ended": "end year e.g. 2024 or PRESENT",
  "score": "GPA or percentage as string e.g. 8.4 or 81 or null",
  "score_max": "max score e.g. 10.0 or 100 or null",
  "score_type": "GPA or PERCENTAGE or SCORE or null"
}}

If no education exists return [].

Resume:
{text[:2500]}

JSON array:"""
        raw = self._chat(self.SYSTEM, prompt)
        result = _safe_parse_json(raw, [])
        if not isinstance(result, list):
            return []
        cleaned = []
        for e in result:
            if not isinstance(e, dict):
                continue
            cleaned.append(
                {
                    "degree": _ensure_str(e.get("degree", "")),
                    "institution": _ensure_str(e.get("institution", "")),
                    "started": _ensure_str(e.get("started", "")),
                    "ended": _ensure_str(e.get("ended", "")),
                    "score": _ensure_str(e.get("score", "")) or None,
                    "score_max": _ensure_str(e.get("score_max", "")) or None,
                    "score_type": _ensure_str(e.get("score_type", "")) or None,
                }
            )
        return cleaned

    def _extract_projects_achievements(self, text: str) -> dict:
        prompt = f"""From this resume text extract projects and achievements.
Return JSON:
{{
  "projects": [
    {{
      "title": "project name",
      "started": "start date or year or empty string",
      "ended": "end date or PRESENT or empty string",
      "description": "full project description verbatim",
      "technologies": ["list", "of", "technologies", "used"],
      "url": "GitHub or live URL or empty string"
    }}
  ],
  "achievements": [
    "each achievement or award or certification as a separate string"
  ]
}}

If no projects return "projects": [].
If no achievements return "achievements": [].

Resume:
{text[:2500]}

JSON:"""
        raw = self._chat(self.SYSTEM, prompt)
        result = _safe_parse_json(raw, {})
        if not isinstance(result, dict):
            result = {}

        projects = result.get("projects", [])
        if not isinstance(projects, list):
            projects = []
        clean_projects = []
        for p in projects:
            if not isinstance(p, dict):
                continue
            clean_projects.append(
                {
                    "title": _ensure_str(p.get("title", "")),
                    "started": _ensure_str(p.get("started", "")),
                    "ended": _ensure_str(p.get("ended", "")),
                    "description": _ensure_str(p.get("description", "")),
                    "technologies": _ensure_list(p.get("technologies", [])),
                    "url": _ensure_str(p.get("url", "")),
                }
            )

        return {
            "projects": clean_projects,
            "achievements": _ensure_list(result.get("achievements", [])),
        }

    def extract(self, raw_text: str) -> dict:
        """
        Run all 4 extraction calls and merge into the unified schema.
        Each call is independent — a failure in one doesn't break others.
        """
        # Truncate to model context window safely
        text = raw_text[:3000]

        print("   🔍 Extracting: info + about...", end=" ", flush=True)
        info_data = self._extract_info_about(text)
        print("✓")

        print("   🔍 Extracting: skills...", end=" ", flush=True)
        skills_data = self._extract_skills(text)
        print("✓")

        print("   🔍 Extracting: experience...", end=" ", flush=True)
        experience = self._extract_experience(text)
        print(f"✓  ({len(experience)} entries)")

        print("   🔍 Extracting: education...", end=" ", flush=True)
        education = self._extract_education(text)
        print(f"✓  ({len(education)} entries)")

        print("   🔍 Extracting: projects + achievements...", end=" ", flush=True)
        proj_ach = self._extract_projects_achievements(text)
        print(
            f"✓  ({len(proj_ach['projects'])} projects, "
            f"{len(proj_ach['achievements'])} achievements)"
        )

        return {
            "info": {
                "name": info_data["name"],
                "role": info_data["role"],
                "email": info_data["email"],
                "phone": info_data["phone"],
                "address": info_data["address"],
                "website": info_data["website"],
            },
            "about": info_data["about"],
            "skills": skills_data["skills"],
            "soft_skills": skills_data["soft_skills"],
            "languages": skills_data["languages"],
            "experience": experience,
            "education": education,
            "projects": proj_ach["projects"],
            "achievements": proj_ach["achievements"],
        }


# ─────────────────────────────────────────────────────────────────────────────
# META COMPUTATION
# ─────────────────────────────────────────────────────────────────────────────

_PRESENT_WORDS = {"present", "current", "now", "ongoing", "till date"}


def _parse_year(s: str) -> int | None:
    m = re.search(r"\b(19|20)(\d{2})\b", str(s))
    return int(m.group()) if m else None


def _get_years_of_experience(experience: list) -> float:
    total_months = 0
    now = datetime.datetime.now()
    for exp in experience:
        start_yr = _parse_year(exp.get("joined", ""))
        left = str(exp.get("left", "")).strip().lower()
        end_yr = now.year if left in _PRESENT_WORDS else _parse_year(left)
        if start_yr and end_yr and end_yr >= start_yr:
            total_months += (end_yr - start_yr) * 12
    return round(total_months / 12, 1) if total_months else 0.0


def _detect_fresher(parsed: dict) -> bool:
    """
    Fresher = no real work experience.
    Logic:
      - no experience entries at all           → fresher
      - has entries but all are student/intern → fresher
      - has ANY real job title                 → NOT fresher
    """
    exp = parsed.get("experience", [])
    if not exp:
        return True

    REAL_JOB_WORDS = (
        "engineer",
        "developer",
        "analyst",
        "scientist",
        "manager",
        "lead",
        "architect",
        "consultant",
        "designer",
        "researcher",
        "specialist",
        "associate",
        "officer",
        "executive",
        "coordinator",
        "programmer",
    )
    STUDENT_WORDS = ("student", "intern", "trainee", "fresher", "volunteer")

    real_count = 0
    for e in exp:
        title = e.get("title", "").lower()
        company = e.get("company", "").lower()
        # Skip blank entries the SLM hallucinated
        if not title and not company:
            continue
        if any(w in title for w in REAL_JOB_WORDS):
            real_count += 1
        elif not any(w in title for w in STUDENT_WORDS):
            # Unknown title but has a company — count as real
            if company:
                real_count += 1

    return real_count == 0


def _build_raw_sections(parsed: dict, raw_text: str) -> dict:
    """Reconstruct raw_sections for downstream matcher/clusterer compatibility."""
    return {
        "about": parsed.get("about", ""),
        "skills": " ".join(parsed.get("skills", []) + parsed.get("soft_skills", [])),
        "experience": " ".join(
            f"{e.get('title', '')} {e.get('company', '')} {e.get('description', '')}"
            for e in parsed.get("experience", [])
        ),
        "projects": " ".join(
            f"{p.get('title', '')} {p.get('description', '')} {' '.join(p.get('technologies', []))}"
            for p in parsed.get("projects", [])
        ),
        "education": " ".join(
            f"{e.get('degree', '')} {e.get('institution', '')}"
            for e in parsed.get("education", [])
        ),
        "achievements": " ".join(parsed.get("achievements", [])),
        "other": raw_text[:1000],
    }


# ─────────────────────────────────────────────────────────────────────────────
# EMBEDDINGS  (unchanged from previous versions)
# ─────────────────────────────────────────────────────────────────────────────


def build_embeddings(parsed: dict, model: SentenceTransformer) -> dict:
    emb: dict = {}
    raw = parsed.get("_meta", {}).get("raw_sections", {})

    if parsed.get("about"):
        emb["summary"] = model.encode(parsed["about"], normalize_embeddings=True)

    if parsed.get("skills"):
        emb["skills"] = model.encode(
            "Technical skills: " + ", ".join(parsed["skills"]),
            normalize_embeddings=True,
        )

    exp_text = raw.get("experience", "")
    if exp_text and not parsed.get("_meta", {}).get("is_fresher"):
        emb["experience"] = model.encode(exp_text[:2000], normalize_embeddings=True)

    proj_text = raw.get("projects", "")
    if proj_text:
        emb["projects"] = model.encode(proj_text[:2000], normalize_embeddings=True)
    elif "experience" in emb:
        emb["projects"] = emb["experience"]

    edu_list = parsed.get("education", [])
    if edu_list:
        edu_str = " | ".join(
            f"{e.get('degree', '')} {e.get('institution', '')}".strip()
            for e in edu_list
        )
        if edu_str.strip():
            emb["education"] = model.encode(edu_str, normalize_embeddings=True)

    full = " ".join(v for v in raw.values() if isinstance(v, str))[:3000]
    emb["full"] = model.encode(full, normalize_embeddings=True)

    return emb


# ─────────────────────────────────────────────────────────────────────────────
# HIGH-LEVEL CLASS
# ─────────────────────────────────────────────────────────────────────────────


class ResumeParser:
    """
    PDF → unified schema + embeddings using a local SLM + SentenceTransformer.

    No API key needed. Runs fully offline after first download.

    First run downloads:
      Qwen2.5-1.5B-Instruct   ~3 GB  (cached in ~/.cache/huggingface)
      BAAI/bge-large-en-v1.5  ~1.3 GB

    Example:
        parser = ResumeParser()
        result = parser.process("resume.pdf")
        print(result["parsed"]["info"])
        print(result["parsed"]["projects"])

    To use a different SLM:
        parser = ResumeParser(slm_name="Qwen/Qwen2.5-0.5B-Instruct")   # faster, lighter
        parser = ResumeParser(slm_name="Qwen/Qwen2.5-3B-Instruct")     # more accurate
    """

    def __init__(
        self, embed_model: str = "BAAI/bge-large-en-v1.5", slm_name: str = MODEL_NAME
    ):

        self.extractor = SLMExtractor(slm_name)

        print(f"⏳ Loading embedding model: {embed_model}")
        self.model = SentenceTransformer(embed_model)
        print("✅ Embedding model ready.")
        print(
            f"   Tesseract OCR  : {'active' if TESSERACT_AVAILABLE else 'unavailable'}"
        )
        print(f"   PyMuPDF        : {'active' if PYMUPDF_AVAILABLE else 'unavailable'}")

    def process(self, filepath: str) -> dict:
        """Parse one PDF → { parsed, embeddings }."""
        filename = Path(filepath).name
        print(f"\n📄 Processing: {filename}")

        # 1. Extract raw text from PDF
        raw_text = extract_raw_text(filepath)
        print(f"   📝 {len(raw_text)} chars extracted")

        # 2. SLM field-by-field extraction
        parsed = self.extractor.extract(raw_text)

        # 3. Inject meta
        parsed["_meta"] = {
            "is_fresher": _detect_fresher(parsed),
            "years_of_experience": _get_years_of_experience(
                parsed.get("experience", [])
            ),
            "source_file": filename,
            "raw_sections": _build_raw_sections(parsed, raw_text),
            "raw_text": raw_text[:3000],
        }

        # 4. Build embeddings
        embeddings = build_embeddings(parsed, self.model)

        # Summary
        info = parsed.get("info", {})
        meta = parsed["_meta"]
        print(f"   ✅ Name     : {info.get('name', '?')}")
        print(f"   ✅ Role     : {info.get('role', '—')}")
        print(f"   ✅ Skills   : {parsed.get('skills', [])[:5]}")
        print(
            f"   ✅ Projects : {len(parsed.get('projects', []))}  |  "
            f"Edu: {len(parsed.get('education', []))}  |  "
            f"Exp: {len(parsed.get('experience', []))}"
        )
        print(
            f"   ✅ Fresher  : {meta['is_fresher']}  YoE: {meta['years_of_experience']}"
        )

        return {"parsed": parsed, "embeddings": embeddings}

    def process_many(self, filepaths: list) -> dict:
        db: dict = {}
        for fp in filepaths:
            key = Path(fp).name
            db[key] = self.process(fp)
        return db
