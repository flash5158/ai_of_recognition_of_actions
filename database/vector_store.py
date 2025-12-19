from pymilvus import MilvusClient, DataType
import numpy as np

class VectorDB:
    def __init__(self, db_path="panoptes_behaviors.db", collection_name="behaviors"):
        """
        Initialize Milvus Lite client and collection.
        """
        self.client = MilvusClient(db_path)
        self.collection_name = collection_name
        self._init_collection()

    def _init_collection(self):
        """
        Create the collection if it doesn't exist.
        Schema:
        - id: Int64, Primary Key, AutoID
        - person_id: Int64 (Tracking ID)
        - timestamp: Float
        - behavior_vector: FloatVector (dim=128) - Placeholder dimension
        - metadata: JSON (for storing textual descriptions or alerts)
        """
        if self.client.has_collection(self.collection_name):
            return

        schema = MilvusClient.create_schema(auto_id=True, enable_dynamic_field=True)
        schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
        schema.add_field(field_name="person_id", datatype=DataType.INT64)
        schema.add_field(field_name="timestamp", datatype=DataType.FLOAT)
        schema.add_field(field_name="behavior_vector", datatype=DataType.FLOAT_VECTOR, dim=128)

        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="behavior_vector",
            index_type="FLAT", # Simple for small scale/lite
            metric_type="COSINE"
        )

        self.client.create_collection(
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params
        )

    def insert_behavior(self, person_id, timestamp, vector, metadata=None):
        """
        Insert a behavior vector.
        """
        data = {
            "person_id": person_id,
            "timestamp": timestamp,
            "behavior_vector": vector,
            "metadata": metadata or {}
        }
        res = self.client.insert(collection_name=self.collection_name, data=data)
        return res

    def search_behavior(self, query_vector, limit=5):
        """
        Search for similar behaviors.
        """
        res = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            limit=limit,
            output_fields=["person_id", "timestamp", "metadata"]
        )
        return res
