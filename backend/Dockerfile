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
RUN python scripts/download_models.py \
    && useradd --create-home --uid 1000 --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/uploads /app/results \
    && chmod +x /app/docker-entrypoint.sh \
    && chown -R appuser:appuser /app

USER appuser

# Default port (Render injects PORT=10000; falls back to 8000 locally)
ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/api/v1/health' % os.environ.get('PORT', '8000'))"]

CMD ["/app/docker-entrypoint.sh"]
