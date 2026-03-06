from collections import defaultdict
from itertools import combinations


DOMAIN_KEYWORDS = {
    "🌐 Web / Full Stack": ["html", "css", "javascript", "react", "vue", "angular", "node", "django", "flask", "frontend", "backend", "full stack", "typescript", "next", "spring"],
    "🧠 Deep Learning / AI": ["python", "pytorch", "tensorflow", "keras", "cnn", "rnn", "lstm", "transformer", "bert", "gpt", "nlp", "computer vision", "yolo", "llm"],
    "📊 Data Science / Analytics": ["pandas", "numpy", "scikit-learn", "matplotlib", "seaborn", "sql", "tableau", "power bi", "spark", "etl", "regression", "classification"],
    "☁️ Cloud / DevOps": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd", "jenkins", "linux", "devops", "microservices", "ansible"],
    "📱 Mobile Development": ["android", "ios", "flutter", "swift", "kotlin", "react native", "firebase", "jetpack compose", "swiftui"]
}

FRESHER_LABEL = "🎓 Fresher / General"


def classify_resume_skills(parsed: dict) -> dict:
    skills = set(s.lower() for s in parsed.get("skills", []))
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        overlap = len(skills & set(keywords))
        scores[domain] = overlap
    top_domain = max(scores, key=scores.get)
    top_score = scores[top_domain]
    if top_score == 0:
        top_domain = FRESHER_LABEL
    return {
        "primary": top_domain,
        "primary_score": top_score,
        "name": parsed.get("info", {}).get("name", parsed.get("name", "Unknown")),
        "skills": parsed.get("skills", [])
    }


def cluster_resumes(resumes: dict) -> dict:
    """
    resumes: { filename: parsed_resume_dict, ... }
    returns: { domain_label: [member_dict, ...], ... }
    """
    clusters = defaultdict(list)
    for filename, parsed in resumes.items():
        result = classify_resume_skills(parsed)
        clusters[result["primary"]].append(result)
    return dict(clusters)


class TeamFormer:
    def __init__(self, clusters: dict):
        self.clusters = clusters

    def form_team(self, required_skills: list, team_size: int = 3, domain: str = None) -> dict:
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

        return {"team": list(best_team), "success_rate": round(best_score * 100, 2)}

    def _team_score(self, team, required_skills: list) -> float:
        team_skills = set()
        for m in team:
            team_skills.update([s.lower() for s in m.get("skills", [])])
        coverage = len(team_skills & set(s.lower() for s in required_skills)) / max(1, len(required_skills))
        expertise = 0.5
        return 0.6 * coverage + 0.4 * expertise
