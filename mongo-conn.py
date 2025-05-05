from pymongo import MongoClient
from datetime import datetime

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Select the database and collection
db = client["upsc_ai_comics"]
collection = db["comics_qa"]

# Define a sample document
comic_doc = {
    "question": "What is LPG reform in India?",
    "answer": "LPG stands for Liberalization, Privatization, and Globalization, key parts of India's 1991 economic reforms.",
    "tags": ["lpg", "economic reforms", "1991", "india"],
    "image_url": "https://yourcdn.com/images/lpg_comic.png",
    "created_at": datetime.utcnow()
}

# Insert the document
result = collection.insert_one(comic_doc)

# Confirm insertion
print(f"Inserted document with ID: {result.inserted_id}")
