from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from openai import OpenAI
import faiss
import numpy as np
import pickle
import os

# Setup
with open("gpt-key.txt") as f:
    api_key = f.read().strip()

client = OpenAI(api_key=api_key)

app = Flask(__name__)
CORS(app)

model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
FAISS_FILE = "faiss_index.idx"
META_FILE = "metadata.pkl"

# Load FAISS index and metadata
if os.path.exists(FAISS_FILE):
    index = faiss.read_index(FAISS_FILE)
    with open(META_FILE, "rb") as f:
        metadata = pickle.load(f)
else:
    index = faiss.IndexFlatL2(384)
    metadata = {}

# MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["upsc_ai_comics"]
collection = db["comics_qa"]

@app.route("/semantic-search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query")
    test_mode = data.get("test", True)

    if not query:
        return jsonify({"error": "Missing query"}), 400

    try:
        query_embedding = model.encode([query], convert_to_numpy=True)
        D, I = index.search(np.array(query_embedding), k=1)

        best_match_idx = I[0][0]
        distance = D[0][0]
        THRESHOLD = 1.2  # Tune based on results

        if distance > THRESHOLD or best_match_idx not in metadata:
            # Fallback to GPT
            gpt_resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You're an academic assistant for UPSC aspirants. Answer questions clearly and formally."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            )
            gpt_answer = gpt_resp.choices[0].message.content.strip()
            return jsonify({
                "answer": gpt_answer,
                "matched_question": None,
                "pdf_url": None,
                "source": "gpt",
                "distance": float(distance)
            })

        # Return match from MongoDB
        matched_q = metadata[best_match_idx]
        doc = collection.find_one({"question": matched_q})
        if not doc:
            return jsonify({"error": "Match found in FAISS but not in MongoDB."}), 404

        return jsonify({
            "answer": doc.get("answer"),
            "matched_question": doc.get("question"),
            "pdf_url": doc.get("pdf_url"),
            "source": "semantic",
            "distance": float(distance)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5002)
