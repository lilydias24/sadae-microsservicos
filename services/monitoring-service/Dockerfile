FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy shared modules
COPY shared/ /app/shared/

# Copy service files
COPY services/monitoring-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/monitoring-service/ .

# Make start script executable
RUN chmod +x start.sh

EXPOSE 8002

CMD ["./start.sh"]


