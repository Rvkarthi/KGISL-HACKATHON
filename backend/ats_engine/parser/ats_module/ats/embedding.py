"""
Production-ready Resume vs Job Description Embedding Scorer
============================================================
Computes per-field semantic similarity scores between a parsed
resume and a job description using sentence-transformers.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class FieldScore:
    field: str
    score: float  # 0.0 – 1.0
    weight: float = 2.0

    @property
    def score_pct(self) -> str:
        return f"{self.score * 100:.2f}%"

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "score": round(self.score, 6),
            "score_pct": self.score_pct,
            "weight": self.weight,
        }


@dataclass
class ScoringResult:
    field_scores: list[FieldScore] = field(default_factory=list)
    overall_score: float = 0.0
    skipped_fields: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "overall_score": round(self.overall_score, 6),
            "overall_score_pct": f"{self.overall_score * 100:.2f}%",
            "field_scores": [fs.to_dict() for fs in self.field_scores],
            "skipped_fields": self.skipped_fields,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _coerce_to_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item.strip())
            elif isinstance(item, dict):
                parts.extend(str(v) for v in item.values() if v)
        return " ".join(parts).strip() or None
    if isinstance(value, dict):
        return " ".join(str(v) for v in value.values() if v).strip() or None
    return None


def _weighted_average(scores: list[tuple[float, float]]) -> float:
    total_weight = sum(w for _, w in scores)
    if total_weight == 0:
        return 0.0
    return sum(s * w for s, w in scores) / total_weight


# ---------------------------------------------------------------------------
# Main scorer class
# ---------------------------------------------------------------------------
class EmbeddingScorer:
    DEFAULT_WEIGHTS: dict[str, float] = {
        "about": 0.5,
        "skills": 3.0,
        "soft_skills": 2.0,
        "experience": 2.0,
        "education": 1.0,
        "languages": 2.5,
        "certifications": 1.0,
        "projects": 1.5,
    }

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        field_weights: dict[str, float] | None = None,
        batch_size: int = 64,
        device: str | None = None,
    ) -> None:
        self.model = SentenceTransformer(model_name, device=device)
        self.batch_size = batch_size
        self.field_weights: dict[str, float] = {
            **self.DEFAULT_WEIGHTS,
            **(field_weights or {}),
        }
        self._jd_embeddings: dict[str, np.ndarray] = {}

    def load_job_description(self, jd: dict[str, Any]) -> None:
        if not jd:
            raise ValueError("Job description must not be empty.")

        texts = {k: t for k, v in jd.items() if (t := _coerce_to_text(v))}

        if not texts:
            raise ValueError("No usable text found in the job description.")

        encoded = self.model.encode(
            list(texts.values()),
            batch_size=self.batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        self._jd_embeddings = dict(zip(texts.keys(), encoded))

    def get_embedding(self, data: dict[str, Any]) -> list[float]:
        """Convert a dict (resume or JD) to a single embedding vector."""
        texts = []
        for v in data.values():
            t = _coerce_to_text(v)
            if t:
                texts.append(t)
        combined = " ".join(texts)
        return self.model.encode([combined], normalize_embeddings=True)[0].tolist()

    def score(self, resume: dict[str, Any]) -> dict:
        if not self._jd_embeddings:
            raise RuntimeError("Call load_job_description() before score().")
        if not resume:
            raise ValueError("Resume dict must not be empty.")

        t0 = time.perf_counter()

        fields_to_score = {
            key: text
            for key in self._jd_embeddings
            if key in resume and (text := _coerce_to_text(resume[key]))
        }

        skipped = [k for k in self._jd_embeddings if k not in fields_to_score]

        if not fields_to_score:
            return {"overall": "0.00%", "fields": {}, "skipped": skipped}

        resume_vectors = self.model.encode(
            list(fields_to_score.values()),
            batch_size=self.batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        field_results: dict[str, str] = {}
        weighted_pairs: list[tuple[float, float]] = []

        for idx, key in enumerate(fields_to_score):
            raw = float(
                cosine_similarity(
                    resume_vectors[idx].reshape(1, -1),
                    self._jd_embeddings[key].reshape(1, -1),
                )[0][0]
            )
            score = max(0.0, min(1.0, raw))
            weight = self.field_weights.get(key, 1.0)
            field_results[key] = f"{score * 100:.2f}%"
            weighted_pairs.append((score, weight))

        overall = _weighted_average(weighted_pairs)

        return {
            "overall": f"{overall * 100:.2f}%",
            "fields": field_results,
            "skipped": skipped,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
