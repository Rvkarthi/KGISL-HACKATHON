from ats_engine.parser.embedding import EmbeddingScorer
from ats_engine.parser.mparser import parse_resume
from ats_engine.parser.sparser import ResumeParser


def parse(pdf_bytes: bytes) -> dict:

    half = parse_resume(pdf_bytes)
    parser = ResumeParser(half).parse()

    scorer = EmbeddingScorer(device="cpu")
    scorer.load_job_description(
        {
            "about": "should be in ML and expertise",
            "skills": ["python", "rust", "tensorflow", "pytorch", "pandas"],
            "soft_skills": [
                "teamwork",
                "good communication",
                "team leader",
            ],
            "language": ["english"],
        }
    )
    data_res = scorer.score(parser)

    return data_res
