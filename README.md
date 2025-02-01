
### create virtual env 
```
python3 -m venv <myenvpath>
```
### avtivate virtual env 
```

.\myenvpath\Scripts\activate
```
### Install requirement lib/module 
```
pip install pymongo kafka-python pyspark faiss-cpu flask numpy requests
pip install scikit-learn
pip install fastapi uvicorn pymongo faiss-cpu
```

### Create dummy data (eg; run init-data.py for 3 million of data)
```
python init.data.py
```

### Search exact record(eg; "identical": true)
```
curl -X POST http://localhost:5000/search \
-H "Content-Type: application/json" \
-d '{"identical": true, "biometric_vector": [0.1, 0.2, 0.3, 0.4, 0.5]}'
```
### Search Similarity record(eg; "identical": false)

update k value to limit the size of record.

```
curl -X POST http://localhost:5000/search \
-H "Content-Type: application/json" \
-d '{"identical": false, "biometric_vector": [0.1, 0.2, 0.3, 0.4, 0.5]}'
```



### Reload Index after new record is inserted on mongodb
```
curl -X POST http://localhost:8000/reindex?incremental=true
```

### Reload Index for all data
```
curl -X POST http://localhost:8000/reindex?incremental=false
```
