# Vodafone RAG Assistant

RAG assistant for Vodafone user queries with hybrid retrieval from Azure AI Search, generation with Azure OpenAI, and optional structured queries in PostgreSQL.

## Features

- Queries answers with context retrieved from Azure AI Search.
- Combines PostgreSQL results and RAG fragments when an authenticated user is present.
- Exposes a FastAPI API with `/health` and `/ask` endpoints.
- Includes configuration validation on startup.

## Requirements

- Python 3.12+
- Azure AI Search
- Azure OpenAI
- PostgreSQL (optional), as source of truth for user profiles

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment variables

Create a local `.env` file based on `.env.example`.

## Run the API

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

## Example request

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"que tarifa tengo?","username":"mcorbella"}'
```

## Files

- [api.py](api.py)
- [rag_vodafone.py](rag_vodafone.py)
- [test_user_integration.py](test_user_integration.py)
