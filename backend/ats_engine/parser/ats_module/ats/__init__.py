"""
ATS Module
==========
Applicant Tracking System utilities for resume scoring, vector storage, and clustering.

Quick start:
    from ats import ATS

    ats = ATS()
    ats.load_job_description({ "skills": ["react", "css"], "about": "Frontend dev" })

    scores      = ats.score_resume(resume_dict)
    embedding   = ats.get_embedding(resume_dict)
    clusters    = ats.cluster(resumes_dict)
    team        = ats.form_team(["react", "css"], team_size=3)

    ats.db.insert_resume(filename, resume_dict, scores, embedding)
    results     = ats.db.similarity_search(embedding, top_k=5)
    all_resumes = ats.db.fetch_all_resumes()
"""

from .embedding import EmbeddingScorer, FieldScore, ScoringResult
from .mongo_vector_store import VectorDatabase
from .resume_clusterer import cluster_resumes, classify_resume_skills, TeamFormer
from .config import MONGO_URI, DB_NAME, COLLECTION, EMBED_MODEL, VECTOR_DIM, FIELDS


class ATS:
    """
    Single entry point for the full ATS pipeline.

    Usage:
        from ats import ATS
        ats = ATS()
    """

    def __init__(
        self,
        model_name: str = EMBED_MODEL,
        mongo_uri: str = MONGO_URI,
        db_name: str = DB_NAME,
        collection: str = COLLECTION,
    ):
        self.scorer = EmbeddingScorer(model_name=model_name)
        self.db = VectorDatabase(uri=mongo_uri, db_name=db_name, collection=collection)
        self._clusters: dict = {}

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    def load_job_description(self, jd: dict) -> None:
        """Load a job description to score resumes against."""
        self.scorer.load_job_description(jd)

    def score_resume(self, resume: dict) -> dict:
        """
        Score a resume against the loaded job description.
        Returns: { "overall": "82.50%", "fields": { "skills": "90.00%", ... }, ... }
        """
        return self.scorer.score(resume)

    def get_embedding(self, data: dict) -> list[float]:
        """Convert a resume or JD dict into a vector embedding."""
        return self.scorer.get_embedding(data)

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------
    def save_resume(self, filename: str, resume: dict, scores: dict, embedding: list, name: str = None, email: str = None) -> None:
        """Insert or update a resume in MongoDB."""
        self.db.insert_resume(filename, resume, scores, embedding, name=name, email=email)

    def search(self, jd: dict, top_k: int = 5) -> list[dict]:
        """
        One-shot: embed a JD and return the top_k most similar resumes from DB.
        Returns: [{ "filename": ..., "score": float, "resume": {...} }, ...]
        """
        embedding = self.get_embedding(jd)
        return self.db.similarity_search(embedding, top_k=top_k)

    # ------------------------------------------------------------------
    # Clustering & Team Formation
    # ------------------------------------------------------------------
    def cluster(self, resumes: dict) -> dict:
        """
        Cluster resumes by domain.
        resumes: { filename: parsed_resume_dict, ... }
        Returns: { domain_label: [member, ...], ... }
        """
        self._clusters = cluster_resumes(resumes)
        return self._clusters

    def form_team(self, required_skills: list, team_size: int = 3, domain: str = None) -> dict:
        """
        Form the best team from clustered resumes.
        Call cluster() first, or pass clusters manually via TeamFormer.
        Returns: { "team": [...], "success_rate": float }
        """
        if not self._clusters:
            raise RuntimeError("Call cluster() before form_team().")
        former = TeamFormer(self._clusters)
        return former.form_team(required_skills, team_size=team_size, domain=domain)


__all__ = [
    "ATS",
    "EmbeddingScorer",
    "VectorDatabase",
    "cluster_resumes",
    "classify_resume_skills",
    "TeamFormer",
    "FieldScore",
    "ScoringResult",
    "MONGO_URI",
    "DB_NAME",
    "COLLECTION",
    "EMBED_MODEL",
    "VECTOR_DIM",
    "FIELDS",
]
