FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

# SQLite lives on disk; mount a volume here to keep the taxonomy and trend
# history across container restarts.
ENV DATABASE_URL=sqlite+aiosqlite:////data/sentilytics.db
VOLUME ["/data"]

EXPOSE 8000

# Shell form on purpose: hosts assign a port through $PORT, and the exec
# form would pass the literal string instead of expanding it.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
