# 🎯 ATS Resume Screening System  v4

> **AI-powered Applicant Tracking System with persistent MongoDB vector storage.**  
> Parse PDFs once, store forever, search semantically, score against any HR role.

Built with: spaCy · sentence-transformers · MongoDB · Tesseract OCR · rapidfuzz · pdfplumber

---

## 📋 Table of Contents

1. [What's New in v4](#-whats-new-in-v4)
2. [Full Architecture](#-full-architecture)
3. [Project Structure](#-project-structure)
4. [System Requirements](#-system-requirements)
5. [Step-by-Step Installation](#-step-by-step-installation)
6. [Quick Start](#-quick-start)
7. [CLI Commands — Complete Reference](#-cli-commands--complete-reference)
8. [Workflow Guide](#-workflow-guide)
9. [Python API Usage](#-python-api-usage)
10. [Vector DB API Reference](#-vector-db-api-reference)
11. [HR Requirements Config](#-hr-requirements-config)
12. [Understanding the Output](#-understanding-the-output)
13. [Scoring Breakdown](#-scoring-breakdown)
14. [Troubleshooting](#-troubleshooting)
15. [FAQ](#-faq)

---

## 🆕 What's New in v4

| Feature | v3 | v4 |
|---------|----|----|
| Parse PDFs | ✅ | ✅ |
| ATS scoring | ✅ | ✅ |
| Domain clustering | ✅ | ✅ |
| **MongoDB storage** | ❌ | ✅ |
| **Re-score without re-parsing** | ❌ | ✅ `--from-db` |
| **Semantic section search** | ❌ | ✅ `--search-section` |
| **List / delete DB records** | ❌ | ✅ `--list-db` / `--delete` |
| **Upsert (no duplicate records)** | ❌ | ✅ |

---

## 🧠 Full Architecture

```
PDF Resumes (one-time)
       │
       ▼
┌──────────────────────────────────────────────────┐
│  STAGE 1 — PARSER  (parser.py)                   │
│  pdfplumber → pdfminer → Tesseract OCR           │
│  spaCy NER → structured JSON + embeddings        │
└────────────────────────┬─────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────┐
│  STAGE 2 — CLUSTERER  (clusterer.py)             │
│  Cosine similarity + rapidfuzz keyword boost     │
│  → assigns primary domain label per resume       │
└────────────────────────┬─────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────┐
│  STAGE 3 — VECTOR DB  (ats_vector_db.py)         │
│  MongoDB upsert:                                 │
│    • parsed JSON fields                          │
│    • all embeddings (skills/exp/projects/full)   │
│    • primary domain + confidence score           │
└────────────┬────────────────────┬────────────────┘
             │                    │
             ▼                    ▼
┌─────────────────┐    ┌──────────────────────────┐
│  STAGE 4        │    │  SEMANTIC SEARCH          │
│  MATCHER        │    │  search_section()         │
│  (matcher.py)   │    │                           │
│                 │    │  Query any section by     │
│  Score resumes  │    │  free-text:               │
│  from DB or     │    │  skills / projects /      │
│  fresh parse    │    │  experience / education   │
│  against HR req │    │                           │
└────────┬────────┘    └──────────────────────────┘
         │
         ▼
   Ranked candidates
   JSON export
```

---

## 📁 Project Structure

```
ats_system/
│
├── 📄 main.py              ← Entry point — all CLI commands here
├── 📄 parser.py            ← PDF extraction + NER + embeddings
├── 📄 matcher.py           ← ATS scoring engine (rapidfuzz + semantic)
├── 📄 clusterer.py         ← Domain clustering (cosine + keyword boost)
├── 📄 ats_vector_db.py     ← MongoDB storage + search  ← NEW in v4
├── 📄 requirements.py      ← HR requirement presets
├── 📄 __init__.py          ← Package definition
├── 📄 install.sh           ← One-shot installer (includes MongoDB)
└── 📄 README.md            ← This file

your-project/
├── ats_system/             ← The module folder
├── resumes/                ← Drop PDFs here
│   ├── alice_cv.pdf
│   └── bob_cv.pdf
└── results.json            ← Exported output
```

---

## 💻 System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.10+ | 3.11+ |
| RAM | 4 GB | 8 GB+ |
| Disk | 5 GB | 10 GB (model cache) |
| MongoDB | 5.0+ | 7.0+ |
| OS | Windows / macOS / Linux | Ubuntu 20.04+ |

> ⚠️ First run downloads ~1.5 GB of model files. Subsequent runs use cache.

---

## 🚀 Step-by-Step Installation

### Step 1 — Create a virtual environment

```bash
python -m venv venv

# Activate:
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate.bat         # Windows CMD
venv\Scripts\Activate.ps1         # Windows PowerShell
```

---

### Step 2 — Install Tesseract OCR

**Ubuntu / Debian / WSL:**
```bash
sudo apt update && sudo apt install -y tesseract-ocr tesseract-ocr-eng
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki  
Then add `C:\Program Files\Tesseract-OCR\` to your PATH.

**Verify:**
```bash
tesseract --version
# tesseract 5.x.x
```

---

### Step 3 — Install and start MongoDB

**Ubuntu / Debian / WSL:**
```bash
sudo apt install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb      # auto-start on boot
```

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Docker (easiest — works on all OS):**
```bash
docker run -d -p 27017:27017 --name mongo mongo:7
# To start again after reboot:
docker start mongo
```

**Windows:**
Download MongoDB Community Server: https://www.mongodb.com/try/download/community  
Or use Docker (recommended).

**Verify MongoDB is running:**
```bash
mongosh --eval "db.runCommand({ connectionStatus: 1 })"
# Should print: ok: 1
```

---

### Step 4 — Install Python packages

```bash
pip install pdfplumber "pdfminer.six" PyMuPDF pytesseract Pillow \
            spacy dateparser rapidfuzz \
            sentence-transformers scikit-learn numpy torch \
            pymongo
```

---

### Step 5 — Download spaCy model

```bash
python -m spacy download en_core_web_md
```

---

### Step 6 — Verify everything

```bash
python -c "
import pdfplumber, fitz, pytesseract, spacy, dateparser, rapidfuzz, pymongo
from sentence_transformers import SentenceTransformer
print('✅ All packages OK')
print('   Tesseract:', pytesseract.get_tesseract_version())
from pymongo import MongoClient
MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000).server_info()
print('   MongoDB  : connected')
"
```

---

### OR: One-shot installer

```bash
chmod +x install.sh
bash install.sh
```

---

## ⚡ Quick Start

```bash
# First time — parse and store resumes
python main.py --resumes ./resumes/ --role web --output results.json

# Later — re-score same resumes without re-parsing
python main.py --from-db --role dl

# Find the best candidates for a project query
python main.py --search-section projects "e-commerce recommendation engine"

# See what's in the database
python main.py --list-db
```

---

## 📟 CLI Commands — Complete Reference

### Synopsis
```
python main.py [INPUT] [UTILITY] [--role ROLE] [--output FILE]
```

---

### Input flags (choose one)

| Flag | Description |
|------|-------------|
| `--resumes ./folder/` | Parse all PDFs in a folder, store in MongoDB, then score |
| `--resumes file.pdf` | Parse a single PDF, store in MongoDB, then score |
| `--from-db` | Skip parsing — load resumes already stored in MongoDB |
| *(none)* | Auto-detects: if DB has data, asks to load it |

---

### Utility flags (run and exit)

| Flag | Example | Description |
|------|---------|-------------|
| `--list-db` | `python main.py --list-db` | Print all resumes in MongoDB |
| `--delete FILENAME` | `python main.py --delete alice.pdf` | Remove one resume from DB |
| `--search-section SECTION QUERY` | see below | Semantic search on a section |

---

### Search sections

```bash
# Skills search
python main.py --search-section skills "React.js Node.js PostgreSQL"

# Projects search
python main.py --search-section projects "machine learning recommendation system"

# Experience search
python main.py --search-section experience "backend API microservices"

# Education search
python main.py --search-section education "computer science machine learning"

# Full resume search
python main.py --search-section full "DevOps cloud infrastructure AWS"
```

Valid sections: `skills` | `experience` | `projects` | `education` | `summary` | `full`

---

### Scoring flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--role web` | — | `web` | Score against web dev requirements |
| `--role dl` | — | — | Score against deep learning requirements |
| `--role custom` | — | — | Enter requirements interactively |
| `--output file.json` | `-o` | none | Export results to JSON |

---

### All command examples

```bash
# ── PARSE + STORE + SCORE ────────────────────────────────────────────
python main.py --resumes ./resumes/ --role web --output results.json
python main.py --resumes ./resumes/ --role dl  --output dl_results.json
python main.py --resumes candidate.pdf --role web

# ── SCORE FROM DB (no re-parsing) ───────────────────────────────────
python main.py --from-db --role web
python main.py --from-db --role dl  --output results.json
python main.py --from-db --role custom

# ── DATABASE MANAGEMENT ─────────────────────────────────────────────
python main.py --list-db
python main.py --delete alice_smith.pdf
python main.py --delete "bob jones cv.pdf"

# ── SEMANTIC SEARCH ──────────────────────────────────────────────────
python main.py --search-section skills    "Python FastAPI PostgreSQL Docker"
python main.py --search-section projects  "e-commerce web app spring boot"
python main.py --search-section experience "team lead agile backend"
python main.py --search-section full      "deep learning computer vision"

# ── CUSTOM HR REQUIREMENTS ───────────────────────────────────────────
python main.py --resumes ./resumes/ --role custom --output custom_results.json
```

---

## 🔧 Workflow Guide

### Scenario A — First-time screening (new batch of resumes)

```bash
# 1. Drop PDF resumes into a folder
mkdir resumes
# Copy CVs into resumes/

# 2. Parse, cluster, store in DB, score — all in one command
python main.py --resumes ./resumes/ --role web --output results.json

# 3. View results
cat results.json
```

---

### Scenario B — Re-score the same candidates for a different role

```bash
# Resumes are already in MongoDB from the previous run
# No need to re-parse — just load and score against new role

python main.py --from-db --role dl --output dl_results.json
```

---

### Scenario C — Add more resumes to an existing DB

```bash
# New CVs arrived — add them without affecting existing records
python main.py --resumes ./new_resumes/ --role web --output updated.json
# Existing resumes are updated (upsert), new ones are inserted
```

---

### Scenario D — Find the best candidate for a specific requirement

```bash
# Search for candidates with machine learning project experience
python main.py --search-section projects "deep learning image classification"

# Search for candidates with specific skills
python main.py --search-section skills "Kubernetes Docker CI/CD AWS"
```

---

### Scenario E — Clean up the database

```bash
# See what's stored
python main.py --list-db

# Remove a specific candidate
python main.py --delete old_candidate.pdf

# Or clear everything in MongoDB shell:
mongosh ats_db --eval "db.resumes.deleteMany({})"
```

---

## 🐍 Python API Usage

### Full pipeline

```python
from ats_system.parser       import ResumeParser
from ats_system.matcher      import ResumeMatcher
from ats_system.clusterer    import ResumeClusterer
from ats_system.ats_vector_db import store_resumes_vector, query_resumes_vector, search_section

# ── Initialise (load model once) ──────────────────────────────────────
parser    = ResumeParser()
matcher   = ResumeMatcher(parser.model)
clusterer = ResumeClusterer(parser.model)

# ── Parse and store ───────────────────────────────────────────────────
resume_db = parser.process_many(["cv1.pdf", "cv2.pdf"])
clusters  = clusterer.cluster(resume_db)
store_resumes_vector(resume_db, clusters)      # persists to MongoDB

# ── Score ─────────────────────────────────────────────────────────────
HR_REQ = {
    "job_role": "Backend Engineer",
    "role_description": "Python API developer with FastAPI",
    "required_skills":  ["Python", "FastAPI", "PostgreSQL", "Docker"],
    "preferred_skills": ["Redis", "AWS"],
    "projects_required":   {"min_count": 1, "description": "API projects"},
    "education_required":  {"field": "Computer Science"},
    "experience_required": {"freshers_allowed": False},
}
matcher.set_requirements(HR_REQ)
results = matcher.match_all(resume_db)

for r in results:
    print(f"{r['name']:30}  {r['total_score']:.1f}%")
```

---

### Load from DB and re-score

```python
import numpy as np
from ats_system.ats_vector_db import query_resumes_vector

# Fetch all stored resumes
docs = query_resumes_vector(domain="all", top_n=500)

# Reconstruct resume_db
resume_db = {
    doc["filename"]: {
        "parsed":     doc["parsed"],
        "embeddings": {k: np.array(v, dtype=np.float32) for k, v in doc["embeddings"].items()},
    }
    for doc in docs
}

# Score against new requirements
matcher.set_requirements(NEW_HR_REQ)
results = matcher.match_all(resume_db)
```

---

### Semantic section search

```python
from ats_system.ats_vector_db import search_section

# Find best candidates for a project query
top = search_section(
    section = "projects",
    query   = "e-commerce recommendation system with ML",
    top_n   = 5,
    model   = parser.model,
)

for doc in top:
    print(doc["parsed"]["candidate_name"], "—", doc["parsed"]["skills"][:4])
```

---

### DB utilities

```python
from ats_system.ats_vector_db import (
    list_resumes, count_resumes, get_resume, delete_resume
)

print(count_resumes())                       # 12
print(list_resumes())                        # [{filename, candidate_name, domain}, ...]
doc = get_resume("alice_smith.pdf")          # full document dict
delete_resume("old_candidate.pdf")           # remove from DB
```

---

## 🗄️ Vector DB API Reference

### `store_resumes_vector(resume_db, clusters)`
Upsert parsed resumes + embeddings into MongoDB.  
- Uses filename as unique key — safe to call multiple times (no duplicates).
- Stores all embedding vectors as lists for MongoDB compatibility.

```python
store_resumes_vector(resume_db, clusters)
# 💾 Stored / updated 3 resume(s) (2 new, 1 updated)
```

---

### `query_resumes_vector(domain, top_n, model, query)`
Fetch resumes by domain, optionally re-ranked by a query.

```python
# All resumes, no filter
docs = query_resumes_vector(domain="all", top_n=50)

# Domain-filtered
docs = query_resumes_vector(domain="🌐 Web / Full Stack", top_n=10)

# Semantic re-ranking with a query
docs = query_resumes_vector(
    domain="all", top_n=10,
    model=parser.model,
    query="React full stack developer with Node.js"
)
```

---

### `search_section(section, query, top_n, model)`
Semantic cosine similarity search on a specific resume section.

```python
# Search projects
top = search_section("projects", "ML image classification model", top_n=5, model=parser.model)

# Search skills
top = search_section("skills", "cloud AWS Kubernetes DevOps", top_n=5, model=parser.model)
```

---

### `list_resumes()` / `count_resumes()` / `get_resume(filename)` / `delete_resume(filename)`

```python
list_resumes()                   # → [{filename, candidate_name, primary_domain}, ...]
count_resumes()                  # → 12
get_resume("alice_smith.pdf")    # → full document dict
delete_resume("old.pdf")         # → True / False
```

---

## ⚙️ HR Requirements Config

```python
HR_REQUIREMENTS = {
    "job_role":         "Junior Web Developer",
    "role_description": "Full stack developer with HTML/CSS/JS and Spring Boot.",

    # MUST-HAVE — weighted 75% of skills score
    # Fuzzy matched: "React.js" = "ReactJS" = "react js"
    "required_skills":  ["HTML", "CSS", "JavaScript", "Java", "Spring Boot", "MySQL"],

    # Nice-to-have — weighted 20% of skills score
    "preferred_skills": ["React.js", "REST API", "Docker", "Git"],

    "projects_required": {
        "min_count":   2,
        "description": "Web application projects with frontend + backend",
    },

    "education_required": {
        "degree":   "Bachelor of Computer Science",
        "field":    "Computer Science or related",
        "min_gpa":  7.0,      # set 0 to skip GPA check
    },

    "experience_required": {
        "freshers_allowed": True,
        # True  → fresher scores 45/100 (fair chance)
        # False → fresher scores 0/100 (disqualified)
        "description": "Project-based experience acceptable.",
    },
}
```

**Adding a new preset:**

1. Add to `requirements.py`:
```python
DATA_ANALYST_REQUIREMENTS = {
    "job_role": "Data Analyst",
    ...
}
```

2. Register in `main.py`:
```python
from requirements import DATA_ANALYST_REQUIREMENTS
ROLE_MAP["analyst"] = DATA_ANALYST_REQUIREMENTS
```

3. Use it:
```bash
python main.py --resumes ./resumes/ --role analyst
```

---

## 📊 Understanding the Output

### Score grades

| Score | Grade | Action |
|-------|-------|--------|
| 80–100% | 🟢 Excellent | Shortlist immediately |
| 60–79% | 🟡 Good | Schedule interview |
| 45–59% | 🟠 Partial | Consider with caution |
| 0–44% | 🔴 Weak | Not suitable |

### JSON output (`results.json`)

```json
{
  "job_role": "Junior Web Developer",
  "ats_results": [
    {
      "name": "Alice Smith",
      "filename": "alice_smith.pdf",
      "total_score": 81.4,
      "section_scores": {
        "skills": 85.0,
        "experience": 72.0,
        "projects": 68.0,
        "education": 80.0,
        "summary": 74.0
      },
      "details": {
        "skills":     "8/10 required, 4/6 preferred",
        "experience": "2 job(s) | 6/10 skills in exp",
        "projects":   "2 project(s) (dedicated section)",
        "education":  "GPA 8.7 | Field matched ✅ | State University"
      }
    }
  ],
  "clusters": {
    "🌐 Web / Full Stack": [
      {
        "name":            "Alice Smith",
        "primary_score":   81.4,
        "secondary":       "📊 Data Science",
        "secondary_score": 72.1,
        "richness":        78,
        "top_skills":      ["React", "JavaScript", "MySQL", "Spring Boot"]
      }
    ]
  }
}
```

---

## 📐 Scoring Breakdown

```
Total Score =
  (skills     × 0.37)
+ (experience × 0.15)
+ (projects   × 0.20)
+ (education  × 0.40)
+ (summary    × 0.30)
```

| Section | Weight | How scored |
|---------|--------|------------|
| Skills | 37% | required_matched/total × 75% + preferred × 20% + depth bonus |
| Experience | 15% | keyword overlap 50% + semantic similarity 50% |
| Projects | 20% | count vs min_count 40% + semantic similarity 60% |
| Education | 40% | base 70 + field match +10 + GPA ±20 + institution +5 |
| Summary | 30% | cosine similarity vs role description |

---

## 🔧 Troubleshooting

| Error | Fix |
|-------|-----|
| `TesseractNotFoundError` | `sudo apt install tesseract-ocr` (Linux) or `brew install tesseract` (Mac) |
| `Can't find model 'en_core_web_md'` | `python -m spacy download en_core_web_md` |
| `No module named 'fitz'` | `pip install PyMuPDF` |
| `No module named 'pymongo'` | `pip install pymongo` |
| `ServerSelectionTimeoutError` | MongoDB not running. Run `sudo systemctl start mongodb` or `docker start mongo` |
| `No module named 'rapidfuzz'` | `pip install rapidfuzz` |
| Low text / blank extraction | PDF is scanned — Tesseract auto-activates. If still failing, PDF may be password-protected. |
| Wrong name extracted | Override: `resume_db["file.pdf"]["parsed"]["candidate_name"] = "Correct Name"` |
| Out of memory | `ResumeParser(model_name="BAAI/bge-small-en-v1.5")` — smaller model |
| Slow first run | Normal — downloading ~1.5 GB. Cached after first run. |

---

## ❓ FAQ

**Q: If I run `--resumes` twice with the same PDFs, will it create duplicates?**  
No. MongoDB uses the filename as a unique key and upserts (updates) existing records.

**Q: Can I change the HR role and re-score without re-parsing?**  
Yes — use `--from-db --role dl` to load from the database and score against a new role.

**Q: Can I store resumes from multiple different batches?**  
Yes. Each `--resumes` run adds new files and updates existing ones. All accumulate in MongoDB.

**Q: How do I reset the database completely?**  
```bash
mongosh ats_db --eval "db.resumes.deleteMany({})"
```

**Q: Can I use a remote MongoDB (Atlas)?**  
Yes. Change `MONGO_URI` in `ats_vector_db.py`:
```python
MONGO_URI = "mongodb+srv://user:password@cluster.mongodb.net/"
```

**Q: Can I use this in a Flask/FastAPI app?**  
```python
from ats_system.parser       import ResumeParser
from ats_system.matcher      import ResumeMatcher
from ats_system.ats_vector_db import store_resumes_vector, query_resumes_vector
import numpy as np

parser  = ResumeParser()        # load ONCE at startup
matcher = ResumeMatcher(parser.model)

@app.post("/upload")
def upload(pdf_path: str):
    db = parser.process_many([pdf_path])
    clusters = clusterer.cluster(db)
    store_resumes_vector(db, clusters)
    return {"status": "stored"}

@app.post("/score")
def score(hr_req: dict):
    docs = query_resumes_vector(domain="all", top_n=500)
    resume_db = {
        d["filename"]: {
            "parsed": d["parsed"],
            "embeddings": {k: np.array(v, dtype=np.float32) for k,v in d["embeddings"].items()}
        } for d in docs
    }
    matcher.set_requirements(hr_req)
    return matcher.match_all(resume_db)
```

---

## 🛠️ Tech Stack

| Library | Purpose |
|---------|---------|
| `pdfplumber` | Spatial word-position PDF extraction |
| `pdfminer.six` | Fallback for complex font encodings |
| `PyMuPDF (fitz)` | 300 DPI rendering for OCR |
| `pytesseract` | Tesseract OCR for scanned PDFs |
| `Pillow` | Image preprocessing (greyscale → binarise) |
| `spaCy en_core_web_md` | NER (names, orgs, locations) + POS tagging |
| `dateparser` | Robust date parsing for work history |
| `rapidfuzz` | Fuzzy skill matching (React vs ReactJS) |
| `sentence-transformers` | Semantic embeddings (BAAI/bge-large-en-v1.5) |
| `scikit-learn` | Cosine similarity |
| `pymongo` | MongoDB driver — vector storage and retrieval |
| `numpy` | Vector math |

---

*MIT License — free to use in personal and commercial projects.*