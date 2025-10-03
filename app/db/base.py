from pymongo import MongoClient
import os
from pymongo.errors import ConnectionFailure

# Initialize the MongoDB client and database variables
client = None
db = None

def connect_to_database():
    global client, db
    try:
        # Initialize the client using the MongoDB URI, including the database name
        client = MongoClient(os.getenv("MONGODB_URI"))
        # Access the specific database (replace 'talent-scan' with your database name)
        db = client['talent-scan']
        print(f"Database: {db}")
        
        # List collections in the database
        collections = db.list_collection_names()
        print(f"Collections: {collections}")
        
        # Check the connection by sending a ping command
        client.admin.command('ping')
        print("Database connected successfully.")
    except ConnectionFailure as e:
        print(f"Failed to connect to the database: {e}")
        client = None
        db = None

def get_collection(collection_name: str):
    """Get a specific collection from the database."""
    if db is None:  # Explicitly check if db is None
        print("Database is not connected.")
        return None
    return db[collection_name]

def close_connection():
    """Close the MongoDB client connection."""
    global client
    if client:
        client.close()
        print("Database connection closed.")
    else:
        print("No active database connection to close.")
