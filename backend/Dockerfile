FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
COPY ../requirements.txt ../requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r ../requirements.txt

# Copy application code
COPY . .

# Copy RAG pipeline and security modules
COPY ../RAG-Pipeline-Ollama /app/RAG-Pipeline-Ollama
COPY ../Health-Security-Metrics /app/Health-Security-Metrics

# Create conversations directory
RUN mkdir -p /app/conversations

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV API_PORT=8000

# Run the application
CMD ["python", "main.py"]
