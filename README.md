# Moderation NLP Server

Server-side JSON API for text moderation using the OpenAI moderation model.
The app has no UI. It accepts JSON input, calls OpenAI moderation, and returns
JSON output with category scores and summary fields.

## Files

- `app.py`: FastAPI application and moderation logic.
- `requirements.txt`: Python package dependencies.
- `.env.example`: Template for local environment variables.
- `.gitignore`: Keeps `.env`, virtual environments, and cache files out of Git.
- `Dockerfile`: Optional container build for server deployment.

## Requirements

- Python 3.9 or newer.
- An OpenAI API key.
- Internet access from the server so the app can call the OpenAI API.

## Install Locally

From the project folder:

```bash
cd "/Users/duchaba/Documents/moderation nlp"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If the virtual environment already exists, activate it and update packages:

```bash
cd "/Users/duchaba/Documents/moderation nlp"
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and set your OpenAI API key:

```bash
OPENAI_API_KEY=your-api-key
```

The application loads `.env` automatically. You can also set the key directly
in the shell:

```bash
export OPENAI_API_KEY="your-api-key"
```

Do not commit `.env`. It is ignored by `.gitignore`.

## Run The App

Start the server:

```bash
cd "/Users/duchaba/Documents/moderation nlp"
source .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000
```

When the server is running, the API is available at:

```text
http://localhost:8000
```

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

## API Endpoints

### Health Check

Request:

```bash
curl http://localhost:8000/health
```

Successful response:

```json
{
  "status": "ok"
}
```

### Moderate Text

Request:

```bash
curl -X POST http://localhost:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{"message":"I want to eat pizza and thinking about killing you.","safer":0.0005}'
```

Request body:

```json
{
  "message": "text to moderate",
  "safer": 0.0005
}
```

Input fields:

- `message`: Required string. The text to send to OpenAI moderation.
- `safer`: Optional number. Custom threshold used for `is_safer_flagged`.
  Defaults to `0.0005`.

Successful response:

```json
{
  "harassment": 0.4544254600591021,
  "harassment_threatening": 0.463955376504361,
  "hate": 0.0011826021388617776,
  "hate_threatening": 0.003334548179527813,
  "illicit": 0.02025874500971543,
  "illicit_violent": 0.008613207271058701,
  "self_harm": 0.004689724014751604,
  "self_harm_instructions": 0.00021559218865928174,
  "self_harm_intent": 0.0003102091628826725,
  "sexual": 0.00017274586267297022,
  "sexual_minors": 0.000002840974294610978,
  "violence": 0.9433940214218499,
  "violence_graphic": 0.0015619735921627608,
  "is_safer_flagged": true,
  "is_flagged": true,
  "max_key": "violence",
  "max_value": 0.9433940214218499,
  "sum_value": 2.3848005182675993,
  "safer_value": 0.0005,
  "message": "I want to eat pizza and thinking about killing you."
}
```

Response fields:

- OpenAI category score fields such as `harassment`, `hate`, `self_harm`,
  `sexual`, and `violence`.
- `is_safer_flagged`: `true` when the highest category score is greater than
  or equal to `safer`.
- `is_flagged`: OpenAI's built-in moderation flag.
- `max_key`: Category with the highest score.
- `max_value`: Highest category score.
- `sum_value`: Sum of all category scores.
- `safer_value`: Threshold used for `is_safer_flagged`.
- `message`: Original input text.

## Test Without Starting A Server

You can test the moderation function directly from Python:

```bash
cd "/Users/duchaba/Documents/moderation nlp"
source .venv/bin/activate
python -c "from app import moderate_text; import json; print(json.dumps(moderate_text('hello world'), indent=2))"
```

## Test With The Running Server

Start the app in one terminal:

```bash
cd "/Users/duchaba/Documents/moderation nlp"
source .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000
```

In another terminal, run:

```bash
curl http://localhost:8000/health
```

Then run:

```bash
curl -X POST http://localhost:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{"message":"hello world","safer":0.0005}'
```

## Validate Syntax

Run a Python syntax check:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/moderation_pycache .venv/bin/python -m py_compile app.py
```

The `PYTHONPYCACHEPREFIX` value keeps Python cache files out of system folders
that may not be writable in restricted environments.

## Docker

Build the image:

```bash
docker build -t moderation-nlp .
```

Run the container:

```bash
docker run -p 8000:8000 -e OPENAI_API_KEY="your-api-key" moderation-nlp
```

Test it:

```bash
curl http://localhost:8000/health
```

## Deployment Notes

Run the app behind your server process manager with:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

For production:

- Store `OPENAI_API_KEY` in your host's secret or environment manager.
- Do not hard-code the API key in source code.
- Do not commit `.env`.
- Make sure outbound HTTPS access to the OpenAI API is allowed.
- Put a reverse proxy such as Nginx or a platform load balancer in front if
  you need TLS, custom domains, or traffic management.

## Troubleshooting

### `OPENAI_API_KEY environment variable is required`

The app cannot find an API key. Add it to `.env` or export it in the shell:

```bash
export OPENAI_API_KEY="your-api-key"
```

### `Moderation request failed: Connection error`

The server could not reach OpenAI. Check internet access, DNS, firewall rules,
and whether outbound HTTPS is allowed.

### `422 Unprocessable Entity`

The JSON request body is invalid. Make sure `message` exists and is not empty:

```json
{
  "message": "text to moderate",
  "safer": 0.0005
}
```

### Port Already In Use

Run on another port:

```bash
uvicorn app:app --host 0.0.0.0 --port 8001
```
