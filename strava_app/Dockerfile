FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ ./scripts/

# Expose the webhook server port
EXPOSE 8080

# Run the webhook server
CMD ["python3", "scripts/webhook_server.py"]
