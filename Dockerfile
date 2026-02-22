FROM python:3.11-slim-bullseye

WORKDIR /app

# Install minimal system deps needed before playwright installs chromium deps
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright + all Chromium system dependencies automatically
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Server runs headless (no display on cloud)
ENV HEADLESS=true

# Run as a background worker (polls every 30s)
CMD ["python", "-c", "import asyncio; from app.services.scheduler import poll_task; asyncio.run(poll_task())"]
