FROM python:3.12

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path environment variable
ENV PYTHONPATH=/app

# Install wait-for-it script and other dependencies
RUN apt-get update && apt-get install -y wget
RUN wget -O /usr/local/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh && \
    chmod +x /usr/local/bin/wait-for-it.sh

# Expose port
EXPOSE 8000

# Command to run the application
CMD /usr/local/bin/wait-for-it.sh db:5432 -t 60 -- \
    python -m app.db.init_db && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload