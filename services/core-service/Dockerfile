FROM python:3.11-slim

WORKDIR /app

# Copy shared directory from project root (contexto é a raiz do projeto)
COPY shared/ /app/shared/

# Copy core service files
COPY services/core-service/ .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]