"""
ats_system  v4
──────────────
ATS Resume Screening System with MongoDB vector storage.

Modules:
    parser         — PDF extraction, spaCy NER, embedding generation
    matcher        — Section-by-section ATS scoring with rapidfuzz
    clusterer      — Zero-shot domain clustering
    ats_vector_db  — MongoDB storage, semantic search, domain queries
    requirements   — HR requirement config presets

Quick start:
    from ats_system.parser       import ResumeParser
    from ats_system.matcher      import ResumeMatcher
    from ats_system.clusterer    import ResumeClusterer
    from ats_system.ats_vector_db import store_resumes_vector, search_section

    parser    = ResumeParser()
    matcher   = ResumeMatcher(parser.model)
    clusterer = ResumeClusterer(parser.model)

    resume_db = parser.process_many(["cv1.pdf", "cv2.pdf"])
    clusters  = clusterer.cluster(resume_db)

    store_resumes_vector(resume_db, clusters)

    matcher.set_requirements(HR_REQUIREMENTS)
    results = matcher.match_all(resume_db)
"""

from .parser       import ResumeParser
from .matcher      import ResumeMatcher
from .clusterer    import ResumeClusterer
from .ats_vector_db import (
    store_resumes_vector,
    query_resumes_vector,
    search_section,
    list_resumes,
    delete_resume,
    count_resumes,
    get_resume,
)

__all__ = [
    "ResumeParser", "ResumeMatcher", "ResumeClusterer",
    "store_resumes_vector", "query_resumes_vector",
    "search_section", "list_resumes", "delete_resume",
    "count_resumes", "get_resume",
]
__version__ = "4.0.0"