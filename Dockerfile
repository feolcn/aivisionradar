FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data

ENV DATABASE_URL=sqlite:///./data/aivisionradar.db
ENV ENABLE_SCHEDULER=true

EXPOSE 8000

CMD ["sh", "-c", "python -m app.cli init-db && python -m app.cli seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
