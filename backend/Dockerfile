# Backend Dockerfile for FastAPI application
FROM python:3.12.9-slim

# Install system dependencies for document processing
# Including LibreOffice for high-quality PPTX to PDF conversion
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libgl1-mesa-glx \
    libglib2.0-0 \
    # LibreOffice for PPTX to PDF conversion
    libreoffice-writer \
    libreoffice-impress \
    libreoffice-common \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy minimal requirements for Docker
COPY requirements-docker.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure startup script is executable
RUN chmod +x /app/start.sh

# Create necessary directories
RUN mkdir -p data/cache data/output data/temp data/logging

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os, urllib.request; port=os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/api/health')"

# Run the application - use shell form to ensure script is executable at runtime
# This handles volume mounts which may override the chmod done during build
CMD ["/bin/bash", "-c", "chmod +x /app/start.sh && /app/start.sh"]
