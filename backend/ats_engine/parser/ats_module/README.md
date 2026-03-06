# ATS Module

## Install dependencies
```
pip install -r requirements.txt
```

## Usage (Backend)

```python
from ats import ATS

ats = ATS()

# 1. Load Job Description
jd = {
    "skills": ["html", "css", "js", "react", "figma"],
    "soft_skills": ["teamwork", "leadership"],
    "about": "Looking for a frontend developer"
}
ats.load_job_description(jd)

# 2. Score a resume
resume = {
    "name": "Alice",
    "skills": ["html", "css", "react", "figma"],
    "soft_skills": ["teamwork"],
    "about": "Frontend developer with UI/UX skills"
}
scores = ats.score_resume(resume)
# → { "overall": "91.23%", "fields": { "skills": "95.00%", ... } }

# 3. Get embedding + save to DB
embedding = ats.get_embedding(resume)
ats.save_resume("alice_resume.pdf", resume, scores, embedding)

# 4. Search top matching resumes for a JD
results = ats.search(jd, top_k=5)
# → [{ "filename": "alice_resume.pdf", "score": 0.91, "resume": {...} }, ...]

# 5. Cluster resumes by domain
resumes = {
    "alice.pdf": resume,
    "bob.pdf": { "name": "Bob", "skills": ["python", "pytorch"] }
}
clusters = ats.cluster(resumes)
# → { "🌐 Web / Full Stack": [...], "🧠 Deep Learning / AI": [...] }

# 6. Form a team
team = ats.form_team(["html", "css", "react"], team_size=2)
# → { "team": [...], "success_rate": 80.0 }
```

## Or use individual classes
```python
from ats import EmbeddingScorer, VectorDatabase, TeamFormer, cluster_resumes
```
