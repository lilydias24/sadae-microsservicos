FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared modules
COPY shared/ /app/shared/

# Copy service files
COPY services/monitoring-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/monitoring-service/ .

# Make start script executable and fix line endings
RUN chmod +x start.sh && \
    sed -i 's/\r$//' start.sh

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

EXPOSE 8002

CMD ["./start.sh"]


