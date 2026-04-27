# Multi-stage build for the Sentinel API
# Stage 1: build wheels in a fatter image
FROM python:3.11-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

    # Build wheels with extended timeouts and retry — large packages like xgboost
    # can stall on a slow connection. 300s timeout + 5 retries handles most flakes.
RUN pip wheel \
        --no-cache-dir \
        --wheel-dir /wheels \
        --timeout 300 \
        --retries 5 \
        -r requirements.txt

# Stage 2: slim runtime
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Non-root user
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# Install deps from prebuilt wheels
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels

# App code + model artifacts
COPY src/ ./src/
COPY models/ ./models/

RUN chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
