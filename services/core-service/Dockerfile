FROM python:3.11-slim

WORKDIR /app

# Copy shared directory
COPY shared/ /app/shared/

# Copy core service
COPY services/core-service/ /app/

# Install dependencies
RUN pip install fastapi uvicorn sqlalchemy psycopg2-binary httpx python-multipart

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]