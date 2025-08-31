# Social Media Content Analyzer

Turn PDFs and images into clean, actionable social content. Upload files, extract text (with OCR for scans), analyze tone and structure, and get AI‑assisted caption, hashtags, and engagement tips — all in a simple Flask app.

## Features
- Upload multiple PDFs and images (drag & drop)
- Text extraction with layout preservation (pdfplumber/pdfminer)
- OCR for scanned PDFs and images (Tesseract via pytesseract/pdf2image)
- Quick metrics: word/char counts, hashtags, mentions, URLs, top keywords
- Sentiment/tone via VADER
- Optional AI suggestions (caption, hashtags, 10 engagement ideas) via Gemini
- Copy buttons, JSON export, and light/dark theme

## Requirements
- Python 3.10+
- Poppler (for `pdf2image`)
- Tesseract OCR (for `pytesseract`)

Install system tools:
- Windows: Install Poppler and Tesseract and note their install paths
- macOS: `brew install poppler tesseract`
- Linux (Debian/Ubuntu): `sudo apt-get install poppler-utils tesseract-ocr`

## Setup
1. Create a virtual environment and install deps
   - `python -m venv .venv`
   - `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows)
   - `pip install -r requirements.txt`
2. Create `.env` in project root:
   - `SECRET_KEY=devkey` (any random string)
   - Optional: `GEMINI_API_KEY=your_key` (enable AI suggestions)
   - Optional (Windows):
     - `POPPLER_PATH=C:\\Poppler\\poppler-25.07.0\\Library\\bin` (or your path)
     - `TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe`
   - Optional: `PRESERVE_FORMATTING=1` (keep line breaks) or `0`

## Run
- `python app.py`
- Open `http://127.0.0.1:5000`

For production (example):
- `gunicorn -w 2 -k gthread -t 120 -b 0.0.0.0:$PORT app:app`

## Notes
- AI suggestions are only generated if `GEMINI_API_KEY` is present.
- If OCR yields empty text, verify Tesseract is installed and accessible.
- If PDF images fail to render for OCR, ensure Poppler is installed and on PATH (or set `POPPLER_PATH`).

## Project Structure
- `app.py` — Flask app (upload, route, render)
- `utils/extract.py` — PDF/image text extraction + OCR
- `utils/analyze.py` — text metrics + VADER + Gemini wiring
- `utils/gemini_client.py` — Gemini client
- `templates/` — HTML (Bootstrap)
- `static/` — CSS/JS
