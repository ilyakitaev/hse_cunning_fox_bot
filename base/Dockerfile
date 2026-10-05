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

RUN pip install --no-cache-dir -r requirements.txt


# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "-c", "print('Base image ready')"]
