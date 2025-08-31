# Use stable Python (not 3.13, since some libs break)
FROM python:3.11-slim

# Install system dependencies (OCR + PDF tools)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Render sets $PORT automatically
ENV PORT=10000

# Start Flask app with Gunicorn
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-t", "120", "-b", "0.0.0.0:${PORT}", "app:app"]
