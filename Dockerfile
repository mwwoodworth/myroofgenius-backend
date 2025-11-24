FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install AI and LangGraph dependencies
RUN pip install --no-cache-dir \
    langchain \
    langchain-openai \
    langchain-anthropic \
    langchain-google-genai \
    langgraph \
    pgvector \
    numpy

# Copy all application code (excluding BrainOps.env to use Render env vars)
COPY . .
RUN rm -f BrainOps.env

# Ensure all directories exist
RUN mkdir -p logs memory reports .ai_persistent

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ENV=production

# Expose port
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

# Start command - using the actual main.py in root
# Render uses port 10000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 10000"]
