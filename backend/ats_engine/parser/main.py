from ats_engine.parser.embedding import EmbeddingScorer
from ats_engine.parser.mparser import parse_resume
from ats_engine.parser.sparser import ResumeParser


def parse(pdf_bytes: bytes, hr_req: dict) -> dict:

    half = parse_resume(pdf_bytes)
    parser = ResumeParser(half).parse()

    scorer = EmbeddingScorer()
    scorer.load_job_description(hr_req)
    data_res = scorer.score(parser)

    return data_res
