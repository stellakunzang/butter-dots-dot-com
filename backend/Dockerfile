FROM python:3.11-slim

# poppler-utils: required by pdf2image for PDF → image conversion
# libgomp1: required by onnxruntime
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Download BDRC OCR models at build time
# Models are saved to /app/OCRModels/ and /app/Models/Lines|Layout/
RUN python scripts/download_models.py

# Default port (Render injects PORT=10000; falls back to 8000 locally)
ENV PORT=8000
EXPOSE ${PORT}

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
