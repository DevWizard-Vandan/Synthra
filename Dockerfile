# ── Python build stage ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Frontend build stage ──────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend-build

# Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="Synthra" \
      org.opencontainers.image.description="Autonomous quantitative research platform" \
      org.opencontainers.image.version="0.1.0"

# Non-root user required by Hugging Face Spaces
RUN useradd --create-home --shell /bin/bash synthra

WORKDIR /app

# Copy installed Python packages
COPY --from=builder /install /usr/local

# Copy frontend static build files
COPY --from=frontend-builder --chown=synthra:synthra /frontend-build/out ./frontend/out

# Copy application source
COPY --chown=synthra:synthra synthra/ ./synthra/
COPY --chown=synthra:synthra config/ ./config/

# Create data directory for SQLite
RUN mkdir -p /app/data && chown synthra:synthra /app/data

USER synthra

EXPOSE 7860

CMD ["uvicorn", "synthra.api.app:app", "--host", "0.0.0.0", "--port", "7860", \
     "--workers", "1", "--log-level", "info"]
