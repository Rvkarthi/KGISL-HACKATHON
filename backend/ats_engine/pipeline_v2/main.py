"""
main.py  (v5 — Unified Schema)
────────────────────────────────────────────────────────────────
ATS Resume Screening System — CLI Entry Point

Usage:
    # Parse new PDFs, store in DB, score them
    python main.py --resumes ./resumes/ --role web --output results.json

    # Score candidates already in the DB
    python main.py --from-db --role dl

    # Semantic search on a specific resume section
    python main.py --search-section projects "machine learning recommendation system"
    python main.py --search-section skills "React.js Node.js REST API"

    # List all resumes in the database
    python main.py --list-db

    # Delete a resume from the database
    python main.py --delete alice_smith.pdf

Available roles: web | dl | data | devops | custom
"""

import argparse
import json
import sys
import numpy as np
from pathlib import Path

from parser    import ResumeParser
from matcher   import ResumeMatcher
from clusterer import ResumeClusterer
from requirements import ROLE_MAP
from ats_vector_db import (
    store_resumes_vector,
    query_resumes_vector,
    search_section,
    list_resumes,
    delete_resume,
    count_resumes,
)

# ── CONFIG ────────────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════╗
║         ATS Resume Screening System  v5              ║
║  parser · matcher · clusterer · MongoDB vector DB    ║
╚══════════════════════════════════════════════════════╝
"""

VALID_SECTIONS = ["skills", "experience", "projects", "education", "about", "full"]


# ── HELPERS ───────────────────────────────────────────────────────────────────

def collect_pdfs(path: str) -> list:
    p = Path(path)
    if p.is_file() and p.suffix.lower() == ".pdf":
        return [str(p)]
    if p.is_dir():
        pdfs = sorted(str(f) for f in p.glob("*.pdf"))
        if not pdfs:
            print(f"⚠️  No PDF files found in: {path}")
        return pdfs
    print(f"❌  Path not found: {path}")
    return []


def print_ats_results(results: list) -> None:
    # results is now a list of ResumeScoreCard — delegate to matcher's printer
    ResumeMatcher.print_summary(results)


def build_custom_requirements() -> dict:
    print("\n📝  Enter custom HR requirements:\n")
    job_role    = input("   Job role title                     : ").strip()
    description = input("   Role description                   : ").strip()
    req_raw     = input("   Required skills (comma-separated)  : ").strip()
    pref_raw    = input("   Preferred skills (comma-separated) : ").strip()
    freshers    = input("   Freshers allowed? (y/n)            : ").strip().lower() == "y"
    field       = input("   Education field required            : ").strip()
    min_count   = input("   Minimum projects required (default 1): ").strip()
    return {
        "job_role":         job_role,
        "role_description": description,
        "required_skills":  [s.strip() for s in req_raw.split(",")  if s.strip()],
        "preferred_skills": [s.strip() for s in pref_raw.split(",") if s.strip()],
        "experience_required": {"freshers_allowed": freshers, "description": ""},
        "education_required":  {"field": field, "min_gpa": 0},
        "projects_required":   {"min_count": int(min_count) if min_count.isdigit() else 1, "description": ""},
    }


def export_json(resume_db, results, clusters, hr_req, output_path):
    output = {
        "job_role":    hr_req.get("job_role", ""),
        "ats_results": ResumeMatcher.to_dicts(results),
        "clusters":   clusters,
        "parsed_resumes": [
            # export public schema only, exclude internal _meta.raw_sections to keep file small
            {
                **{k: v for k, v in data["parsed"].items() if k != "_meta"},
                "_meta": {
                    mk: mv for mk, mv in data["parsed"].get("_meta", {}).items()
                    if mk != "raw_sections"
                },
            }
            for data in resume_db.values()
        ],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"✅  Results exported → {output_path}")


def _normalize_str_dict(val) -> str:
    """
    SLM sometimes returns {'language': 'English', 'proficiency': 'Fluent'}.
    When stored in MongoDB and reloaded, it comes back as a Python repr string
    like "{'language': 'English', ...}".  This collapses it to 'English (Fluent)'.
    """
    if isinstance(val, dict):
        lang = val.get("language") or val.get("name") or val.get("lang", "")
        prof = val.get("proficiency") or val.get("level") or val.get("fluency", "")
        return f"{lang} ({prof})" if lang and prof else lang or str(val)
    s = str(val).strip()
    # Looks like a stringified dict  e.g.  "{'language': 'English', 'proficiency': 'Fluent'}"
    if s.startswith("{") and "language" in s:
        import ast
        try:
            d = ast.literal_eval(s)
            return _normalize_str_dict(d)
        except Exception:
            pass
    return s


def _sanitize_list_field(lst) -> list:
    """Ensure every element in a list is a clean string (no dicts, no repr-dicts)."""
    if not isinstance(lst, list):
        return []
    result = []
    for item in lst:
        cleaned = _normalize_str_dict(item).strip()
        if cleaned and not cleaned.startswith("{"):
            result.append(cleaned)
    return result


def _sanitize_parsed(parsed: dict) -> dict:
    """
    Fix issues introduced by the old regex parser or SLM format quirks:
      - languages stored as dicts  → flatten to 'English (Fluent)'
      - skills/soft_skills stored as dicts → extract name
      - experience/education/projects stored as empty {} → convert to []
      - missing _meta keys → inject defaults
    """
    # Fix list fields that may contain dicts
    for field in ("languages", "skills", "soft_skills", "achievements"):
        parsed[field] = _sanitize_list_field(parsed.get(field, []))

    # Fix list-of-object fields — ensure proper structure
    for exp in parsed.get("experience", []):
        if isinstance(exp, dict):
            exp["description"] = str(exp.get("description", "")).strip()

    for proj in parsed.get("projects", []):
        if isinstance(proj, dict):
            proj["description"]  = str(proj.get("description", "")).strip()
            proj["technologies"] = _sanitize_list_field(proj.get("technologies", []))

    # Ensure _meta exists with required keys
    if "_meta" not in parsed or not isinstance(parsed["_meta"], dict):
        parsed["_meta"] = {}

    meta = parsed["_meta"]

    # Rebuild raw_sections if missing or empty (old regex parser stored them differently)
    if not meta.get("raw_sections"):
        meta["raw_sections"] = {
            "about":        parsed.get("about", ""),
            "skills":       " ".join(parsed.get("skills", []) + parsed.get("soft_skills", [])),
            "experience":   " ".join(
                f"{e.get('title','')} {e.get('company','')} {e.get('description','')}"
                for e in parsed.get("experience", []) if isinstance(e, dict)
            ),
            "projects":     " ".join(
                f"{p.get('title','')} {p.get('description','')} {' '.join(p.get('technologies',[]))}"
                for p in parsed.get("projects", []) if isinstance(p, dict)
            ),
            "education":    " ".join(
                f"{e.get('degree','')} {e.get('institution','')}"
                for e in parsed.get("education", []) if isinstance(e, dict)
            ),
            "achievements": " ".join(parsed.get("achievements", [])),
        }

    # Ensure is_fresher exists
    if "is_fresher" not in meta:
        exp = parsed.get("experience", [])
        meta["is_fresher"] = not any(
            any(w in str(e.get("title","")).lower()
                for w in ("engineer","developer","analyst","scientist","manager","lead"))
            for e in exp if isinstance(e, dict)
        ) if exp else True

    if "years_of_experience" not in meta:
        meta["years_of_experience"] = 0.0

    return parsed


def _db_docs_to_resume_db(docs: list) -> dict:
    """
    Convert MongoDB documents → resume_db format.
    Applies _sanitize_parsed() to fix old regex-parser data and SLM format quirks
    so that fields like languages, projects, education score correctly.
    """
    resume_db = {}
    fixed = 0
    for doc in docs:
        filename   = doc["filename"]
        raw_parsed = doc.get("parsed", {})
        sanitized  = _sanitize_parsed(raw_parsed)

        # Warn if this looks like old regex-parsed data (no real content in projects/education)
        has_projects = bool(sanitized.get("projects"))
        has_education = bool(sanitized.get("education"))
        if not has_projects and not has_education:
            fixed += 1

        embeddings = {
            k: np.array(v, dtype=np.float32)
            for k, v in doc.get("embeddings", {}).items()
            if v
        }
        resume_db[filename] = {
            "parsed":     sanitized,
            "embeddings": embeddings,
        }
    if fixed:
        print(f"   ⚠️  {fixed}/{len(docs)} resume(s) have no projects/education "
              f"— run with --reparse ./resumes/ to re-extract with SLM")
    return resume_db


# ── COMMAND HANDLERS ──────────────────────────────────────────────────────────

def _handle_clear_db():
    """Wipe the entire MongoDB collection."""
    from ats_vector_db import _get_collection
    col   = _get_collection()
    count = col.count_documents({})
    if count == 0:
        print("📭  Database already empty.")
        return
    col.delete_many({})
    print(f"🗑️  Cleared {count} resume(s) from MongoDB.")
    print("   Run: python main.py --resumes <folder> --role <role>  to re-parse.")


def handle_list_db():
    docs  = list_resumes()
    total = count_resumes()
    if not docs:
        print("📭  Database is empty. Run with --resumes to add resumes.")
        return
    print(f"\n📋  MongoDB — {total} resume(s) stored")
    print("-" * 65)
    for d in docs:
        print(f"  • {d.get('candidate_name','?'):<28}  "
              f"{d['filename']:<25}  "
              f"{d.get('primary_domain','Unknown')}")
    print()


def handle_delete(filename: str):
    delete_resume(filename)


def handle_search_section(section: str, query: str, model):
    if section not in VALID_SECTIONS:
        print(f"❌  Invalid section '{section}'. Choose from: {', '.join(VALID_SECTIONS)}")
        sys.exit(1)
    print(f"\n🔍  Searching section='{section}' for: \"{query}\"\n")
    top_docs = search_section(section, query, top_n=10, model=model)
    if not top_docs:
        print("   No results found.")
        return
    print(f"   Top {len(top_docs)} result(s):\n")
    for i, doc in enumerate(top_docs, 1):
        name   = doc["parsed"].get("info", {}).get("name", "Unknown")
        fname  = doc["filename"]
        domain = doc.get("primary_domain", "?")
        skills = doc["parsed"].get("skills", [])[:5]
        print(f"  {i}. {name:<28}  ({fname})")
        print(f"     Domain : {domain}")
        print(f"     Skills : {', '.join(skills) or 'N/A'}")
        print()


def handle_parse_and_store(pdf_paths, resume_parser, resume_clusterer):
    print(f"\n⚙️   Parsing {len(pdf_paths)} resume(s)...\n")
    resume_db = resume_parser.process_many(pdf_paths)
    print(f"\n✅  Parsed {len(resume_db)} resume(s).")
    print("\n⚙️   Clustering resumes...")
    clusters = resume_clusterer.cluster(resume_db)
    resume_clusterer.print_summary(clusters)
    store_resumes_vector(resume_db, clusters)
    return resume_db, clusters


def handle_from_db(model):
    print("\n📂  Loading all resumes from MongoDB...")
    docs = query_resumes_vector(domain="all", top_n=500, model=model)
    if not docs:
        print("❌  Database is empty. Run with --resumes first.")
        sys.exit(1)
    resume_db = _db_docs_to_resume_db(docs)
    print(f"✅  Loaded {len(resume_db)} resume(s) from MongoDB.")
    return resume_db


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    cli = argparse.ArgumentParser(
        description="ATS Resume Screening System v5",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    src = cli.add_mutually_exclusive_group()
    src.add_argument("--resumes", "-r",
        help="Path to a PDF file or folder of PDFs")
    src.add_argument("--from-db", action="store_true",
        help="Load resumes from MongoDB instead of parsing PDFs")
    cli.add_argument("--list-db", action="store_true",
        help="List all resumes in MongoDB and exit")
    cli.add_argument("--delete", metavar="FILENAME",
        help="Delete a resume from MongoDB by filename and exit")
    cli.add_argument("--search-section", nargs=2, metavar=("SECTION", "QUERY"),
        help=(
            f"Semantic search a resume section.\n"
            f"  SECTION: {' | '.join(VALID_SECTIONS)}\n"
            '  Example: --search-section projects "ML recommendation engine"'
        ))

    cli.add_argument("--role", default="web",
        choices=list(ROLE_MAP.keys()) + ["custom"],
        help=f"HR requirement preset. Choices: {', '.join(ROLE_MAP.keys())}, custom  (default: web)")
    cli.add_argument("--output", "-o",
        help="Export results to JSON file")
    cli.add_argument("--slm",
        default=None,
        help="Hugging Face SLM model name (default: Qwen/Qwen2.5-1.5B-Instruct)")
    cli.add_argument("--reparse", action="store_true",
        help=(
            "Re-parse all stored resumes with the SLM.\n"
            "Clears stale MongoDB records and re-runs extraction.\n"
            "Use this whenever parser.py changes.\n"
            "Requires --resumes <folder>."
        ))
    cli.add_argument("--clear-db", action="store_true",
        help="Wipe all resumes from MongoDB and exit.")

    args = cli.parse_args()
    print(BANNER)

    # ── DB utility commands (no model needed) ─────────────────────────────────
    if args.list_db:
        handle_list_db()
        return

    if args.delete:
        handle_delete(args.delete)
        return

    if args.clear_db:
        _handle_clear_db()
        return

    # ── Load the pipeline ─────────────────────────────────────────────────────
    print("⏳  Loading pipeline...")
    kwargs = {}
    if args.slm:
        kwargs["slm_name"] = args.slm
    resume_parser    = ResumeParser(**kwargs)
    resume_matcher   = ResumeMatcher(resume_parser.model)
    resume_clusterer = ResumeClusterer(resume_parser.model)
    model            = resume_parser.model

    # ── Search-only mode ──────────────────────────────────────────────────────
    if args.search_section:
        section, query = args.search_section
        handle_search_section(section, query, model)
        return

    # ── HR requirements ───────────────────────────────────────────────────────
    if args.role == "custom":
        hr_req = build_custom_requirements()
    else:
        hr_req = ROLE_MAP[args.role]
    print(f"\n🎯  Role     : {hr_req['job_role']}")
    print(f"    Required : {hr_req.get('required_skills', [])}")

    # ── Populate resume_db ────────────────────────────────────────────────────
    clusters = {}

    if args.reparse:
        # Re-parse: wipe DB entries for these files, parse fresh with SLM
        if not args.resumes:
            print("❌  --reparse requires --resumes <folder>  e.g.:")
            print("    python main.py --resumes ./resumes/ --reparse --role web")
            sys.exit(1)
        pdf_paths = collect_pdfs(args.resumes)
        if not pdf_paths:
            print(f"❌  No PDFs found in '{args.resumes}'.")
            sys.exit(1)
        print(f"\n🔄  Re-parsing {len(pdf_paths)} resume(s) — clearing stale DB records...")
        for p in pdf_paths:
            fname = Path(p).name
            delete_resume(fname)
            print(f"   🗑️  Cleared: {fname}")
        print()
        resume_db, clusters = handle_parse_and_store(pdf_paths, resume_parser, resume_clusterer)

    elif args.resumes:
        pdf_paths = collect_pdfs(args.resumes)
        if not pdf_paths:
            print("❌  No PDFs found. Exiting.")
            sys.exit(1)
        print(f"\n📄  Found {len(pdf_paths)} PDF(s):\n" + "\n".join(f"     {p}" for p in pdf_paths))
        resume_db, clusters = handle_parse_and_store(pdf_paths, resume_parser, resume_clusterer)

    elif args.from_db:
        resume_db = handle_from_db(model)

    else:
        db_count = count_resumes()
        if db_count > 0:
            print(f"\n💡  {db_count} resume(s) found in MongoDB.")
            choice = input("   Load from database? (y/n, default y): ").strip().lower()
            if choice != "n":
                resume_db = handle_from_db(model)
            else:
                print("❌  No resumes to process. Provide --resumes or --from-db.")
                sys.exit(1)
        else:
            print("❌  No --resumes provided and database is empty.")
            print("    Run: python main.py --resumes ./resumes/ --role web")
            sys.exit(1)

    # ── ATS Matching ──────────────────────────────────────────────────────────
    print("\n⚙️   Running ATS matching...")
    resume_matcher.set_requirements(hr_req)
    results = resume_matcher.match_all(resume_db)
    print_ats_results(results)

    # ── Clustering ────────────────────────────────────────────────────────────
    if not clusters:
        print("⚙️   Clustering resumes...")
        clusters = resume_clusterer.cluster(resume_db)
        resume_clusterer.print_summary(clusters)

    # ── Export ────────────────────────────────────────────────────────────────
    if args.output:
        clusters_s = {
            domain: [{k: v for k, v in m.items()} for m in members]
            for domain, members in clusters.items()
        }
        export_json(resume_db, results, clusters_s, hr_req, args.output)

    print("✅  Done!\n")


if __name__ == "__main__":
    main()