# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies for pdf2image (Poppler) and pytesseract (Tesseract)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       poppler-utils \
       tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Default env (can be overridden at runtime)
ENV PRESERVE_FORMATTING=1

EXPOSE 8000

# Use PORT if provided (e.g., Render), else 8000
CMD ["sh", "-c", "gunicorn -w 2 -k gthread -t 120 -b 0.0.0.0:${PORT:-8000} app:app"]

