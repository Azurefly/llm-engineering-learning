FROM python:3.12-slim

# Build-time package index. Defaults to PyPI; override it when the build host
# cannot reach PyPI directly (a mirror is required):
#   docker compose build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LLM_LEARNING_DATA_DIR=/data \
    HOST=0.0.0.0 \
    PORT=8765

WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir --index-url "$PIP_INDEX_URL" -r requirements.lock.txt

# Fail the build if the verified dependency set is incomplete, instead of
# starting a container that dies on the first request with ModuleNotFoundError.
RUN python -c "import bleach, fastapi, jinja2, mistune, python_multipart, uvicorn"

COPY app ./app
COPY docs ./docs
COPY ROADMAP.md ROADMAP.en.md ./
COPY run.py ./
RUN mkdir -p /data
EXPOSE 8765
CMD ["python", "run.py"]
