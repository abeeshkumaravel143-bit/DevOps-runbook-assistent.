# ══════════════════════════════════════════════════════════════════
#  OpsRunbook RAG — Dockerfile
#  Stage 1: Build React frontend
#  Stage 2: Run FastAPI backend + serve built frontend
# ══════════════════════════════════════════════════════════════════

# ── Stage 1: Frontend Build ────────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --frozen-lockfile 2>/dev/null || npm install

COPY frontend/ .
RUN npm run build

# ── Stage 2: Backend + Serve ───────────────────────────────────────
FROM python:3.11-slim

# System deps for psycopg2, faiss, tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libgomp1 \
    tesseract-ocr poppler-utils \
    curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY main.py database.py auth.py audit.py rag.py ./
COPY runbooks.txt ./

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Copy .env.example (user should mount their own .env)
COPY .env.example .env.example

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
