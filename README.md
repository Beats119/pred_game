# BDG WIN Pattern Monitor

A robust, production-ready Python web application that automatically scrapes game results from BDG WIN and sends configurable real-time Telegram notifications when sequences (like Triple B or Alternating) are detected.

## Architecture
- **Backend**: FastAPI 
- **Scraper**: Playwright Python (Async)
- **Cache**: Redis
- **Scheduler**: asyncio background tasks

## Setup

1. Copy `.env.example` to `.env` and fill in your details:
   - Telegram Bot Token
   - Telegram Chat ID
   - BDG WIN Credentials (username/password)

2. Make sure you have Docker and Docker Compose installed.

## Deployment

Deploying with Docker Compose is the easiest way to launch both the application and the Redis database.

```bash
docker-compose up --build -d
```

### Logs
To view logs:
```bash
docker-compose logs -f app
```

### Stopping
```bash
docker-compose down
```

## Running Locally (Without Docker)

1. Install Python 3.10+
2. Install dependencies: `pip install -r requirements.txt`
3. Install Playwright browsers: `python -m playwright install chromium`
4. Start a local Redis server on port 6379
5. Run the server: `uvicorn app.main:app --reload`

## Tests
```bash
pytest tests/
```
