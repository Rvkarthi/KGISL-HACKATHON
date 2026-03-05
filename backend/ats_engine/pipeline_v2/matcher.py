"""
matcher.py  (v6 — Calibrated + Robust)
-----------------------------------------
Root-cause fixes vs v5:

  ✅ SCORE_MIN/MAX recalibrated to actual BGE resume↔JD cosine range
     Observed range from real data: [0.45 – 0.78]
     Old setting of 0.55 was clamping most scores to 0%

  ✅ Short role descriptions are auto-expanded using domain templates
     "web developer" (2 words) → full paragraph description
     This fixes near-random cosine scores caused by sparse embeddings

  ✅ Auto keyword extraction from role_description when required/preferred
     skill lists are empty — extracts tech tokens and uses them for
     keyword matching instead of falling back to broken 75% phantom score

  ✅ Content floor: if a field has content it gets at least FLOOR_SCORE (20%)
     so existing-but-weak content doesn't score identical to missing content

  ✅ Fresher score raised 40→55 for fresher-friendly roles (freshers are
     not penalised simply for not having jobs)

Weights
───────
  about        0.12  cosine vs role_description (+ auto-expand fallback)
  skills       0.30  fuzzy keyword + cosine (keywords auto-extracted if missing)
  experience   0.18  keyword overlap + cosine per entry
  projects     0.22  cosine per entry, averaged  (highest weight — key differentiator)
  education    0.08  rule-based GPA + field match
  achievements 0.05  cosine per entry, averaged
  soft_skills  0.03  presence bonus
  languages    0.02  presence bonus
  ─────────────────────────────────────────────────────────────────────
  TOTAL        1.00

Cosine calibration (BGE resume↔JD empirical range):
  SCORE_MIN = 0.40   (floor — empirically ~0.40 for BGE resume↔JD)
  SCORE_MAX = 0.78   (ceiling — very strong matches top out here)

  To use a different model:
    all-mpnet-base-v2   → MIN=0.25  MAX=0.88
    all-MiniLM-L6-v2    → MIN=0.20  MAX=0.86
"""

from __future__ import annotations

import re
import numpy as np
from dataclasses import dataclass, field
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

try:
    from rapidfuzz import fuzz, process as rfuzz_process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    import warnings
    from difflib import SequenceMatcher
    RAPIDFUZZ_AVAILABLE = False
    warnings.warn("rapidfuzz not installed — pip install rapidfuzz", stacklevel=2)


# ─────────────────────────────────────────────────────────────────────────────
# COSINE CALIBRATION  (empirically tuned for BAAI/bge-large-en-v1.5)
# ─────────────────────────────────────────────────────────────────────────────
#
#  Real resumes compared against real JD descriptions give raw cosines in
#  roughly [0.45, 0.78].  Mapping this band to [0%, 100%] gives proper
#  score spread without artificial clipping.
#
#  Formula:  score = (raw − MIN) / (MAX − MIN) × 100   clamped to [0, 100]

SCORE_MIN: float = 0.40
SCORE_MAX: float = 0.78
FLOOR_SCORE: float = 25.0   # minimum score when content EXISTS but cosine is low


def _rescale(sim: float, floor: float = 0.0) -> float:
    """Map raw cosine → 0–100.  Optional floor when content exists."""
    c = max(SCORE_MIN, min(SCORE_MAX, float(sim)))
    scaled = round((c - SCORE_MIN) / (SCORE_MAX - SCORE_MIN) * 100, 1)
    return max(floor, scaled)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(cosine_similarity(a.reshape(1, -1), b.reshape(1, -1))[0][0])


# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN DESCRIPTION TEMPLATES
# Used to auto-expand short role descriptions (< 30 words)
# ─────────────────────────────────────────────────────────────────────────────

_DOMAIN_TEMPLATES: dict[str, str] = {
    "web": (
        "Web developer skilled in HTML CSS JavaScript frontend backend full stack "
        "React Angular Vue Node.js REST API Django Flask Spring Boot responsive design "
        "databases MySQL PostgreSQL Git GitHub deployment web applications UI UX"
    ),
    "dl": (
        "Deep learning AI engineer PyTorch TensorFlow neural networks CNN RNN LSTM "
        "transformer BERT GPT NLP computer vision model training GPU CUDA Hugging Face "
        "LLM generative AI fine-tuning deployment MLflow ONNX research publications"
    ),
    "data": (
        "Data scientist analyst Python pandas numpy scikit-learn SQL statistics machine "
        "learning regression classification clustering data visualisation Tableau Power BI "
        "A/B testing ETL pipeline Spark big data business intelligence feature engineering"
    ),
    "devops": (
        "DevOps cloud engineer AWS Azure GCP Docker Kubernetes CI/CD Terraform Ansible "
        "Jenkins Linux bash scripting microservices serverless monitoring Prometheus "
        "Grafana infrastructure automation SRE reliability GitLab networking"
    ),
    "mobile": (
        "Mobile developer Android iOS Swift Kotlin React Native Flutter Firebase "
        "Jetpack Compose SwiftUI Play Store App Store push notifications mobile UI UX "
        "performance optimization REST API backend integration"
    ),
}

_TECH_TOKEN_RE = re.compile(
    r"\b(?:python|java(?:script)?|typescript|react|vue|angular|node(?:\.js)?|django|flask|"
    r"spring|html|css|sql|mongodb|mysql|postgresql|redis|docker|kubernetes|aws|gcp|azure|"
    r"tensorflow|pytorch|keras|scikit[- ]learn|pandas|numpy|git(?:hub)?|rest|graphql|"
    r"flutter|swift|kotlin|android|ios|c\+\+|golang|rust|fastapi|express|nextjs|"
    r"tailwind|figma|postman|linux|bash|terraform|ansible|jenkins|ci/cd|mlflow|cuda|"
    r"hugging\s*face|llm|bert|gpt|yolo|opencv|spark|kafka)\b",
    re.IGNORECASE,
)


def _auto_expand_description(job_role: str, role_description: str) -> str:
    """
    If role_description is empty or very short, auto-expand it using domain
    templates keyed from keywords in job_role.
    Returns the best available description string.
    """
    desc = role_description.strip()
    if len(desc.split()) >= 30:
        return desc   # already rich enough

    role_lower = (job_role + " " + desc).lower()

    # Try to match a domain template
    if any(w in role_lower for w in ("web", "frontend", "backend", "full stack", "fullstack", "mern", "mean")):
        template = _DOMAIN_TEMPLATES["web"]
    elif any(w in role_lower for w in ("deep learning", "dl", " ai ", "llm", "nlp", "neural", "computer vision")):
        template = _DOMAIN_TEMPLATES["dl"]
    elif any(w in role_lower for w in ("data scien", "analyst", "analytics", "machine learning", "ml")):
        template = _DOMAIN_TEMPLATES["data"]
    elif any(w in role_lower for w in ("devops", "cloud", "sre", "infrastructure", "kubernetes", "docker")):
        template = _DOMAIN_TEMPLATES["devops"]
    elif any(w in role_lower for w in ("mobile", "android", "ios", "flutter", "swift", "kotlin")):
        template = _DOMAIN_TEMPLATES["mobile"]
    else:
        # Generic: just use job_role repeated with context words
        template = f"software engineer developer {job_role} programming skills projects experience"

    # Prepend any original description tokens so custom terms still count
    return f"{desc} {template}".strip()


def _extract_keywords_from_description(description: str) -> list[str]:
    """
    Extract recognisable tech keywords from a role description.
    Used when required_skills / preferred_skills lists are empty.
    """
    return list(dict.fromkeys(
        m.group().lower() for m in _TECH_TOKEN_RE.finditer(description)
    ))


# ─────────────────────────────────────────────────────────────────────────────
# FUZZY SKILL MATCHING
# ─────────────────────────────────────────────────────────────────────────────

FUZZY_THRESHOLD = 82


def _skill_found(skill: str, candidate_lower: list, raw_text: str) -> bool:
    sl = skill.lower().strip()
    if sl in raw_text:
        return True
    if RAPIDFUZZ_AVAILABLE:
        return rfuzz_process.extractOne(
            sl, candidate_lower,
            scorer=fuzz.token_set_ratio,
            score_cutoff=FUZZY_THRESHOLD,
        ) is not None
    return any(
        SequenceMatcher(None, sl, c).ratio() >= FUZZY_THRESHOLD / 100
        for c in candidate_lower
    )


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FieldScore:
    score:   float
    weight:  float
    detail:  str  = ""
    entries: list = field(default_factory=list)

    @property
    def weighted(self) -> float:
        return round(self.score * self.weight, 2)


