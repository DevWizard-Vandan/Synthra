# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="Synthra" \
      org.opencontainers.image.description="Autonomous quantitative research platform" \
      org.opencontainers.image.version="0.1.0"

# Non-root user required by Hugging Face Spaces
RUN useradd --create-home --shell /bin/bash synthra

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=synthra:synthra synthra/ ./synthra/
COPY --chown=synthra:synthra config/ ./config/

# Create data directory for SQLite
RUN mkdir -p /app/data && chown synthra:synthra /app/data

USER synthra

EXPOSE 7860

CMD ["uvicorn", "synthra.api.app:app", "--host", "0.0.0.0", "--port", "7860", \
     "--workers", "1", "--log-level", "info"]
