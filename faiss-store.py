from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from openai import OpenAI
import faiss
import numpy as np
import pickle
import os

# Load OpenAI API key
with open("gpt-key.txt", "r") as f:
    api_key = f.read().strip()

# Constants
DEFAULT_TEST_MODE = True
SIMILARITY_THRESHOLD = 0.80  # Cosine similarity (1 = exact match)

# Flask setup
app = Flask(__name__)
CORS(app)

# Clients
client = OpenAI(api_key=api_key)
model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

# FAISS setup with cosine similarity
FAISS_FILE = "faiss_index_cosine.idx"
META_FILE = "metadata_cosine.pkl"

if os.path.exists(FAISS_FILE):
    index = faiss.read_index(FAISS_FILE)
    with open(META_FILE, "rb") as f:
        metadata = pickle.load(f)
else:
    index = faiss.IndexFlatIP(384)  # Cosine similarity via dot product
    metadata = {}

# MongoDB setup
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["upsc_ai_comics"]
collection = db["comics_qa"]

@app.route("/add-question", methods=["POST"])
def add_question():
    data = request.get_json()
    question = data.get("question")
    answer = data.get("answer")
    pdf_url = data.get("pdf_url")

    if not question:
        return jsonify({"error": "Missing required field: question"}), 400
    if not pdf_url:
        return jsonify({"error": "Missing required field: pdf_url"}), 400

    # Step 1: Embed and normalize
    embedding = model.encode([question], convert_to_numpy=True)
    faiss.normalize_L2(embedding)

    # Step 2: Check for similar question
    if index.ntotal > 0:
        D, I = index.search(embedding, k=3)
        for dist, idx in zip(D[0], I[0]):
            if dist > SIMILARITY_THRESHOLD:
                matched_q = metadata.get(idx)
                if matched_q:
                    doc = collection.find_one({"question": matched_q})
                    if doc:
                        return jsonify({
                            "message": "✅ Similar question already exists",
                            "matched_question": matched_q,
                            "answer": doc["answer"],
                            "pdf_url": doc.get("pdf_url"),
                            "from_cache": True,
                            "distance": float(dist)
                        })

    # Step 3: Generate answer with GPT if not provided
    if not answer:
        try:
            gpt_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an academic assistant for UPSC civil service aspirants. Provide a clear, formal answer suitable for textbooks."
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            )
            answer = gpt_response.choices[0].message.content.strip()
        except Exception as e:
            return jsonify({"error": f"OpenAI error: {str(e)}"}), 500

    # Step 4: Store in FAISS and MongoDB
    index.add(embedding)
    new_id = len(metadata)
    metadata[new_id] = question

    collection.insert_one({
        "question": question,
        "answer": answer,
        "pdf_url": pdf_url
    })

    faiss.write_index(index, FAISS_FILE)
    with open(META_FILE, "wb") as f:
        pickle.dump(metadata, f)

    return jsonify({
        "message": "✅ New question added",
        "id": new_id,
        "question": question,
        "answer": answer,
        "pdf_url": pdf_url,
        "from_cache": False
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)