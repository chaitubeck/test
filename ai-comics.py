from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import hashlib

# Load OpenAI API key
with open("gpt-key.txt", "r") as f:
    api_key = f.read().strip()

# Toggle test mode here (or override per request)
DEFAULT_TEST_MODE = True

# Set up Flask
app = Flask(__name__)
CORS(app)
client = OpenAI(api_key=api_key)

# In-memory cache to avoid repeat DALL·E charges
image_cache = {}

def hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()

@app.route('/generate', methods=['POST'])
def generate_response():
    data = request.get_json()
    prompt = data.get("prompt")
    test_mode = data.get("test", DEFAULT_TEST_MODE)

    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400

    try:
        # Step 1: Generate clean academic answer
        answer_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an academic assistant for UPSC civil service aspirants in India. Provide a concise, formal, and accurate textbook-style answer."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        answer_text = answer_resp.choices[0].message.content.strip()

        # Step 2: Generate Pixar-style comic prompt
        comic_prompt_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a visual storyteller. Convert UPSC topics into playful, expressive comic scenes with cartoon characters, dialogue, and emotion. "
                        "Describe a single comic panel in rich, colorful visual detail suitable for an image generator like DALL·E. Use imaginative, whimsical storytelling tone."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        visual_prompt = comic_prompt_resp.choices[0].message.content.strip()

        # Step 3: Check cache or generate image
        visual_hash = hash_prompt(visual_prompt)

        if visual_hash in image_cache:
            image_url = image_cache[visual_hash]
        elif test_mode:
            image_url = "http://localhost:5000/static/test.png"
        else:
            image_response = client.images.generate(
                model="dall-e-3",
                prompt=visual_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            image_url = image_response.data[0].url
            image_cache[visual_hash] = image_url

        # Optional: Log everything to file
        with open("test-log.txt", "a") as log:
            log.write(f"\nPrompt: {prompt}\nAnswer: {answer_text}\nVisual Prompt: {visual_prompt}\nImage: {image_url}\n---\n")

        return jsonify({
            "answer": answer_text,
            "image_url": image_url,
            "image_prompt_used": visual_prompt,
            "test_mode": test_mode
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
