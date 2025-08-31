# Social Media Content Analyzer

Turn PDFs and images into clean, actionable social content. Upload files, extract text (with OCR for scans), analyze tone and structure, and get AI-assisted caption, hashtags, and engagement tips — all in a simple Flask app.

Live demo: https://social-media-analyzer-e0fe.onrender.com

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

Install system tools (only if running without Docker):
- Windows: Install Poppler and Tesseract and note their install paths
- macOS: `brew install poppler tesseract`
- Linux (Debian/Ubuntu): `sudo apt-get install poppler-utils tesseract-ocr`

## Run (Docker)
This repo includes a Dockerfile that installs Poppler and Tesseract in the image.

- Build: `docker build -t social-analyzer .`
- Run: `docker run -p 8000:8000 -e SECRET_KEY=devkey social-analyzer`
- Open: `http://localhost:8000`

Environment variables:
- `SECRET_KEY` (required)
- `GEMINI_API_KEY` (optional, enables AI suggestions)
- `PRESERVE_FORMATTING=1` (optional)

## Run (without Docker)
- `python -m venv .venv`
- `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows)
- `pip install -r requirements.txt`
- Add `.env` with: `SECRET_KEY=...`, optional `GEMINI_API_KEY=...`
- Windows optional: `POPPLER_PATH=...`, `TESSERACT_CMD=...`
- Start: `python app.py` → `http://127.0.0.1:5000`

## Deploy on Render
Option A — Docker (recommended):
- Push this repo with `Dockerfile` to GitHub.
- In Render: New → Web Service → Select repo → “Use Docker”.
- Set env vars: `SECRET_KEY`, optional `GEMINI_API_KEY`, optional `PRESERVE_FORMATTING=1`.
- Render builds the image and serves the app (binds to `$PORT` automatically).

Option B — Native Python (no Docker):
- Build command: `apt-get update && apt-get install -y poppler-utils tesseract-ocr && pip install -r requirements.txt`
- Start command: `gunicorn -w 2 -k gthread -t 120 -b 0.0.0.0:$PORT app:app`
- Add env vars in the dashboard as above.

## Notes
- AI suggestions are only generated if `GEMINI_API_KEY` is present.
- If OCR yields empty text, verify Tesseract is installed and accessible.
- If PDF images fail for OCR, ensure Poppler is installed and on PATH (or set `POPPLER_PATH`).

## Project Structure
- `app.py` — Flask app (upload, route, render)
- `utils/extract.py` — PDF/image text extraction + OCR
- `utils/analyze.py` — text metrics + VADER + Gemini wiring
- `utils/gemini_client.py` — Gemini client
- `templates/` — HTML (Bootstrap)
- `static/` — CSS/JS

