import faiss
import pickle
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
import numpy as np

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

# Setup MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["upsc_ai_comics"]
collection = db["comics_qa"]

# Create FAISS index for cosine similarity
dimension = 384  # Dimension of MiniLM
index = faiss.IndexFlatIP(dimension)
metadata = {}

# Fetch all questions from MongoDB
docs = list(collection.find({}, {"question": 1, "_id": 0}))

if not docs:
    print("❌ No questions found in MongoDB.")
    exit()

print(f"📦 Found {len(docs)} documents. Rebuilding index...")

# Prepare embeddings
questions = [doc["question"] for doc in docs]
embeddings = model.encode(questions, convert_to_numpy=True, normalize_embeddings=True)

# Add to index and build metadata
index.add(embeddings)
for i, question in enumerate(questions):
    metadata[i] = question

# Save index and metadata
faiss.write_index(index, "faiss_index.idx")
with open("metadata.pkl", "wb") as f:
    pickle.dump(metadata, f)

print("✅ FAISS index and metadata rebuilt using cosine similarity.")
