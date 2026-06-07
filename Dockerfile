FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir \
    fastapi==0.111.0 \
    "uvicorn[standard]==0.29.0" \
    pydantic==2.7.1 \
    "groq==0.9.0" \
    "httpx==0.27.2" \
    requests==2.32.2 \
    python-dotenv==1.0.1

COPY backend/ ./backend/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "7860"]