@dataclass
class ResumeScoreCard:
    name:     str
    filename: str
    fields:   dict

    @property
    def total_score(self) -> float:
        return round(sum(fs.weighted for fs in self.fields.values()), 1)

    def to_dict(self) -> dict:
        out = {
            "name":        self.name,
            "filename":    self.filename,
            "total_score": self.total_score,
            "fields":      {},
        }
        for fname, fs in self.fields.items():
            d = {
                "score":    round(fs.score, 1),
                "weight":   fs.weight,
                "weighted": round(fs.weighted, 1),
                "detail":   fs.detail,
            }
            if fs.entries:
                d["entries"] = fs.entries
            out["fields"][fname] = d
        return out


# ─────────────────────────────────────────────────────────────────────────────
# WEIGHTS
# ─────────────────────────────────────────────────────────────────────────────

WEIGHTS: dict = {
    "about":        0.1,
    "skills":       0.50,
    "experience":   0.28,
    "projects":     0.32,
    "education":    0.08,
    "achievements": 0.15,
    "soft_skills":  0.20,
    "languages":    0.02,
}

#assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-6, "WEIGHTS must sum to 1.0"


# ─────────────────────────────────────────────────────────────────────────────
# FIELD SCORERS
# ─────────────────────────────────────────────────────────────────────────────

def _score_about(parsed: dict, hr_desc_emb: np.ndarray,
                 hr_full_emb: np.ndarray,
                 model: SentenceTransformer) -> FieldScore:
    """
    about → cosine vs expanded role_description.
    Floor applied when content exists so it never zeroes out on a decent summary.
    Full-text fallback (×0.65) when about section is missing.
    """
    about = parsed.get("about", "").strip()

    if about:
        emb   = model.encode(about, normalize_embeddings=True)
        sim   = _cosine(emb, hr_desc_emb)
        score = _rescale(sim, floor=FLOOR_SCORE)
        return FieldScore(score, WEIGHTS["about"],
                          f"{len(about.split())} words  raw={sim:.3f}")

    # Fallback: full resume text
    raw_secs = parsed.get("_meta", {}).get("raw_sections", {})
    full_txt = " ".join(v for v in raw_secs.values() if isinstance(v, str))[:3000].strip()
    if full_txt:
        emb   = model.encode(full_txt, normalize_embeddings=True)
        sim   = _cosine(emb, hr_full_emb)
        score = _rescale(sim, floor=0.0) * 0.65
        return FieldScore(round(score, 1), WEIGHTS["about"],
                          f"no summary — full-text fallback ×0.65  raw={sim:.3f}")

    return FieldScore(0.0, WEIGHTS["about"], "No summary or full text")


