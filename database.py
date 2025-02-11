from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")  # Fetch from .env file
DB_NAME = "video_streaming"

# Initialize MongoDB Client
client = AsyncIOMotorClient(MONGO_URI)

#test connection by checking server info
try:
    print("Connecting to MongoDB...")
    client.admin.command('ping')
    print("Connected to MongoDB")
    
except Exception as e:
    print(f"Error connecting to MongoDB: {str(e)}")
database = client[DB_NAME]

# Collections
users_collection = database.get_collection("users")
doctors_collection = database.get_collection("doctors")
videos_collection = database.get_collection("videos")
