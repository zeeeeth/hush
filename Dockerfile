FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Copy runtime data (processed only - raw CSVs are excluded via .dockerignore)
COPY data/processed/ ./data/processed/
COPY models/ ./models/

# Expose the backend API port
EXPOSE 8000
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "--timeout", "120", "--preload", "main:app"]
