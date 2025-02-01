# build_index.py
import os
import numpy as np
import faiss
import pymongo
import time

# Paths to saved files
faiss_index_path = "faiss_index.bin"
faiss_ids_path = "faiss_ids.npy"
last_indexed_timestamp_path = "last_indexed_timestamp.txt"  # File to store the last indexed timestamp

def build_and_save_index(incremental=False):
    print("Building FAISS index..." if not incremental else "Updating FAISS index incrementally...")
    
    client = pymongo.MongoClient("mongodb://biouser:bio123456@localhost:27017/biometrics?authSource=admin")
    db = client["biometrics"]
    collection = db["biometric_data_2"]

    # Initialize FAISS index
    dimension = 128  # Dimension of your vectors
    if not incremental or not os.path.exists(faiss_index_path):
        # Create a new index if not incremental or no existing index
        index = faiss.IndexFlatL2(dimension)
        ids = np.array([], dtype=int)
        last_indexed_timestamp = 0  # Start from the beginning
    else:
        # Load existing index and IDs
        index = faiss.read_index(faiss_index_path)
        ids = np.load(faiss_ids_path)

        # Load the last indexed timestamp
        if os.path.exists(last_indexed_timestamp_path):
            with open(last_indexed_timestamp_path, "r") as f:
                last_indexed_timestamp = int(f.read().strip())
        else:
            last_indexed_timestamp = 0  # If no timestamp file exists, start from the beginning

    # Fetch new or updated records from MongoDB
    if incremental:
        print("Last indexed timestamp:", last_indexed_timestamp)
        query = {"timestamp": {"$gt": last_indexed_timestamp}}  # Fetch records newer than the last indexed timestamp
    else:
        query = {}  # Fetch all records

    # Debug: Print the query
    print("MongoDB Query:", query)

    # Batch processing to load data
    batch_size = 100000  # Adjust based on your memory capacity
    vectors = []
    new_ids = []
    new_timestamps = []

    print("Loading data from MongoDB...")
    cursor = collection.find(query, {"biometric_vector": 1, "id": 1, "timestamp": 1}).batch_size(batch_size)
    for doc in cursor:
        if doc.get("id") is None:  # Check for null IDs
            print("Warning: Found document with null ID:", doc)
            continue  # Skip documents with null IDs

        vectors.append(doc["biometric_vector"])
        new_ids.append(doc["id"])
        new_timestamps.append(doc["timestamp"])

        if len(vectors) == batch_size:
            vectors_np = np.array(vectors).astype("float32")
            index.add(vectors_np)
            vectors = []  # Clear the batch
            print(f"Processed {len(new_ids)} records...")

    # Add any remaining vectors
    if vectors:
        vectors_np = np.array(vectors).astype("float32")
        index.add(vectors_np)

    # Update IDs
    if incremental:
        ids = np.concatenate([ids, np.array(new_ids)])
    else:
        ids = np.array(new_ids)

    print("Updated Id Size :", len(new_ids))
    # Update the last indexed timestamp
    last_indexed_timestamp = round(time.time() * 1000)  # Update to the system current time milliseconds
    with open(last_indexed_timestamp_path, "w") as f:
        f.write(str(last_indexed_timestamp))
    print("Updated last indexed timestamp:", last_indexed_timestamp)

    # Save FAISS index and ID mappings
    print("Saving FAISS index and ID mappings...")
    faiss.write_index(index, faiss_index_path)
    np.save(faiss_ids_path, ids)

    print("Index build complete!" if not incremental else "Index update complete!")
    return index, ids