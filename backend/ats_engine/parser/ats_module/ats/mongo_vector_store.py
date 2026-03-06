from pymongo import MongoClient
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .config import MONGO_URI, DB_NAME, COLLECTION


class VectorDatabase:

    def __init__(self, uri: str = MONGO_URI, db_name: str = DB_NAME, collection: str = COLLECTION):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection]

    def insert_resume(self, filename: str, resume: dict, scores: dict, embedding: list, name: str = None, email: str = None):
        doc = {
            "filename": filename,
            "name": name or resume.get("name"),
            "email": email,
            "fields": resume,
            "scores": scores,
            "embedding": embedding
        }
        self.collection.update_one(
            {"filename": filename},
            {"$set": doc},
            upsert=True
        )

    def fetch_all_resumes(self):
        return list(self.collection.find({}, {"_id": 0}))

    def similarity_search(self, query_embedding: list, top_k: int = 5) -> list[dict]:
        results = []
        for doc in self.collection.find():
            resume_emb = np.array(doc["embedding"]).reshape(1, -1)
            query_emb = np.array(query_embedding).reshape(1, -1)
            score = cosine_similarity(query_emb, resume_emb)[0][0]
            results.append({
                "filename": doc["filename"],
                "score": float(score),
                "resume": doc
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_resume(self, filename: str) -> bool:
        result = self.collection.delete_one({"filename": filename})
        return result.deleted_count > 0

    def get_resume(self, filename: str) -> dict | None:
        return self.collection.find_one({"filename": filename}, {"_id": 0})
