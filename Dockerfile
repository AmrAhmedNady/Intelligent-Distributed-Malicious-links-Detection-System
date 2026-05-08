# SpectraGuard — Backend Dockerfile
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV REDIS_URL=redis://redis:6379/0

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure data and models directories exist
RUN mkdir -p data ml/models

# Train the model during build so it's ready to go
RUN python train_model.py

# Expose port (default for uvicorn)
EXPOSE 8000

# Default command (will be overridden by docker-compose)
CMD ["python", "-m", "uvicorn", "coordinator.api:app", "--host", "0.0.0.0", "--port", "8000"]
