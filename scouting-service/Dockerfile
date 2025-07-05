# Multi-stage Dockerfile for optimized scouting service with CPU-only packages
FROM python:3.12-slim AS base

# Install essential system dependencies only
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install wait-for-it script
RUN wget -O /usr/local/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh && \
    chmod +x /usr/local/bin/wait-for-it.sh

# Stage for installing Python dependencies
FROM base AS dependencies

WORKDIR /app

# Copy requirements file (using minimal version for faster builds)
COPY requirements-minimal.txt .

# Install dependencies with optimized settings
RUN pip install --no-cache-dir \
    --timeout 300 \
    --retries 3 \
    -r requirements-minimal.txt

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

# Set environment variables for CPU-only execution
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Command to run the application
CMD /usr/local/bin/wait-for-it.sh db:5432 -t 60 -- \
    uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
