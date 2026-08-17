FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LLM_LEARNING_DATA_DIR=/data \
    HOST=0.0.0.0 \
    PORT=8765

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY docs ./docs
COPY ROADMAP.md ROADMAP.en.md ./
COPY run.py ./
RUN mkdir -p /data
EXPOSE 8765
CMD ["python", "run.py"]
