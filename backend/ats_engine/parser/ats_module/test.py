# test_ats.py
# run: python test_ats.py

from ats import ATS, EmbeddingScorer, VectorDatabase, cluster_resumes, TeamFormer

JD = {
    "skills": ["html", "css", "js", "react", "figma"],
    "soft_skills": ["teamwork", "leadership"],
    "about": "Looking for a frontend developer"
}

RESUMES = {
    "alice.pdf": { "name": "Alice", "email": "alice@gmail.com", "skills": ["html", "css", "react", "figma"], "soft_skills": ["teamwork"], "about": "Frontend dev" },
    "bob.pdf":   { "name": "Bob",   "email": "bob@gmail.com",   "skills": ["python", "pytorch", "tensorflow"], "soft_skills": ["problem solving"], "about": "ML engineer" },
    "diana.pdf": { "name": "Diana", "email": "diana@gmail.com", "skills": ["aws", "docker", "kubernetes"],     "soft_skills": ["collaboration"],    "about": "DevOps engineer" },
}

def test(label, fn):
    try:
        result = fn()
        print(f"✅ {label}: {result}")
    except Exception as e:
        print(f"❌ {label}: {e}")


ats = ATS()
ats.load_job_description(JD)

test("score_resume",    lambda: ats.score_resume(RESUMES["alice.pdf"])["overall"])
test("get_embedding",   lambda: f"{len(ats.get_embedding(RESUMES['alice.pdf']))} dims")
test("save_resume",     lambda: [f"saved {r['name']} ({r['email']})" for f, r in RESUMES.items() if not ats.save_resume(f, r, ats.score_resume(r), ats.get_embedding(r), name=r["name"], email=r["email"])])
test("search",          lambda: [(r["filename"], f"{r['score']*100:.1f}%") for r in ats.search(JD, top_k=10)])
test("cluster",         lambda: {k: [m["name"] for m in v] for k, v in ats.cluster(RESUMES).items()})
test("form_team",       lambda: {"members": [m["name"] for m in ats.form_team(["html", "css", "react"], team_size=2)["team"]], "success_rate": f"{ats.form_team(['html','css','react'], team_size=2)['success_rate']}%"})
test("VectorDatabase",  lambda: f"{len(VectorDatabase().fetch_all_resumes())} resumes in DB")
test("EmbeddingScorer", lambda: EmbeddingScorer().get_embedding(RESUMES["alice.pdf"])[:3])
test("cluster_resumes", lambda: list(cluster_resumes(RESUMES).keys()))
test("TeamFormer",      lambda: {"members": [m["name"] for m in TeamFormer(cluster_resumes(RESUMES)).form_team(["html", "react"], team_size=2)["team"]], "success_rate": f"{TeamFormer(cluster_resumes(RESUMES)).form_team(['html','react'], team_size=2)['success_rate']}%"})