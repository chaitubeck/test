from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from openai import OpenAI
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
import os

# Load OpenAI API key
with open("gpt-key.txt", "r") as f:
    api_key = f.read().strip()

DEFAULT_TEST_MODE = True
SIMILARITY_THRESHOLD = 0.8  # Cosine similarity threshold

# Flask setup
app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=api_key)
embedder = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

# FAISS (Cosine similarity, so must use IndexFlatIP)
faiss_index = faiss.read_index("faiss_index.idx")

with open("metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

# MongoDB setup
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["upsc_ai_comics"]
collection = db["comics_qa"]

@app.route('/generate', methods=['POST'])
def generate_response():
    data = request.get_json()
    prompt = data.get("prompt")
    test_mode = data.get("test", DEFAULT_TEST_MODE)

    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400

    try:
        # Step 0: UPSC topic relevance check
        relevance_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're a classifier. Only respond with 'Yes' or 'No'. "
                        "Is the following question related to the UPSC syllabus (e.g., Indian polity, economy, governance, geography, history, etc.)?"
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )
        relevance = relevance_resp.choices[0].message.content.strip().lower()

        if "no" in relevance:
            return jsonify({
                "answer": "Sorry, I can only help with UPSC-related topics!",
                "pdf_url": None,
                "matched_question": None,
                "test_mode": test_mode
            })

        # Step 1: Encode & Normalize embedding
        query_embedding = embedder.encode([prompt], convert_to_numpy=True, normalize_embeddings=True)
        D, I = faiss_index.search(query_embedding, k=1)
        similarity_score = float(D[0][0])

        matched_question = None
        doc = None

        if similarity_score >= SIMILARITY_THRESHOLD:
            matched_question = metadata.get(I[0][0])
            doc = collection.find_one({"question": matched_question}) if matched_question else None

        # Step 2: Return from DB if found
        if doc and "answer" in doc:
            answer_text = doc["answer"]
            pdf_url = doc.get("pdf_url", "http://localhost:5000/static/test.pdf" if test_mode else None)
        else:
            # Step 3: Fallback to GPT
            gpt_resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an academic assistant for UPSC civil service aspirants in India. "
                            "Provide a concise, formal, and accurate textbook-style answer."
                        )
                    },
                    {"role": "user", "content": prompt}
                ]
            )
            answer_text = gpt_resp.choices[0].message.content.strip()
            pdf_url = doc.get("pdf_url") if doc else "http://localhost:5000/static/test.pdf" if test_mode else None

        # Log
        with open("test-log.txt", "a") as log:
            log.write(f"\nPrompt: {prompt}\nAnswer: {answer_text}\nMatched Q: {matched_question}\nPDF: {pdf_url}\nScore: {similarity_score:.4f}\n---\n")

        return jsonify({
            "answer": answer_text,
            "pdf_url": pdf_url,
            "matched_question": matched_question,
            "similarity_score": similarity_score,
            "test_mode": test_mode
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/explain5-stream', methods=['POST'])
def explain_like_5_stream():
    data = request.get_json()
    prompt = data.get("prompt")

    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400

    try:
        def generate():
            completion = client.chat.completions.create(
                model="gpt-4o",
                stream=True,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a friendly teacher explaining UPSC topics to a 5-year-old using fun analogies and simple words. "
                            "Only answer if the question is related to UPSC syllabus (e.g., Indian polity, economy, history, geography, environment, governance, etc.). "
                            "If the question is not related to UPSC, politely say: 'Sorry, I can only help with UPSC-related topics!'"
                        )
                    },
                    {"role": "user", "content": prompt}
                ]
            )

            for chunk in completion:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content"):
                    yield f"data: {delta.content}\n\n"

        return Response(generate(), mimetype="text/event-stream")

    except Exception as e:
        import traceback
        print("❌ Exception occurred in explain5-stream:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    app.run(debug=True)
