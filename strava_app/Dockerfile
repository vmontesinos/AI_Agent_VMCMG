FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ ./scripts/

# Set ownership and switch to non-root user
RUN chown -R appuser:appgroup /app
USER appuser

# Expose the webhook server port
EXPOSE 8080

CMD ["python3", "scripts/webhook_server.py"]
