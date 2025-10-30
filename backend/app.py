import os
import io
import zipfile
import logging
from time import sleep

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


def safe_openai_completion(prompt, model="gpt-4o-mini", retries=3):
    """
    Calls OpenAI ChatCompletion safely with retries on rate limits or API errors.
    Returns the generated text.
    """
    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                # max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.warning(f"OpenAI error: {e}, retrying in 10 seconds...")
            sleep(10)
    return "Failed to get response from OpenAI after retries."


def generate_preview_summary(text_chunk):
    """
    Generates a very short preview 2-3 sentences and a one-line title.
    """
    prompt = f"""
You are a professional document summarizer AI.
Analyze the following text and create a **very concise, clear, short, easy-to-read preview**.
Limit the output to **exactly 2-3 sentences** only.
Generate a **one-line title** as well.
Do NOT add extra details beyond the most important points.

Respond strictly in this format:

Title: <one-line title>
Preview: <2-3 sentences>

Text:
{text_chunk}
"""

    response_text = safe_openai_completion(prompt)

    title = "Untitled Document"
    preview = "Preview not available."

    for line in response_text.splitlines():
        if line.lower().startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif line.lower().startswith("preview:"):
            preview = line.split(":", 1)[1].strip()

    # print("preview: \n", preview)
    
    return {"title": title, "summary": preview}


def summarize_detailed_with_openai(text):
    prompt = f"""
You are a helpful assistant that summarizes property documents.
Summarize the following document text into 3 short, concise paragraphs.
- Each paragraph should focus on key highlights like ownership, sales, taxes, mortgage, property features, and utilities.
- Use plain text, no numbering or bullet points.
- Keep it factual and easy to read.

Document text:
{text[:10000]}
"""
    response_text = safe_openai_completion(prompt)
    # Split into paragraphs by double newline
    paragraphs = [p.strip() for p in response_text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = ["No summary generated."]
    return paragraphs[:3]


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

        preview_data = generate_preview_summary(text)
        detailed = summarize_detailed_with_openai(text)

        # print("preview_data:", preview_data)

        return {
            "file_name": name,
            "title": preview_data.get("title", "Untitled Document"),
            "summary": preview_data.get("summary", ""),
            "fullSummary": detailed
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
    app.run(host="0.0.0.0", port=7860)

