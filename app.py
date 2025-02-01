from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
import faiss
import os
from build_index import build_and_save_index, faiss_index_path, faiss_ids_path
import pymongo

# Initialize FastAPI app
app = FastAPI()

# FAISS index parameters
dimension = 128  # Dimension of your vectors
nlist = 100  # Number of clusters (adjust based on your dataset)

# Load FAISS index and ID mappings (or build if not exists)
if not os.path.exists(faiss_index_path) or not os.path.exists(faiss_ids_path):
    print("FAISS index not found. Building index...")
    index, ids = build_and_save_index(incremental=False)
else:
    print("Loading FAISS index and ID mappings...")
    index = faiss.read_index(faiss_index_path)
    ids = np.load(faiss_ids_path)

# If the index is not an IVF index, convert it
if not isinstance(index, faiss.IndexIVFFlat):
    print("Converting index to IndexIVFFlat for faster search...")
    quantizer = faiss.IndexFlatL2(dimension)
    ivf_index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
    ivf_index.train(index.reconstruct_n(0, index.ntotal))  # Train on existing data
    ivf_index.add(index.reconstruct_n(0, index.ntotal))    # Add existing data
    index = ivf_index
    faiss.write_index(index, faiss_index_path)  # Save the new index

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://biouser:bio123456@localhost:27017/biometrics?authSource=admin")
db = client["biometrics"]
collection = db["biometric_data_2"]


# Ensure the `id` field is indexed
collection.create_index("id")

# Request model for API input
class SearchRequest(BaseModel):
    identical: bool
    biometric_vector: List[float]
    
# Search endpoint
@app.post("/search")
async def search(request: SearchRequest):
    try:
        # Convert input vector to numpy array
        query_vector = np.array([request.biometric_vector]).astype("float32")

        # Set the number of clusters to search (nprobe)
        if isinstance(index, faiss.IndexIVFFlat):
            index.nprobe = 10  # Adjust this value for speed/accuracy trade-off

        # Search FAISS for nearest neighbors
        # k = 5  # Number of results to return
        k = 5
        distances, indices = index.search(query_vector, k)
        
        user_data = []
        
        # Debug: Print indices and distances
        print("Indices:", indices)
        print("Distances:", distances)
        if request.identical:
            # identical=true => To search exact record(Similarity 100%) on db, distance value must be zero
            if distances[0][0] == 0:
                user_id = int(ids[indices[0][0]])
                user = collection.find_one({"id": user_id}, {"id": 1, "metadata": 1, "email": 1, "phone": 1})
                if user:
                    # if user found on db
                    user_data.append(user)
                    print("Identical User IDs:", user_id)  # Debug: Print user ID
                else:
                    # if user not found on db
                     user_data.append({"id": None, "metadata": None, "email": None, "phone": None})
            else:
                # if distance value is not zero
                 user_data.append({"id": None, "metadata": None, "email": None, "phone": None})
        else:
            # identical=false => To search other 5 similar record on db, k=5 limit record
            user_ids = [int(ids[idx]) for idx in indices[0]]
            print("User IDs:", user_ids)  # Debug: Print user IDs

            if not user_ids:
                return {"results": []}  # Return empty results if no user IDs are found

            user_data = list(collection.find({"id": {"$in": user_ids}}, {"id": 1, "metadata": 1, "email": 1, "phone": 1}))
            print("Similar User IDs", user_ids)  # Debug: Print user data

        # Map results to their IDs
        results = []
        for data in user_data:
            results.append({
                "id": data.get("id"),  # Use .get() to safely access keys
                "metadata": data.get("metadata", {}),  # Default to empty dict if missing
                "email": data.get("email", ""),  # Default to empty string if missing
                "phone": data.get("phone", "")  # Default to empty string if missing
            })

        return {"results": results}

    except Exception as e:
        print("Error:", str(e))  # Debug: Print the error
        raise HTTPException(status_code=500, detail=str(e))

# Reindex endpoint
@app.post("/reindex")
async def reindex(incremental: bool = True):
    global index, ids
    index, ids = build_and_save_index(incremental=incremental)
    return {"message": "Incremental reindexing complete!" if incremental else "Full reindexing complete!"}

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)