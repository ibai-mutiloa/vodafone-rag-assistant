from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_vodafone import _validate_config, rag


class AskRequest(BaseModel):
    question: str
    username: str = None  # Usuario que realiza la pregunta
    user_display_name: str = None  # Nombre visible del usuario
    response_language: str = "es"  # es | eus


app = FastAPI(title="Vodafone RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_validate_config() -> None:
    _validate_config()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask")
def ask(payload: AskRequest) -> dict:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    username = (payload.username or "").strip()
    user_display_name = (payload.user_display_name or "").strip()
    response_language = (payload.response_language or "es").strip().lower()

    try:
        result = rag(
            question=question,
            username=username,
            user_display_name=user_display_name,
            response_language=response_language,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "question": result.get("question", question),
        "answer": result.get("answer", ""),
        "chunks": result.get("chunks", []),
        "username": result.get("username", username),
        "response_language": result.get("response_language", response_language),
    }
