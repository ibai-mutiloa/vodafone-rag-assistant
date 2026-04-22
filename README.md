# Vodafone RAG Assistant

Asistente RAG para consultas de usuarios de Vodafone con recuperación híbrida desde Azure AI Search, generación con Azure OpenAI y consulta estructurada opcional en PostgreSQL.

## Features

- Consulta respuestas con contexto recuperado desde Azure AI Search.
- Combina resultados de PostgreSQL y fragmentos RAG cuando hay usuario autenticado.
- Expone una API FastAPI con `/health` y `/ask`.
- Incluye validación de configuración al arrancar.

## Requirements

- Python 3.12+
- Azure AI Search
- Azure OpenAI
- PostgreSQL opcional, como fuente de verdad para perfiles de usuario

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
