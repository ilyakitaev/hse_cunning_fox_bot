FROM python:3.11-slim

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements
COPY requirements.txt .
COPY Pipfile* .

# Install Python dependencies
RUN pip install --no-cache-dir pipenv && \
    pipenv install --system --deploy --ignore-pipfile

# Pre-cache the embedding model
RUN pip install --no-cache-dir numpy scipy scikit-learn httpcore httpx && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "-c", "print('Base image ready')"]
