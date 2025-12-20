from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
import numpy as np
import time
import os


class VectorDB:
    def __init__(self, host=None, port=None, collection_name=None, dim=128):
        """
        Initialize a Milvus client connection and ensure the collection exists.
        Reads `MILVUS_HOST` and `MILVUS_PORT` from environment when not provided.
        """
        self.collection_name = collection_name or os.getenv('MILVUS_COLLECTION', 'behaviors')
        self.dim = dim or int(os.getenv('EMBED_DIM', 128))
        host = host or os.getenv('MILVUS_HOST', '127.0.0.1')
        port = port or os.getenv('MILVUS_PORT', '19530')
        self.active = False

        try:
            connections.connect(alias='default', host=host, port=str(port))
            self._init_collection()
            self.collection = Collection(self.collection_name)
            self.active = True
        except Exception as e:
            print(f"ALERTA_DB: No se pudo conectar a Milvus ({e}). Modo VOLÁTIL activado.")
            self.collection = None
            self.active = False

    def _init_collection(self):
        if utility.has_collection(self.collection_name):
            return

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="person_id", dtype=DataType.INT64),
            FieldSchema(name="timestamp", dtype=DataType.FLOAT),
            FieldSchema(name="behavior_vector", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
            FieldSchema(name="metadata", dtype=DataType.JSON)
        ]

        schema = CollectionSchema(fields, description="Behavior embeddings and metadata")

        try:
            Collection(name=self.collection_name, schema=schema)
        except Exception as e:
            print(f"ALERTA_DB: error creando colección ({e})")

    def insert_behavior(self, person_id, timestamp, vector, metadata=None):
        if not self.active or self.collection is None:
            return None
        try:
            metadata = metadata or {}
            # pymilvus accepts a list of dicts (one per row)
            row = {
                "person_id": int(person_id),
                "timestamp": float(timestamp),
                "behavior_vector": vector,
                "metadata": metadata
            }
            res = self.collection.insert([row])
            return res
        except Exception as e:
            print(f"ALERTA_DB: insert_behavior error: {e}")
            return None

    def search_behavior(self, query_vector, limit=5):
        if not self.active or self.collection is None:
            return []
        try:
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            results = self.collection.search(
                data=[query_vector],
                anns_field="behavior_vector",
                param=search_params,
                limit=limit,
                output_fields=["person_id", "timestamp", "metadata"]
            )
            # format results
            out = []
            for hits in results:
                for hit in hits:
                    out.append({
                        "id": hit.id,
                        "score": float(hit.score),
                        "person_id": hit.entity.get('person_id'),
                        "timestamp": hit.entity.get('timestamp'),
                        "metadata": hit.entity.get('metadata')
                    })
            return out
        except Exception as e:
            print(f"ALERTA_DB: search_behavior error: {e}")
            return []

    def query(self, expr=None, output_fields=None, limit=50):
        if not self.active or self.collection is None:
            return []
        try:
            return self.collection.query(expr=expr or "", output_fields=output_fields or ["person_id", "timestamp", "metadata"], limit=limit)
        except Exception as e:
            print(f"ALERTA_DB: query error: {e}")
            return []
