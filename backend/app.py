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
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://snap-disclosure.vercel.app",
            "http://localhost:5173"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})


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
    app.run(debug=True, port=7860)





# import os
# import re
# import io
# import zipfile
# import tempfile
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from werkzeug.utils import secure_filename
# from PyPDF2 import PdfReader
# import google.generativeai as genai
# from time import sleep
# from dotenv import load_dotenv

# # Load Gemini API key
# load_dotenv(".env")
# api_key = os.getenv("GEMINI_API_KEY")
# if not api_key:
#     raise RuntimeError("GEMINI_API_KEY not found in .env")
# genai.configure(api_key=api_key)

# app = Flask(__name__)

# # Allow your frontend origins
# ALLOWED_ORIGINS = [
#     "http://localhost:5173",
#     "http://127.0.0.1:5173",
#     "http://localhost:3000",
#     "http://localhost:8080",
#     "http://127.0.0.1:8080",
#     "http://localhost:8082",
#     "http://127.0.0.1:8082",
# ]

# CORS(
#     app,
#     resources={r"/*": {"origins": ALLOWED_ORIGINS}},
#     supports_credentials=True,
#     allow_headers=["*"],
#     expose_headers=["Content-Disposition"],
# )

# # ----------------------------
# # Helper functions
# # ----------------------------

# def summarize_text(text, max_points=3, max_full_chars=6000):
#     """Short preview bullet points from text."""
#     if not text:
#         return [], ""
#     normalized = re.sub(r'\s+', ' ', text).strip()
#     if not normalized:
#         return [], ""
#     candidates = re.split(r'(?<=[.!?])\s+', normalized)
#     summary_points = []
#     for candidate in candidates:
#         cleaned = candidate.strip()
#         if cleaned:
#             summary_points.append(cleaned[:240].rstrip())
#             if len(summary_points) >= max_points:
#                 break
#     full_summary = normalized[:max_full_chars].strip()
#     return summary_points, full_summary

# def generate_gemini_summary(file_bytes, file_name):
#     """Generate concise bullet-point summary using Gemini AI."""
#     ext = file_name.rsplit('.', 1)[-1].lower()
#     pages = []

#     if ext == 'pdf':
#         reader = PdfReader(io.BytesIO(file_bytes))
#         pages = [page.extract_text() or "" for page in reader.pages]
#     else:
#         pages = [file_bytes.decode('utf-8', errors='ignore')]

#     total_pages = len(pages)
#     chunk_size = 10
#     chunks = [pages[i:i + chunk_size] for i in range(0, total_pages, chunk_size)]
#     bullet_summaries = []

#     model = genai.GenerativeModel("gemini-2.5-flash")
#     config = {"temperature": 0.0, "top_p": 1, "top_k": 1}

#     for idx, chunk in enumerate(chunks, start=1):
#         text = "\n\n".join([f"--- Page {i+1} ---\n{p}" for i, p in enumerate(chunk)])
#         prompt = f"""
#  You are a professional document summarizer AI.
# Analyze the following text ({len(chunk)} pages) and create a concise set of 3–5 bullet points 
# highlighting the most important information. Make it clear, short, and easy to read.#

# Text:
# {text}
# """
#         try:
#             response = model.generate_content(prompt, generation_config=config)
#             bullets = [line.strip("-*• \n") for line in response.text.splitlines() if line.strip()]
#             bullet_summaries.extend(bullets[:5])
#             sleep(1)  # rate-limit safety
#         except Exception as e:
#             bullet_summaries.append(f"[Error processing chunk {idx}: {e}]")
#             continue

#     return bullet_summaries

# # ----------------------------
# # Routes
# # ----------------------------

# @app.route('/api/upload', methods=['POST'])
# def api_upload():
#     """Upload ZIP or single file and return preview + Gemini full summary."""
#     if 'file' not in request.files:
#         return jsonify({'success': False, 'error': 'No file provided'}), 400

#     uploaded_file = request.files['file']
#     if uploaded_file.filename == '':
#         return jsonify({'success': False, 'error': 'No file selected'}), 400

#     filename = secure_filename(uploaded_file.filename)
#     uploaded_bytes = uploaded_file.read()
#     files_data = []

#     # ZIP handling
#     if zipfile.is_zipfile(io.BytesIO(uploaded_bytes)):
#         with zipfile.ZipFile(io.BytesIO(uploaded_bytes)) as z:
#             for name in z.namelist():
#                 if name.endswith(('.pdf', '.txt', '.md', '.csv', '.json')):
#                     file_bytes = z.read(name)

#                     # Short preview
#                     if not name.endswith('.pdf'):
#                         text_content = file_bytes.decode('utf-8', errors='ignore')
#                         preview_points, _ = summarize_text(text_content)
#                     else:
#                         pdf_reader = PdfReader(io.BytesIO(file_bytes))
#                         text_content = "\n".join([p.extract_text() or "" for p in pdf_reader.pages])
#                         preview_points, _ = summarize_text(text_content)

#                     # Full Gemini summary
#                     full_summary = generate_gemini_summary(file_bytes, name)

#                     files_data.append({
#                         'name': os.path.basename(name),
#                         'path': name,
#                         'previewSummary': preview_points,
#                         'fullSummary': full_summary
#                     })
#     else:
#         # Single file
#         file_bytes = uploaded_bytes
#         if not filename.endswith('.pdf'):
#             text_content = file_bytes.decode('utf-8', errors='ignore')
#             preview_points, _ = summarize_text(text_content)
#         else:
#             pdf_reader = PdfReader(io.BytesIO(file_bytes))
#             text_content = "\n".join([p.extract_text() or "" for p in pdf_reader.pages])
#             preview_points, _ = summarize_text(text_content)

#         full_summary = generate_gemini_summary(file_bytes, filename)
#         files_data.append({
#             'name': filename,
#             'path': filename,
#             'previewSummary': preview_points,
#             'fullSummary': full_summary
#         })

#     return jsonify({'success': True, 'files': files_data}), 200

# if __name__ == '__main__':
#     app.run(debug=True, use_reloader=False)
