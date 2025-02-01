
```
pip install pymongo kafka-python pyspark faiss-cpu flask numpy requests
pip install scikit-learn
pip install fastapi uvicorn pymongo faiss-cpu
```

```
curl -X POST http://localhost:5000/search \
-H "Content-Type: application/json" \
-d '{"biometric_vector": [0.1, 0.2, 0.3, 0.4, 0.5]}'
```

```
curl -X POST http://localhost:8000/reindex?incremental=false
```