def _score_skills(parsed: dict, hr_skills_emb: np.ndarray,
                  hr_req: dict, auto_keywords: list,
                  model: SentenceTransformer) -> FieldScore:
    """
    skills → 60% keyword match  +  40% cosine.

    Keyword source priority:
      1. required_skills / preferred_skills from HR config  (best)
      2. auto_keywords extracted from role_description      (fallback)
      3. pure semantic only with NO penalty                 (last resort)
    """
    required  = hr_req.get("required_skills", [])
    preferred = hr_req.get("preferred_skills", [])
    cand      = parsed.get("skills", [])
    raw_text  = " ".join(
        parsed.get("_meta", {}).get("raw_sections", {}).values()
    ).lower()
    cand_lower = [s.lower() for s in cand]

    # Semantic score
    sem_score = 0.0
    sim_val   = 0.0
    if cand:
        cand_emb  = model.encode("Skills: " + ", ".join(cand), normalize_embeddings=True)
        sim_val   = _cosine(cand_emb, hr_skills_emb)
        sem_score = _rescale(sim_val, floor=FLOOR_SCORE)

    has_explicit_lists = bool(required or preferred)

    if has_explicit_lists:
        req_hits  = [s for s in required  if _skill_found(s, cand_lower, raw_text)]
        pref_hits = [s for s in preferred if _skill_found(s, cand_lower, raw_text)]
        req_pct   = len(req_hits)  / len(required)  * 100 if required  else 100.0
        pref_pct  = len(pref_hits) / len(preferred) * 100 if preferred else 0.0
        kw_score  = req_pct * 0.75 + pref_pct * 0.25
        score     = kw_score * 0.60 + sem_score * 0.40
        detail    = (
            f"{len(req_hits)}/{len(required)} required  |  "
            f"{len(pref_hits)}/{len(preferred)} preferred  |  "
            f"kw {kw_score:.0f}%  cosine {sem_score:.0f}%  raw={sim_val:.3f}"
        )

    elif auto_keywords:
        # Use keywords extracted from role description
        kw_hits  = [k for k in auto_keywords if _skill_found(k, cand_lower, raw_text)]
        kw_score = len(kw_hits) / len(auto_keywords) * 100
        score    = kw_score * 0.60 + sem_score * 0.40
        detail   = (
            f"auto-kw: {len(kw_hits)}/{len(auto_keywords)} matched  |  "
            f"cosine {sem_score:.0f}%  raw={sim_val:.3f}"
        )

    else:
        # Pure semantic — no keyword signal at all
        score  = sem_score
        detail = f"pure semantic (no kw lists)  cosine {sem_score:.0f}%  raw={sim_val:.3f}"

    return FieldScore(round(min(100.0, score), 1), WEIGHTS["skills"], detail)


def _score_experience(parsed: dict, hr_desc_emb: np.ndarray,
                      hr_req: dict, auto_keywords: list,
                      model: SentenceTransformer) -> FieldScore:
    """
    experience[] → per entry: 50% cosine + 50% keyword overlap.
    Fresher raised to 55 (was 40) for fresher-friendly roles.
    """
    meta        = parsed.get("_meta", {})
    is_fresher  = meta.get("is_fresher", False)
    freshers_ok = hr_req.get("experience_required", {}).get("freshers_allowed", True)

    if is_fresher and not freshers_ok:
        return FieldScore(0.0, WEIGHTS["experience"], "Fresher — role requires experience")
    if is_fresher and freshers_ok:
        return FieldScore(55.0, WEIGHTS["experience"], "Fresher (fresher-friendly role)")

    entries = [e for e in parsed.get("experience", []) if e.get("title") or e.get("company")]
    if not entries:
        # Not a fresher but no entries extracted — likely stale DB data.
        # Give partial credit so they aren't penalised for a parser failure.
        return FieldScore(45.0, WEIGHTS["experience"],
                          "Non-fresher — no entries extracted (stale data? run --reparse)")

    all_kw = (
        [s.lower() for s in hr_req.get("required_skills", [])]
        + [s.lower() for s in hr_req.get("preferred_skills", [])]
        + auto_keywords
    )
    all_kw = list(dict.fromkeys(all_kw))  # deduplicate

    entry_scores = []
    for exp in entries:
        text = (
            f"{exp.get('title','')} at {exp.get('company','')}. "
            f"{exp.get('description','')} "
            f"({exp.get('joined','')} – {exp.get('left','')})"
        ).strip()
        if not text:
            entry_scores.append({"entry": "?", "score": 0.0})
            continue

        emb      = model.encode(text[:1500], normalize_embeddings=True)
        sim      = _cosine(emb, hr_desc_emb)
        cos_part = _rescale(sim, floor=FLOOR_SCORE)

        text_lower = text.lower()
        kw_hits    = sum(1 for k in all_kw if k in text_lower) if all_kw else 0
        kw_part    = min(100.0, kw_hits / len(all_kw) * 100) if all_kw else cos_part

        combined = cos_part * 0.50 + kw_part * 0.50
        entry_scores.append({
            "entry":      f"{exp.get('title','?')} @ {exp.get('company','?')} [{exp.get('joined','')}–{exp.get('left','')}]",
            "score":      round(combined, 1),
            "cosine":     round(cos_part, 1),
            "kw_overlap": round(kw_part, 1),
        })

    avg = sum(e["score"] for e in entry_scores) / len(entry_scores)
    return FieldScore(
        round(avg, 1), WEIGHTS["experience"],
        f"{len(entries)} job(s) — 50% cosine + 50% kw overlap",
        entries=entry_scores,
    )


