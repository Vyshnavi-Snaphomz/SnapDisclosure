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
    """Extract text from a PDF (handles multi-page files)."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    except Exception:
        return ""


def safe_openai_completion(prompt, model="gpt-4o-mini", retries=5):
    """Retry-safe OpenAI completion with backoff."""
    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.warning(f"OpenAI error: {e}, retrying in 10 seconds...")
            sleep(10)
    return "Failed to get response from OpenAI after retries."


def summarize_document(text):
    """
    Summarizes a document and marks potential red flags.
    Returns JSON with is_red_flag keys.
    """
    prompt = f"""
You are an expert AI in real estate, finance, and legal risk assessment.

Analyze the following document carefully and identify general findings and potential red flags.

Return JSON only in this format:
{{
  "title": "Brief document title (<=5 words)",
  "points": [
    {{
      "title": "Short key point title (3-6 words)",
      "summary": "1-2 line summary of the main observation.",
      "details": "3-6 lines elaborating on the finding — include why it matters, implications, and context.",
      "is_red_flag": true or false
    }},
    ...
  ]
}}

Guidelines:
- Set "is_red_flag": true for critical issues, risks, defects, legal or financial concerns.
- Focus on clarity and accuracy.
- Return 4–6 points max.
- Do not include markdown — only valid JSON.

Document text:
{text[:9000]}
"""
    response_text = safe_openai_completion(prompt)

    try:
        # Remove code blocks if model outputs them
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()

        data = json.loads(response_text)
        if "title" in data and isinstance(data.get("points"), list):
            # Ensure every point has is_red_flag
            for p in data["points"]:
                if "is_red_flag" not in p:
                    p["is_red_flag"] = False
            return data
    except Exception as e:
        logging.warning(f"Failed to parse JSON: {e}. Raw response: {response_text}")

    # fallback
    return {
        "title": "Untitled Document",
        "points": [
            {
                "title": "Parsing Error",
                "summary": "Could not parse structured response.",
                "details": response_text,
                "is_red_flag": False,
            }
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
        """Process PDF or text file."""
        if name.endswith(".pdf"):
            text = extract_text_from_pdf(data)
        else:
            text = data.decode("utf-8", errors="ignore")

        if not text.strip():
            return {
                "file_name": name,
                "title": "Untitled Document",
                "points": [
                    {
                        "title": "No content",
                        "summary": "No text extracted.",
                        "details": "",
                        "is_red_flag": False,
                    }
                ],
            }

        summary_data = summarize_document(text)
        return {
            "file_name": name,
            "title": summary_data.get("title", "Untitled Document"),
            "points": summary_data.get("points", []),
        }

    # Handle ZIP archives
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
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 7860)))
