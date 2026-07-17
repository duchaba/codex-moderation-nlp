# Moderation NLP Server

Small server-side JSON API for OpenAI text moderation. There is no UI.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your OpenAI API key in the environment:

```bash
export OPENAI_API_KEY="your-api-key"
```

## Run Locally

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

## API

Health check:

```bash
curl http://localhost:8000/health
```

Moderate one message:

```bash
curl -X POST http://localhost:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{"message":"text to check","safer":0.0005}'
```

Response fields include the OpenAI category scores plus:

- `is_safer_flagged`: `true` when the highest category score is greater than or equal to `safer`
- `is_flagged`: OpenAI moderation flagged value
- `max_key`: category with the highest score
- `max_value`: highest category score
- `sum_value`: sum of all category scores
- `safer_value`: threshold used
- `message`: original input text

## Deploy

Use the same command behind your server process manager:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

For production, put `OPENAI_API_KEY` in your host's secret/environment manager. Do not hard-code it in the source code.

Docker option:

```bash
docker build -t moderation-nlp .
docker run -p 8000:8000 -e OPENAI_API_KEY="your-api-key" moderation-nlp
```