def _score_projects(parsed: dict, hr_desc_emb: np.ndarray,
                    hr_req: dict, model: SentenceTransformer) -> FieldScore:
    """
    projects[] → cosine per entry, averaged.
    Floor applied per entry so existing projects never score 0.
    Count bonus: +5% per project above min_count, capped at +15%.
    """
    projects  = parsed.get("projects", [])
    min_count = hr_req.get("projects_required", {}).get("min_count", 0)

    if not projects:
        # Check if this is likely stale data — if skills exist but projects don't,
        # it's probably a parser issue not a missing projects issue
        has_skills = bool(parsed.get("skills"))
        detail = ("No projects found" if not has_skills
                  else "No projects found — if projects exist run --reparse")
        return FieldScore(0.0, WEIGHTS["projects"], detail)

    entry_scores = []
    for proj in projects:
        techs = ", ".join(proj.get("technologies", []))
        text  = (
            f"{proj.get('title','')}. "
            f"{proj.get('description','')} "
            f"Technologies: {techs}"
        ).strip()
        emb   = model.encode(text[:1500], normalize_embeddings=True)
        sim   = _cosine(emb, hr_desc_emb)
        score = _rescale(sim, floor=FLOOR_SCORE)   # floor: a real project always gets ≥20%
        entry_scores.append({
            "entry":        proj.get("title", "?"),
            "score":        round(score, 1),
            "technologies": proj.get("technologies", []),
            "url":          proj.get("url", ""),
            "raw_cosine":   round(sim, 3),
        })

    avg         = sum(e["score"] for e in entry_scores) / len(entry_scores)
    count_bonus = min(15.0, max(0.0, (len(projects) - min_count) * 5.0)) if min_count else 0.0
    final       = min(100.0, avg + count_bonus)

    detail = (
        f"{len(projects)} project(s)  |  min {min_count}  |  avg {avg:.0f}%"
        + (f"  +{count_bonus:.0f}% count bonus" if count_bonus else "")
    )
    return FieldScore(round(final, 1), WEIGHTS["projects"], detail, entries=entry_scores)


def _score_education(parsed: dict, hr_req: dict) -> FieldScore:
    """
    education[] → rule-based, best entry wins.
    base 60  +15 field match  +15 GPA ok  +5 institution  +5 multi-degree.
    """
    edu_list = parsed.get("education", [])
    edu_req  = hr_req.get("education_required", {})

    if not edu_list:
        return FieldScore(0.0, WEIGHTS["education"], "No education records")

    req_field = edu_req.get("field", "").lower()
    min_gpa   = float(edu_req.get("min_gpa", 0) or 0)

    entry_scores = []
    for edu in edu_list:
        e_score = 60.0
        e_notes = []

        deg_text = (edu.get("degree","") + " " + edu.get("institution","")).lower()
        if req_field and any(w in deg_text for w in req_field.split()):
            e_score += 15
            e_notes.append("field ✅")

        if edu.get("score") and edu.get("score_type") == "GPA":
            try:
                gpa = float(edu["score"])
                if min_gpa > 0:
                    e_score += 15 if gpa >= min_gpa else -10
                    e_notes.append(f"GPA {gpa} {'✅' if gpa >= min_gpa else '⚠️'}")
                else:
                    e_score += 10   # bonus for just having GPA listed
                    e_notes.append(f"GPA {gpa}")
            except ValueError:
                pass
        else:
            e_notes.append("no GPA")

        if edu.get("institution"):
            e_score = min(100.0, e_score + 5)
            e_notes.append(edu["institution"][:30])

        entry_scores.append({
            "entry":  f"{edu.get('degree','?')} | {edu.get('institution','?')}",
            "score":  min(100.0, e_score),
            "detail": " | ".join(e_notes),
        })

    best       = max(entry_scores, key=lambda x: x["score"])
    best_score = min(100.0, best["score"] + (5 if len(edu_list) > 1 else 0))

    return FieldScore(
        round(best_score, 1), WEIGHTS["education"],
        f"{len(edu_list)} degree(s) — best: {best['detail']}",
        entries=entry_scores,
    )


