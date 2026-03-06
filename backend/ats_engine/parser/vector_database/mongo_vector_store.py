from pymongo import MongoClient
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class VectorDatabase:

    def __init__(self):
        uri = "mongodb+srv://nullvoidxexe_db_user:GYNYpPhOxy8hj1HM@cluster0.qxgjvmp.mongodb.net/?appName=Cluster0"
        self.client = MongoClient(uri)
        self.db = self.client["ats_db"]
        self.collection = self.db["resumes"]

    # ---------------------------------
    # insert resume (single, consistent)
    # ---------------------------------
    def insert_resume(self, filename: str, resume: dict, scores: dict, embedding: list):
        doc = {
            "filename": filename,    # store filename at top level
            "fields": resume,        # all resume fields: skills, soft_skills, about, etc
            "scores": scores,        # per-field scores
            "embedding": embedding   # vector
        }
        self.collection.update_one(
            {"filename": filename},
            {"$set": doc},
            upsert=True
        )

    # ---------------------------------
    # fetch all resumes
    # ---------------------------------
    def fetch_all_resumes(self):
        print(list(self.collection.find({}, {"_id": 0})))
        return list(self.collection.find({}, {"_id": 0}))

    # ---------------------------------
    # vector similarity search
    # ---------------------------------
    def similarity_search(self, query_embedding, top_k=5):
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