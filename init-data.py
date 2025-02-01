import random
import numpy as np
import pymongo
# from kafka import KafkaProducer
import json
from bson import ObjectId
from datetime import datetime, timedelta
import time

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://biouser:bio123456@localhost:27017/biometrics?authSource=admin")
db = client["biometrics"]
collection = db["biometric_data_2"]

# Kafka Producer
# producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'))

# Generate dummy biometric data
def generate_dummy_biometric_data(num_samples=10, vector_dim=128):
    lastId = 3001
    for i in range(num_samples):
        # Simulate a biometric vector
        biometric_vector = np.random.rand(vector_dim).tolist()
        data = {
            "_id": ObjectId(),  # Generate a new ObjectId
            "id": i + lastId,
            "biometric_vector": biometric_vector,
            "metadata": {"name": f"user_{i + lastId}", "age": np.random.randint(18, 60)},
            "email": f"user_{i + lastId}@example.com",  # Add email
            "phone": f"123-456-{np.random.randint(1000, 9999)}",  # Add phone
            "timestamp": round(time.time() * 1000)
        }

        # Insert into MongoDB
        collection.insert_one(data)

        # Convert ObjectId to string for JSON serialization
        data["_id"] = str(data["_id"])

        # Publish to Kafka
        # producer.send('biometric_topic', value=data)

    # producer.flush()

generate_dummy_biometric_data()