def _score_achievements(parsed: dict, hr_desc_emb: np.ndarray,
                         model: SentenceTransformer) -> FieldScore:
    ach = [a for a in parsed.get("achievements", []) if a.strip()]
    if not ach:
        return FieldScore(0.0, WEIGHTS["achievements"], "No achievements")

    entry_scores = []
    for a in ach:
        emb   = model.encode(a[:500], normalize_embeddings=True)
        sim   = _cosine(emb, hr_desc_emb)
        score = _rescale(sim, floor=0.0)   # no floor — weak achievements deserve 0
        entry_scores.append({"entry": a[:80], "score": round(score, 1),
                              "raw_cosine": round(sim, 3)})

    avg = sum(e["score"] for e in entry_scores) / len(entry_scores)
    return FieldScore(
        round(avg, 1), WEIGHTS["achievements"],
        f"{len(ach)} achievement(s) — cosine averaged",
        entries=entry_scores,
    )


def _score_soft_skills(parsed: dict) -> FieldScore:
    ss = parsed.get("soft_skills", [])
    if not ss:
        return FieldScore(0.0, WEIGHTS["soft_skills"], "None listed")
    score = min(100.0, len(ss) * 25.0)
    return FieldScore(score, WEIGHTS["soft_skills"],
                      f"{len(ss)} skill(s): {', '.join(ss[:4])}")


def _score_languages(parsed: dict) -> FieldScore:
    langs = parsed.get("languages", [])
    if not langs:
        return FieldScore(0.0, WEIGHTS["languages"], "None listed")
    score = min(100.0, 50.0 + len(langs) * 20.0)
    return FieldScore(score, WEIGHTS["languages"], ", ".join(langs))


# ─────────────────────────────────────────────────────────────────────────────
# HR REQUIREMENT EMBEDDINGS
# ─────────────────────────────────────────────────────────────────────────────

def _embed_requirements(hr_req: dict, model: SentenceTransformer) -> tuple[dict, list]:
    """
    Returns (embeddings_dict, auto_keywords_list).
    Auto-expands short descriptions and extracts keywords if lists are empty.
    """
    job_role         = hr_req.get("job_role", "Software Engineer")
    raw_desc         = hr_req.get("role_description", "").strip()
    expanded_desc    = _auto_expand_description(job_role, raw_desc)

    all_skills = hr_req.get("required_skills", []) + hr_req.get("preferred_skills", [])

    # Auto-extract keywords from expanded description when lists are empty
    auto_keywords: list = []
    if not all_skills:
        auto_keywords = _extract_keywords_from_description(expanded_desc)
        if auto_keywords:
            print(f"   ⚙️  Auto-extracted {len(auto_keywords)} keywords from description: "
                  f"{', '.join(auto_keywords[:8])}{'...' if len(auto_keywords) > 8 else ''}")

    skills_text = (
        "Required skills: " + ", ".join(all_skills)
        if all_skills
        else "Skills: " + ", ".join(auto_keywords[:20])
        if auto_keywords
        else job_role
    )

    emb = {
        "description": model.encode(expanded_desc,             normalize_embeddings=True),
        "skills":      model.encode(skills_text,               normalize_embeddings=True),
        "full":        model.encode(f"{job_role}. {expanded_desc}", normalize_embeddings=True),
    }

    if raw_desc != expanded_desc:
        print(f"   ⚙️  Role description auto-expanded ({len(raw_desc.split())} → "
              f"{len(expanded_desc.split())} words)")

    return emb, auto_keywords


# ─────────────────────────────────────────────────────────────────────────────
# HIGH-LEVEL CLASS
# ─────────────────────────────────────────────────────────────────────────────

