# demo_multiple_resumes.py
from embedding import EmbeddingScorer  # embedding.py
from mongo_vector_store import VectorDatabase
import numpy as np

# ----------------------------
# Initialize
# ----------------------------
scorer = EmbeddingScorer()
db = VectorDatabase()

# ----------------------------
# Sample Job Description
# ----------------------------
job_description = {
    "skills": ["html", "css", "js", "react", "figma"],
    "soft_skills": ["teamwork", "effective communication", "leadership"],
    "about": "Looking for a frontend developer with design skills in Figma and Photoshop"
}

scorer.load_job_description(job_description)

# Convert JD values to a single string for embedding
jd_texts = []
for v in job_description.values():
    if isinstance(v, list):
        jd_texts.append(" ".join(v))
    else:
        jd_texts.append(str(v))

jd_embedding = scorer.model.encode(
    [" ".join(jd_texts)],
    normalize_embeddings=True
)[0]

# ----------------------------
# Multiple Resume Data
# ----------------------------
resumes_data = [
    {
        "name": "Alice Johnson",
        "skills": ["html", "css", "js", "react", "figma"],
        "soft_skills": ["teamwork", "leadership", "creativity"],
        "about": "Frontend developer with UI/UX skills"
    },
    {
        "name": "Bob Smith",
        "skills": ["python", "pytorch", "tensorflow", "keras"],
        "soft_skills": ["problem solving", "communication"],
        "about": "AI/ML engineer focusing on deep learning projects"
    },
    {
        "name": "Charlie Lee",
        "skills": ["sql", "pandas", "numpy", "scikit-learn"],
        "soft_skills": ["analytics", "teamwork"],
        "about": "Data analyst with experience in data visualization"
    },
    {
        "name": "Diana Cruz",
        "skills": ["aws", "docker", "kubernetes", "terraform"],
        "soft_skills": ["collaboration", "critical thinking"],
        "about": "Cloud engineer and DevOps specialist"
    },
    {
        "name": "Ethan Brown",
        "skills": ["android", "kotlin", "flutter", "swift"],
        "soft_skills": ["creativity", "teamwork"],
        "about": "Mobile developer building cross-platform apps"
    },
    {
        "name": "Fiona Green",
        "skills": ["html", "css", "js", "vue", "tailwind"],
        "soft_skills": ["leadership", "teamwork"],
        "about": "Frontend developer focused on responsive web apps"
    }
]

# ----------------------------
# Insert resumes into DB
# ----------------------------
for idx, resume_data in enumerate(resumes_data, start=1):
    # Compute per-field scores
    scores = scorer.score(resume_data)

    # Convert resume fields to a single string for embedding
    resume_texts = []
    for v in resume_data.values():
        if isinstance(v, list):
            resume_texts.append(" ".join(v))
        else:
            resume_texts.append(str(v))

    resume_embedding = scorer.model.encode(
        [" ".join(resume_texts)],
        normalize_embeddings=True
    )[0]

    filename = f"{resume_data['name']} - Resume.pdf"
    db.insert_resume(filename, resume_data, scores, resume_embedding.tolist())
    print(f"✅ Resume '{filename}' stored in database")

# ----------------------------
# Fetch all resumes
# ----------------------------
print("\n📂 All resumes in database")
for r in db.fetch_all_resumes():
    fields = r.get("fields", {})
    scores_data = r.get("scores", {})
    print(f"📄 {fields.get('name', 'Unknown')}")
    print("   Skills:", fields.get("skills", []))
    print("   Soft Skills:", fields.get("soft_skills", []))
    print("   About:", fields.get("about", ""))
    print("   Scores:", scores_data.get("fields", {}))
    print()

# ----------------------------
# Similarity Search
# ----------------------------
print("🔎 Searching best resumes for job...")
results = db.similarity_search(jd_embedding.tolist(), top_k=5)
for res in results:
    print(f"{res['filename']} - Score: {res['score']*100:.2f}%")