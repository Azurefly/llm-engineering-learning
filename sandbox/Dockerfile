FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir pytest==8.4.1 \
    && useradd --create-home --uid 10001 sandbox

USER sandbox
WORKDIR /workspace

ENTRYPOINT ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]
