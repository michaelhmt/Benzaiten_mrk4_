# coding=utf8
"""
Database operations for MongoDB
"""

import json
from pathlib import Path
from typing import List, Dict, Union, Optional
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, DuplicateKeyError

from logging_config import get_logger

logger = get_logger(__name__)


def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path, 'r') as f:
        return json.load(f)


class Database_Class(object):
    """MongoDB database interface with error handling and logging"""

    def __init__(self, databasename: str):
        """
        Initialize database connection

        Args:
            databasename: Name of the database to use
        """
        self.config = load_config()
        db_config = self.config.get('database', {})

        connection_string = db_config.get('connection_string', 'mongodb://localhost:27017')
        timeout = db_config.get('timeout_ms', 5000)

        try:
            logger.info(f"Connecting to MongoDB: {connection_string}")
            self.client = pymongo.MongoClient(
                connection_string,
                serverSelectionTimeoutMS=timeout
            )
            # Test connection
            self.client.server_info()
            logger.info("MongoDB connection successful")

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ConnectionError(f"Could not connect to MongoDB at {connection_string}") from e

        self.database_name = databasename
        self.database = self.client[self.database_name]
        self.collections = self.database.list_collection_names()
        logger.info(f"Connected to database '{databasename}' with {len(self.collections)} collections")

    def add_to_database(self,
                        itemToAdd: Union[Dict, List[Dict]],
                        targetCollection: str,
                        print_IDs: bool = True) -> bool:
        """
        Add item(s) to database collection

        Args:
            itemToAdd: Single dict or list of dicts to add
            targetCollection: Name of collection to add to
            print_IDs: Whether to print inserted IDs

        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(targetCollection, str):
            logger.error(f"Collection name must be string, got {type(targetCollection)}")
            return False

        database_collection = self.database[targetCollection]
        logger.info(f"Adding item(s) to collection '{targetCollection}'")

        try:
            # Handle list of items
            if isinstance(itemToAdd, list) and len(itemToAdd) > 0:
                if len(itemToAdd) == 1:
                    # Single item in list
                    result = database_collection.insert_one(itemToAdd[0])
                    if print_IDs:
                        logger.info(f"Inserted ID: {result.inserted_id}")
                    logger.info("Successfully added 1 item to database")
                else:
                    # Multiple items
                    result = database_collection.insert_many(itemToAdd)
                    if print_IDs:
                        logger.info(f"Inserted {len(result.inserted_ids)} IDs: {result.inserted_ids}")
                    logger.info(f"Successfully added {len(result.inserted_ids)} items to database")
                return True

            # Handle single dict
            elif isinstance(itemToAdd, dict):
                result = database_collection.insert_one(itemToAdd)
                if print_IDs:
                    logger.info(f"Inserted ID: {result.inserted_id}")
                logger.info("Successfully added 1 item to database")
                return True

            else:
                logger.error(f"Invalid item type: {type(itemToAdd)}")
                return False

        except DuplicateKeyError as e:
            logger.warning(f"Duplicate key error: {e}")
            return False

        except pymongo.errors.PyMongoError as e:
            logger.error(f"Database error: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error adding to database: {e}", exc_info=True)
            return False

    def get_complete_collection(self, collection_name: str) -> List[Dict]:
        """
        Retrieve all documents from a collection

        Args:
            collection_name: Name of collection to retrieve

        Returns:
            List of documents
        """
        try:
            logger.info(f"Retrieving complete collection '{collection_name}'")
            collection = self.database[collection_name]
            documents = list(collection.find({}))
            logger.info(f"Retrieved {len(documents)} documents from '{collection_name}'")
            return documents

        except pymongo.errors.PyMongoError as e:
            logger.error(f"Error retrieving collection '{collection_name}': {e}")
            return []

    def close(self):
        """Close database connection"""
        if self.client:
            logger.info("Closing database connection")
            self.client.close()

    def __del__(self):
        """Destructor - ensure connection is closed"""
        try:
            self.close()
        except:
            pass


# Legacy test code (commented out)
# testpackage = [{'MetaData': {...}, 'Content': {...}}]
# testdb = Database_Class('mlp_fan_fiction_data')
# testdb.add_to_database(testpackage, 'collectedData')
