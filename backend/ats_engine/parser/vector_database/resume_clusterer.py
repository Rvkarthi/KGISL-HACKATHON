# resume_clusterer_no_vectors.py
# -----------------------------
# Cluster resumes + team formation without embeddings
# -----------------------------

from collections import defaultdict
from itertools import combinations
import numpy as np

# -----------------------------
# Domain keywords
# -----------------------------
DOMAIN_KEYWORDS = {
    "🌐 Web / Full Stack": ["html", "css", "javascript", "react", "vue", "angular", "node", "django", "flask", "frontend", "backend", "full stack", "typescript", "next", "spring"],
    "🧠 Deep Learning / AI": ["python", "pytorch", "tensorflow", "keras", "cnn", "rnn", "lstm", "transformer", "bert", "gpt", "nlp", "computer vision", "yolo", "llm"],
    "📊 Data Science / Analytics": ["pandas", "numpy", "scikit-learn", "matplotlib", "seaborn", "sql", "tableau", "power bi", "spark", "etl", "regression", "classification"],
    "☁️ Cloud / DevOps": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd", "jenkins", "linux", "devops", "microservices", "ansible"],
    "📱 Mobile Development": ["android", "ios", "flutter", "swift", "kotlin", "react native", "firebase", "jetpack compose", "swiftui"]
}

FRESHER_LABEL = "🎓 Fresher / General"

# -----------------------------
# Resume clustering based on skills
# -----------------------------
def classify_resume_skills(parsed):
    skills = set(s.lower() for s in parsed.get("skills", []))
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        overlap = len(skills & set(keywords))
        scores[domain] = overlap
    top_domain = max(scores, key=scores.get)
    top_score = scores[top_domain]
    if top_score == 0:
        top_domain = FRESHER_LABEL
    return {"primary": top_domain, "primary_score": top_score, "name": parsed.get("info", {}).get("name", "Unknown"), "skills": parsed.get("skills", [])}

def cluster_resumes(resumes):
    clusters = defaultdict(list)
    for filename, parsed in resumes.items():
        result = classify_resume_skills(parsed)
        clusters[result["primary"]].append(result)
    return clusters

# -----------------------------
# Team formation
# -----------------------------
class TeamFormer:
    def __init__(self, clusters):
        self.clusters = clusters

    def form_team(self, required_skills, team_size=3, domain=None):
        candidates = []
        if domain:
            candidates = self.clusters.get(domain, [])
        else:
            for resumes in self.clusters.values():
                candidates.extend(resumes)

        if len(candidates) < team_size:
            return {"team": [], "success_rate": 0.0}

        best_team = None
        best_score = -1
        for team in combinations(candidates, team_size):
            score = self._team_score(team, required_skills)
            if score > best_score:
                best_score = score
                best_team = team

        return {"team": best_team, "success_rate": round(best_score * 100, 2)}

    def _team_score(self, team, required_skills):
        team_skills = set()
        for m in team:
            team_skills.update([s.lower() for s in m.get("skills", [])])
        coverage = len(team_skills & set([s.lower() for s in required_skills])) / max(1, len(required_skills))
        expertise = 0.5  # default minimal expertise for all
        return 0.6*coverage + 0.4*expertise

# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    # Example resumes (replace with your MongoDB fetch)
    resumes = {
        "resume1.pdf": {"info": {"name": "Alice"}, "skills": ["html", "css", "react"]},
        "resume2.pdf": {"info": {"name": "Bob"}, "skills": ["python", "pytorch", "tensorflow"]},
        "resume3.pdf": {"info": {"name": "Charlie"}, "skills": ["react", "figma", "css"]},
        "resume4.pdf": {"info": {"name": "Diana"}, "skills": ["aws", "docker", "kubernetes"]},
        "resume5.pdf": {"info": {"name": "Ethan"}, "skills": ["android", "ios", "flutter"]},
        "resume6.pdf": {"info": {"name": "Fiona"}, "skills": ["html", "css", "js", "react", "figma"]},
    }

    clusters = cluster_resumes(resumes)
    print("\n📂 Clusters:")
    for domain, members in clusters.items():
        print(f"{domain} ({len(members)} resumes): {[m['name'] for m in members]}")

    # Form team for Web / Full Stack
    required_skills = ["html", "css", "react", "figma"]
    team_maker = TeamFormer(clusters)
    team_result = team_maker.form_team(required_skills, team_size=3, domain="🌐 Web / Full Stack")

    print(f"\nSuggested Team (Success Rate: {team_result['success_rate']}%)")
    for member in team_result["team"]:
        print(f" • {member['name']} - Skills: {', '.join(member['skills'])}")