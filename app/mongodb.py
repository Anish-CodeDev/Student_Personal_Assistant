import os
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
from typing import Any, Dict, List, Union, Optional

load_dotenv()

class MongoDBHandler:
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        """
        Initialize the MongoDB connection.
        
        :param uri: MongoDB connection string. If None, fetches from MONGODB_URI env var.
        :param db_name: Database name. If None, fetches from DB_NAME env var or uses default from URI.
        """
        self.uri = uri or os.getenv("MONGODB_URI")
        self.db_name = db_name or os.getenv("DB_NAME")
        
        if not self.uri:
            # You might want to log a warning or raise an error here in production
            print("Warning: MONGODB_URI not found in environment variables.")
            
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        """Establishes the connection to MongoDB."""
        try:
            self.client = MongoClient(self.uri)
            if self.db_name:
                self.db = self.client[self.db_name]
            else:
                self.db = self.client.get_database()
            print(f"Connected to MongoDB database: {self.db.name}")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def insert(self, collection_name: str, data: Union[Dict, List[Dict]]) -> Any:
        """
        Inserts one or multiple documents into a collection.
        
        :param collection_name: Name of the collection.
        :param data: A dictionary (single document) or list of dictionaries (multiple documents).
        :return: Inserted ID(s).
        """
        collection = self.db[collection_name]
        if isinstance(data, list):
            result = collection.insert_many(data)
            return result.inserted_ids
        else:
            result = collection.insert_one(data)
            return result.inserted_id

    def read(self, collection_name: str, query: Dict = None, one: bool = False) -> Union[Dict, List[Dict], None]:
        """
        Reads documents from a collection.
        
        :param collection_name: Name of the collection.
        :param query: Dictionary query filter. Defaults to {} (all documents).
        :param one: If True, returns a single document. Else returns a list of documents.
        :return: A document, a list of documents, or None.
        """
        if query is None:
            query = {}
        
        collection = self.db[collection_name]
        
        try:
            if one:
                return collection.find_one(query)
            else:
                return list(collection.find(query))
        except Exception as e:
            print(f"Error reading from {collection_name}: {e}")
            return None

    def delete(self, collection_name: str, query: Dict, multiple: bool = False) -> int:
        """
        Deletes documents from a collection.
        
        :param collection_name: Name of the collection.
        :param query: Filter to select documents to delete.
        :param multiple: If True, deletes all matching documents. Else deletes one.
        :return: Number of documents deleted.
        """
        collection = self.db[collection_name]
        
        try:
            if multiple:
                result = collection.delete_many(query)
            else:
                result = collection.delete_one(query)
            return result.deleted_count
        except Exception as e:
            print(f"Error deleting from {collection_name}: {e}")
            return 0
    def delete_collection(self,collection_name: str):
        """
        Deletes a collection from the database.
        
        :param collection_name: Name of the collection to delete.
        """
        try:
            self.db.drop_collection(collection_name)
            #print(f"Collection {collection_name} deleted successfully.")
        except Exception as e:
            print(f"Error deleting collection {collection_name}: {e}")
    def close(self):
        """Closes the MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")

