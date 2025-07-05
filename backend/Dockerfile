# Multi-stage Dockerfile for optimized backend service
FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install wait-for-it script
RUN wget -O /usr/local/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh && \
    chmod +x /usr/local/bin/wait-for-it.sh

# Stage for installing Python dependencies
FROM base AS dependencies

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir \
    --timeout 300 \
    --retries 3 \
    -r requirements.txt

# Final stage
FROM base AS final

WORKDIR /app

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Set Python path environment variable
ENV PYTHONPATH=/app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD /usr/local/bin/wait-for-it.sh db:5432 -t 60 -- \
    python -m app.db.init_db && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload