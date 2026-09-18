FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend

# System deps for pycairo/manim/moviepy compilation and runtime
RUN apt-get update && apt-get install -y --no-install-recommends build-essential pkg-config libcairo2-dev libpango1.0-dev ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r /app/backend/requirements.txt

COPY backend /app/backend
COPY knowledge-base /app/knowledge-base

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