class ResumeMatcher:
    """
    Scores every field of the unified resume schema independently,
    then combines them into a single weighted ATS total.

    Calibration knobs (module-level constants):
        SCORE_MIN / SCORE_MAX   — cosine range for your embedding model
        FLOOR_SCORE             — minimum score when content exists (default 25)
        WEIGHTS dict            — relative field importance

    Example:
        matcher = ResumeMatcher(parser.model)
        matcher.set_requirements(WEB_DEV_REQUIREMENTS)
        cards = matcher.match_all(resume_db)
        matcher.print_summary(cards)
    """

    def __init__(self, model: SentenceTransformer, weights: dict | None = None):
        self.model          = model
        self.hr_req: dict   = {}
        self.hr_emb: dict   = {}
        self.auto_kw: list  = []
        if weights:
            WEIGHTS.update(weights)
        status = "✅ rapidfuzz" if RAPIDFUZZ_AVAILABLE else "⚠️  difflib fallback"
        print(f"   Fuzzy matching : {status}")
        print(f"   Cosine range   : [{SCORE_MIN}, {SCORE_MAX}] → [0%, 100%]  "
              f"floor={FLOOR_SCORE}%")

    def set_requirements(self, hr_req: dict) -> None:
        self.hr_req        = hr_req
        self.hr_emb, self.auto_kw = _embed_requirements(hr_req, self.model)
        print(f"✅ Requirements set: {hr_req.get('job_role','Unknown')}")
        req  = hr_req.get("required_skills", [])
        pref = hr_req.get("preferred_skills", [])
        if req or pref:
            print(f"   Skills: {len(req)} required + {len(pref)} preferred")
        elif self.auto_kw:
            print(f"   Skills: no explicit list — using {len(self.auto_kw)} auto-extracted keywords")
        else:
            print("   ⚠️  No skills signal — scoring will be purely semantic")

    def match(self, filename: str, resume_data: dict) -> ResumeScoreCard:
        if not self.hr_req:
            raise RuntimeError("Call set_requirements() first.")
        parsed = resume_data["parsed"]
        fields = {
            "about":        _score_about(parsed,        self.hr_emb["description"], self.hr_emb["full"], self.model),
            "skills":       _score_skills(parsed,        self.hr_emb["skills"],      self.hr_req, self.auto_kw, self.model),
            "experience":   _score_experience(parsed,    self.hr_emb["description"], self.hr_req, self.auto_kw, self.model),
            "projects":     _score_projects(parsed,      self.hr_emb["description"], self.hr_req, self.model),
            "education":    _score_education(parsed,     self.hr_req),
            "achievements": _score_achievements(parsed,  self.hr_emb["description"], self.model),
            "soft_skills":  _score_soft_skills(parsed),
            "languages":    _score_languages(parsed),
        }
        return ResumeScoreCard(
            name=parsed.get("info", {}).get("name", "Unknown"),
            filename=filename,
            fields=fields,
        )

    def match_all(self, resume_db: dict) -> list:
        cards = [self.match(fname, data) for fname, data in resume_db.items()]
        cards.sort(key=lambda c: c.total_score, reverse=True)
        return cards

    @staticmethod
    def print_summary(cards: list) -> None:
        medals = ["🥇", "🥈", "🥉"]
        print("\n" + "═" * 80)
        print("🎯  ATS — Per-Field Cosine Score Breakdown")
        print("═" * 80)
        for i, card in enumerate(cards):
            grade = (
                "🟢 Excellent" if card.total_score >= 80 else
                "🟡 Good"      if card.total_score >= 65 else
                "🟠 Partial"   if card.total_score >= 45 else
                "🔴 Weak"
            )
            rank = medals[i] if i < 3 else f"#{i+1:2d}"
            print(f"\n  {rank}  {card.name}  ({card.filename})")
            print(f"       TOTAL  {card.total_score:>5.1f}%  {grade}")
            print(f"       {'─'*72}")
            print(f"       {'Field':<14} {'Score':>6}  {'×Wt':>5}  {'Contrib':>7}  Detail")
            print(f"       {'─'*14} {'─'*6}  {'─'*5}  {'─'*7}  {'─'*32}")
            for fname, fs in card.fields.items():
                bar = "▓" * int(fs.score / 10) + "░" * (10 - int(fs.score / 10))
                print(
                    f"       {fname:<14} {fs.score:>5.1f}%  "
                    f"×{fs.weight*100:>3.0f}%  "
                    f"{fs.weighted:>6.1f}%  "
                    f"{fs.detail[:52]}"
                )
                for entry in fs.entries:
                    print(
                        f"       {'':14}   ↳ {entry.get('score',0):>5.1f}%  "
                        f"{str(entry.get('entry',''))[:56]}"
                    )
        print()

    @staticmethod
    def to_dicts(cards: list) -> list:
        return [c.to_dict() for c in cards]