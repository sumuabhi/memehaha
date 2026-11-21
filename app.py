import json
import os
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

api_key = os.environ.get("GEMINI_API_KEY", "").strip().strip('"').strip("'")
client = genai.Client(api_key=api_key)

GALI_WORDS = {
    "fuck", "fucking", "shit", "bitch", "asshole", "bastard", "dick",
    "bhosdike", "bhosrike", "madarchod", "behenchod", "bhenchod",
    "chutiya", "gandu", "harami", "kamina", "kamine", "saala", "sala", "bc", "mc"
}

def contains_gali(text: str) -> bool:
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    return bool(words & GALI_WORDS)

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"clip": "stupid", "answer": "You didn't even type anything."})

    has_gali = contains_gali(question)

    system_prompt = """
    You are a deadpan, razor-sharp AI assistant. Classify the user's message silently and craft a matching response.
    Return ONLY valid JSON with two keys:
    1. "clip": MUST be one of "gali", "stupid", or "normal":
       - "gali": if the user swore, used Hindi/English gali, or insulted you.
       - "stupid": if the question is painfully obvious, absurd, lazy, nonsensical, or silly.
       - "normal": if it is a genuine, thoughtful, or real question.
    2. "answer": string matching the vibe of the clip:
       - If "gali": give a cold, unbothered, savage comeback, then briefly address whatever they asked (if anything).
       - If "stupid": give a deadpan, dry, witty roast of the question before giving the obvious answer.
       - If "normal": give a genuinely helpful, clear, slightly dry Philomena Cunk-style matter-of-fact answer.
    Keep answers punchy (2-4 sentences max). Never mention the words "gali", "stupid", "normal", or "clip" in the answer.
    """

    for model_name in ["gemini-3.8-flash-lite", "gemini-3.8-flash"]:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=f"{system_prompt}\n\nUser message: {question}",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            ai_data = json.loads(response.text)
            clip = ai_data.get("clip", "normal")
            if has_gali:
                clip = "gali"
            if clip not in ("gali", "stupid", "normal"):
                clip = "normal"

            return jsonify({
                "clip": clip,
                "answer": ai_data.get("answer", "I refuse to dignify that with a response.")
            })
        except Exception:
            continue

    # Instant fallback if Google's servers are temporarily overloaded
    if has_gali:
        return jsonify({"clip": "gali", "answer": "Watch your mouth. Even Google's servers took a break rather than deal with that."})
    return jsonify({"clip": "stupid", "answer": "My brain is temporarily overloaded by that question. Ask again in 10 seconds."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

