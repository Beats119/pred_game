FROM mambaorg/micromamba:1.5.1-bullseye-slim

WORKDIR /app

# Install system dependencies needed for playwright and general execution
USER root
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libcomposite1 \
    libasound2 \
    libxrandr2 \
    libgbm1 \
    libxext6 \
    libxfixes3 \
    libpango-1.0-0 \
    libcairo2 \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install playwright dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install Playwright browsers manually
RUN python3 -m playwright install --with-deps chromium

COPY . .

# Server runs in headless mode (no display available)
ENV HEADLESS=true

# Run as a background worker (polling every 30s)
CMD ["python", "-c", "import asyncio; from app.services.scheduler import poll_task; asyncio.run(poll_task())"]
