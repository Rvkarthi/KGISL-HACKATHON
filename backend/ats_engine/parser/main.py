from ats_engine.parser.embedding import EmbeddingScorer
from ats_engine.parser.mparser import parse_resume
from ats_engine.parser.sparser import ResumeParser


def parse(pdf_bytes: bytes, hr_req: dict) -> dict:

    half = parse_resume(pdf_bytes)
    parser = ResumeParser(half).parse()

<<<<<<< HEAD
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
=======
    scorer = EmbeddingScorer()
    scorer.load_job_description(hr_req)
>>>>>>> 48067a2b7111915bedc0cb3f1dd7b41c75581ad7
    data_res = scorer.score(parser)

    return data_res
