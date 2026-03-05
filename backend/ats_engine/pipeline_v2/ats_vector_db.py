"""
ats_vector_db.py  (v2 — Unified Schema)
-----------------------------------------
MongoDB vector storage for ATS resumes.

Stores and retrieves parsed resumes in the unified schema from parser.py v4.
Top-level field used for candidate name: parsed["info"]["name"]
"""

import numpy as np
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
from sentence_transformers import SentenceTransformer
from typing import Optional

MONGO_URI = "mongodb+srv://nullvoidxexe_db_user:GYNYpPhOxy8hj1HM@cluster0.qxgjvmp.mongodb.net/?appName=Cluster0"
DB_NAME   = "ats_db"
COL_NAME  = "resumes"

_client     = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client     = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _client.server_info()
        db          = _client[DB_NAME]
        _collection = db[COL_NAME]
        _collection.create_index("filename", unique=True)
        _collection.create_index("primary_domain")
    return _collection


def _to_list(vec):
    return vec.tolist()


def _to_array(vec_list):
    return np.array(vec_list, dtype=np.float32)


def _cosine(a, b):
    return float(np.dot(a, b))


def _get_primary_domain(filename: str, clusters: dict) -> str:
    for domain, members in clusters.items():
        for member in members:
            if member.get("filename") == filename:
                return domain
    return "Unknown"


# ─────────────────────────────────────────────────────────────────────────────
# STORE
# ─────────────────────────────────────────────────────────────────────────────

def store_resumes_vector(resume_db: dict, clusters: dict) -> int:
    col = _get_collection()
    ops = []

    for filename, data in resume_db.items():
        parsed = data["parsed"]
        emb    = data.get("embeddings", {})

        primary_domain = _get_primary_domain(filename, clusters)
        primary_score  = 0.0
        for domain, members in clusters.items():
            for m in members:
                if m.get("filename") == filename:
                    primary_score = m.get("primary_score", 0.0)
                    break

        # candidate_name pulled from unified schema
        candidate_name = parsed.get("info", {}).get("name", "Unknown")

        doc = {
            "filename":       filename,
            "candidate_name": candidate_name,
            "primary_domain": primary_domain,
            "primary_score":  primary_score,
            "parsed":         parsed,
            "embeddings":     {k: _to_list(v) for k, v in emb.items()},
        }
        ops.append(UpdateOne({"filename": filename}, {"$set": doc}, upsert=True))

    if not ops:
        print("⚠️  No documents to store.")
        return 0

    try:
        result = col.bulk_write(ops, ordered=False)
        total  = result.upserted_count + result.modified_count
        print(f"💾  Stored/updated {total} resume(s) ({result.upserted_count} new, {result.modified_count} updated).")
        return total
    except BulkWriteError as e:
        print(f"⚠️  Bulk write error: {e.details}")
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# QUERY
# ─────────────────────────────────────────────────────────────────────────────

def query_resumes_vector(domain: str = "all", top_n: int = 10, model=None, query: str = "") -> list:
    col          = _get_collection()
    mongo_filter = {}
    if domain and domain.lower() != "all":
        mongo_filter["primary_domain"] = domain

    docs = list(col.find(mongo_filter))
    if not docs:
        print(f"⚠️  No resumes found for domain='{domain}'.")
        return []

    if query and model:
        query_vec = model.encode(query, normalize_embeddings=True)
        scored = []
        for doc in docs:
            full_emb = doc["embeddings"].get("full")
            score = _cosine(query_vec, _to_array(full_emb)) if full_emb else doc.get("primary_score", 0.0) / 100.0
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        docs = [d for _, d in scored]
    else:
        docs.sort(key=lambda x: x.get("primary_score", 0.0), reverse=True)

    return docs[:top_n]


# ─────────────────────────────────────────────────────────────────────────────
# SECTION SEARCH
# ─────────────────────────────────────────────────────────────────────────────

def search_section(section: str, query: str, top_n: int = 5, model=None) -> list:
    if model is None:
        raise ValueError("SentenceTransformer model is required.")

    col       = _get_collection()
    query_vec = model.encode(query, normalize_embeddings=True)
    docs      = list(col.find({}))
    if not docs:
        print("⚠️  No resumes in the database.")
        return []

    scored = []
    for doc in docs:
        # Try stored embedding first
        stored_emb = doc["embeddings"].get(section)
        if stored_emb is not None:
            score = _cosine(query_vec, _to_array(stored_emb))
            scored.append((score, doc))
            continue

        # Fall back to raw_sections text
        raw_sections = doc["parsed"].get("_meta", {}).get("raw_sections", {})
        section_text = raw_sections.get(section, "")

        if not section_text:
            # Try top-level parsed fields (unified schema)
            field = doc["parsed"].get(section, "")
            if isinstance(field, list):
                # list of dicts (experience / projects / education)
                section_text = " ".join(
                    " ".join(str(v) for v in (item.values() if isinstance(item, dict) else [item]))
                    for item in field
                )
            elif isinstance(field, str):
                section_text = field

        if not section_text:
            continue

        section_vec = model.encode(section_text[:2000], normalize_embeddings=True)
        score = _cosine(query_vec, section_vec)
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:top_n]]


# ─────────────────────────────────────────────────────────────────────────────
# CRUD HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def delete_resume(filename: str) -> bool:
    col    = _get_collection()
    result = col.delete_one({"filename": filename})
    if result.deleted_count:
        print(f"🗑️  Deleted '{filename}' from MongoDB.")
        return True
    print(f"⚠️  '{filename}' not found in MongoDB.")
    return False


def list_resumes() -> list:
    col  = _get_collection()
    docs = col.find({}, {"filename": 1, "candidate_name": 1, "primary_domain": 1, "_id": 0})
    return list(docs)


def count_resumes() -> int:
    return _get_collection().count_documents({})


def get_resume(filename: str):
    return _get_collection().find_one({"filename": filename}, {"_id": 0})