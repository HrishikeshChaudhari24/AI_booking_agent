FROM python:3.11-slim

# Install build deps for psycopg2 and google libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Expose port (Render/Heroku/Cloud Run will set PORT env)
ENV PORT=8080

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-8080} app:app"]
