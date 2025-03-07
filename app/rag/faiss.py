import faiss
from bson import ObjectId
import time
from sklearn.metrics.pairwise import cosine_similarity

from sentence_transformers import SentenceTransformer
import numpy as np
from app.mongo import mongo_collection

model = SentenceTransformer("all-MiniLM-L6-v2")

def fetchRelevantDocuments(query, k):
    try:
        start = time.time()

        # Fetch All Stored Embeddings from MongoDB
        documents = list(mongo_collection.find({}, {"_id": 1, "text": 1, "embeddings": 1}))
        if not documents:
            return {"error": "No embeddings found in MongoDB."}

        embeddings = np.array([doc["embeddings"] for doc in documents]).astype("float32")
        ids = np.array([str(doc["_id"]) for doc in documents])  # Store MongoDB ObjectIds

        # Create FAISS Index
        dimension = 384  # Embedding dimension for MiniLM
        index = faiss.IndexFlatL2(dimension)  # L2 distance (Euclidean)
        index.add(embeddings)  # Add vectors to FAISS index

        # Ensure query is provided
        if not query:
            return {"error": "Query parameter is required."}

        # Encode Query into an Embedding
        query_embedding = np.array(model.encode(query)).astype("float32").reshape(1, -1)

        # Perform FAISS Search
        _, indices = index.search(query_embedding, k)

        # Retrieve matched document IDs
        matched_ids = [ids[idx] for idx in indices[0]]

        # Retrieve Matched Documents from MongoDB
        matched_docs = list(mongo_collection.find({"_id": {"$in": [ObjectId(id) for id in matched_ids]}}))

        # Compute Cosine Similarity for Re-Ranking
        matched_embeddings = np.array([doc["embeddings"] for doc in matched_docs])
        cosine_similarities = cosine_similarity(query_embedding, matched_embeddings)[0]  # Get similarity scores

        # Attach similarity scores and filter out low-scoring results
        threshold = 0.2  # Remove documents below this similarity score
        filtered_results = []
        for i, doc in enumerate(matched_docs):
            coherence_score = round(float(cosine_similarities[i]), 4)
            if coherence_score >= threshold:
                doc["coherence_score"] = coherence_score
                filtered_results.append(doc)

        # If no results meet the threshold, return empty response
        if not filtered_results:
            return {"query": query, "results": []}

        # Sort results by highest coherence score
        sorted_results = sorted(filtered_results, key=lambda x: x["coherence_score"], reverse=True)

        # Format JSON Response
        results = []
        for doc in sorted_results:
            results.append({
                "id": str(doc["_id"]),
                "text": doc["chunk_text"],  # Ensure field consistency
                "coherence_score": doc["coherence_score"]
            })

        end = time.time()
        print(f"Executed in {end-start}s")

        return {"query": query, "results": results}

    except Exception as e:
        return {"error": str(e)}