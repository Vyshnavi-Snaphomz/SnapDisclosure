
import os
import io
import zipfile
import logging
from time import sleep
import json

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import openai

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found in .env")

openai.api_key = api_key

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


def extract_text_from_pdf(file_bytes):
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    except Exception:
        return ""


def safe_openai_completion(prompt, model="gpt-4o-mini", retries=5):
    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.warning(f"OpenAI error: {e}, retrying in 10 seconds...")
            sleep(10)
    return "Failed to get response from OpenAI after retries."


def summarize_document(text):
    """
    Generates a document title and 3 summary points with details.
    Returns: {"title": str, "points": list of 3 points}
    """
    prompt = f"""
You are a professional document summarizer AI.
Analyze the following text and generate:

1. A concise **document title** (5 words max)
2. Exactly **3 key bullet points**.
   For each point provide:
     - A short **title** (2–5 words)
     - A **summary** (1–2 lines)
     - **Detailed explanation** (3–5 lines)

Respond strictly in this JSON format:
{{
  "title": "string",
  "points": [
    {{
      "title": "string",
      "summary": "string",
      "details": "string"
    }},
    {{
      "title": "string",
      "summary": "string",
      "details": "string"
    }},
    {{
      "title": "string",
      "summary": "string",
      "details": "string"
    }}
  ]
}}

Document text:
{text[:10000]}
"""
    response_text = safe_openai_completion(prompt)

    try:
        data = json.loads(response_text)
        if "title" in data and "points" in data and isinstance(data["points"], list):
            return data
    except Exception:
        logging.warning(f"Failed to parse JSON, response: {response_text}")

    # fallback if JSON parsing fails
    return {
        "title": "Untitled Document",
        "points": [
            {"title": "Point 1", "summary": "Summary may be incomplete.", "details": response_text}
        ],
    }


@app.route("/api/upload", methods=["POST"])
def upload_zip():
    print("UPLOAD ROUTE HIT")
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)
    file_bytes = uploaded_file.read()

    results = []

    def process_file(name, data):
        if name.endswith(".pdf"):
            text = extract_text_from_pdf(data)
        else:
            text = data.decode("utf-8", errors="ignore")

        if not text.strip():
            return {
                "file_name": name,
                "title": "Untitled Document",
                "points": [
                    {"title": "No content", "summary": "No text extracted.", "details": ""}
                ],
            }

        summary_data = summarize_document(text)
        return {
            "file_name": name,
            "title": summary_data.get("title", "Untitled Document"),
            "points": summary_data.get("points", []),
        }

    # Handle ZIP files
    if zipfile.is_zipfile(io.BytesIO(file_bytes)):
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            for name in z.namelist():
                if name.endswith((".pdf", ".txt")):
                    data = z.read(name)
                    results.append(process_file(name, data))
                    sleep(0.5)
    else:
        results.append(process_file(filename, file_bytes))

    return jsonify({"success": True, "files": results}), 200


if __name__ == "__main__":
    # Hugging Face Spaces expect apps to listen on the port set by the PORT env var.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 7860)))
