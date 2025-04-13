FROM python:3.12

WORKDIR /app

# Install system dependencies for OpenCV and WeasyPrint
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path environment variable
ENV PYTHONPATH=/app

# Install wait-for-it script
RUN apt-get update && apt-get install -y wget
RUN wget -O /usr/local/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh && \
    chmod +x /usr/local/bin/wait-for-it.sh

# Expose port
EXPOSE 8001

# Command to run the application
CMD /usr/local/bin/wait-for-it.sh db:5432 -t 60 -- \
    uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
