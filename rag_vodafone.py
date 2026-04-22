import os
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

import psycopg
import requests
from openai import AzureOpenAI
from psycopg import sql
from psycopg.rows import dict_row


def _load_local_env(env_path: str = ".env") -> None:
    """Load KEY=VALUE pairs from a local .env file if present."""
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_local_env()


def _env_value(*names: str, default: str = "") -> str:
    """Return the first non-empty environment variable from a list of aliases."""
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return default

# =========================
# CONFIGURATION
# =========================

# Azure AI Search endpoint (env: AZURE_SEARCH_ENDPOINT), e.g. https://<service>.search.windows.net
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "").rstrip("/")

# Azure AI Search API key (env: AZURE_SEARCH_API_KEY)
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")

# Azure AI Search index name (env: AZURE_SEARCH_INDEX_NAME)
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "")

# Azure AI Search API version
AZURE_SEARCH_API_VERSION = "2023-11-01"

# Field in Azure AI Search that contains text chunks (env: AZURE_SEARCH_CONTENT_FIELD)
AZURE_SEARCH_CONTENT_FIELD = os.getenv("AZURE_SEARCH_CONTENT_FIELD", "content")

# Number of top chunks to retrieve
TOP_K = 3

# Timeout (seconds) for Azure AI Search REST calls
AZURE_SEARCH_TIMEOUT = int(os.getenv("AZURE_SEARCH_TIMEOUT", "180"))

# Azure OpenAI endpoint (env: AZURE_OPENAI_ENDPOINT), e.g. https://<resource>.openai.azure.com
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")

# Azure OpenAI API key (env: AZURE_OPENAI_API_KEY)
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")

# Azure OpenAI API version
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"

# Azure OpenAI deployment name for GPT-4o (env: AZURE_OPENAI_DEPLOYMENT)
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")

# Azure OpenAI embedding deployment for vector search
AZURE_EMBEDDING_DEPLOYMENT = os.getenv(
    "AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"
)

# Azure AI Search vector field name in the index
AZURE_SEARCH_VECTOR_FIELD = os.getenv("AZURE_SEARCH_VECTOR_FIELD", "snippet_vector")

# Semantic search toggles
AZURE_SEARCH_USE_SEMANTIC = os.getenv("AZURE_SEARCH_USE_SEMANTIC", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
AZURE_SEARCH_SEMANTIC_CONFIG = os.getenv("AZURE_SEARCH_SEMANTIC_CONFIG", "default")

# Max tokens for model response
MAX_OUTPUT_TOKENS = 700

# Temperature for response generation
TEMPERATURE = 0.2

# Timeout (seconds) for Azure OpenAI requests
AZURE_OPENAI_TIMEOUT = int(os.getenv("AZURE_OPENAI_TIMEOUT", "300"))

# Optional field in Azure Search index used to filter by username.
# Keep empty to disable strict filtering and rely on lexical/vector retrieval.
AZURE_SEARCH_USER_FILTER_FIELD = os.getenv("AZURE_SEARCH_USER_FILTER_FIELD", "").strip()

# Optional PostgreSQL source of truth for user profile data.
POSTGRES_DSN = _env_value("POSTGRES_DSN", "DB_DSN")
POSTGRES_HOST = _env_value("POSTGRES_HOST", "DB_HOST")
POSTGRES_PORT = int(_env_value("POSTGRES_PORT", "DB_PORT", default="5432"))
POSTGRES_DB = _env_value("POSTGRES_DB", "DB_NAME")
POSTGRES_USER = _env_value("POSTGRES_USER", "DB_USER")
POSTGRES_PASSWORD = _env_value("POSTGRES_PASSWORD", "DB_PASS")
POSTGRES_TABLE = os.getenv("POSTGRES_TABLE", "dispositivos").strip()
POSTGRES_USERNAME_COLUMN = os.getenv("POSTGRES_USERNAME_COLUMN", "username").strip()

THIRD_PARTY_REQUEST_PATTERNS = [
    r"\bde\s+(?:la|el|los|las)?\s*([A-Za-zÁÉÍÓÚáéíóúÑñ][A-Za-zÁÉÍÓÚáéíóúÑñ\s]{2,})",
    r"\b(?:de|para|sobre|acerca de)\s+([A-Za-zÁÉÍÓÚáéíóúÑñ][A-Za-zÁÉÍÓÚáéíóúÑñ\s]{2,})",
    r"\b(?:usuario|cliente)\s+([A-Za-z0-9._-]{3,})",
]

PERSONAL_ACCOUNT_KEYWORDS = {
    "tarifa",
    "plan",
    "mi tarifa",
    "mi plan",
    "contrato",
    "mis datos",
    "mis datos",
    "consumo",
    "saldo",
    "factura",
    "linea",
    "línea",
}

TARIFF_QUESTION_KEYWORDS = {
    "tarifa",
    "tipo de tarifa",
    "mi tarifa",
    "que tarifa tengo",
    "qué tarifa tengo",
    "cual es mi tarifa",
    "cuál es mi tarifa",
}


def _validate_config() -> None:
    """Fail fast if required environment variables are missing."""
    required = {
        "AZURE_SEARCH_ENDPOINT": AZURE_SEARCH_ENDPOINT,
        "AZURE_SEARCH_API_KEY": AZURE_SEARCH_API_KEY,
        "AZURE_SEARCH_INDEX_NAME": AZURE_SEARCH_INDEX_NAME,
        "AZURE_SEARCH_CONTENT_FIELD": AZURE_SEARCH_CONTENT_FIELD,
        "AZURE_OPENAI_ENDPOINT": AZURE_OPENAI_ENDPOINT,
        "AZURE_OPENAI_API_KEY": AZURE_OPENAI_API_KEY,
        "AZURE_OPENAI_DEPLOYMENT": AZURE_OPENAI_DEPLOYMENT,
        "AZURE_EMBEDDING_DEPLOYMENT": AZURE_EMBEDDING_DEPLOYMENT,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ValueError(
            "Faltan variables de entorno requeridas: " + ", ".join(missing)
        )


def _normalize_text(value: str) -> str:
    """Lowercase and remove accents for robust lexical matching."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return ascii_only.lower()


def _extract_keywords(question: str) -> List[str]:
    """Extract useful keywords from the user query for fallback search."""
    stopwords = {
        "que", "como", "donde", "cuando", "cual", "cuanto", "de", "del", "la", "el",
        "los", "las", "un", "una", "unos", "unas", "y", "o", "en", "por", "para",
        "con", "sin", "a", "al", "mi", "tu", "su", "si", "voy", "hacer", "debo",
    }
    tokens = re.findall(r"[A-Za-z0-9ÁÉÍÓÚáéíóúñÑ]+", question)
    keywords: List[str] = []
    seen = set()
    for token in tokens:
        token_norm = _normalize_text(token)
        if len(token_norm) < 4 or token_norm in stopwords or token_norm in seen:
            continue
        seen.add(token_norm)
        keywords.append(token)
    return keywords


def _accent_variants(term: str) -> List[str]:
    """Generate single-accent variants for lexical fallback queries."""
    variants = {term}
    accent_map = {
        "a": "á",
        "e": "é",
        "i": "í",
        "o": "ó",
        "u": "ú",
    }
    lower = term.lower()
    for idx, ch in enumerate(lower):
        if ch in accent_map:
            variants.add(lower[:idx] + accent_map[ch] + lower[idx + 1 :])
    return list(variants)


def _extract_user_from_question(question: str) -> Tuple[str, Optional[str]]:
    """Extract username from inline question text.

    Supported formats:
    - "usuario: juan.perez cual es mi tarifa"
    - "username=juan.perez ..."
    - "Isbek01:\nQue tarifa tengo?"
    """

    def _looks_like_username(value: str) -> bool:
        token = value.strip()
        if not token or len(token) < 3 or " " in token:
            return False
        if not re.fullmatch(r"[A-Za-z0-9._-]+", token):
            return False
        reserved = {"usuario", "username", "user", "asistente", "assistant", "pregunta"}
        if _normalize_text(token) in reserved:
            return False
        # Heuristic to avoid treating random labels as username.
        return bool(re.search(r"[0-9._-]", token))

    explicit_pattern = re.compile(
        r"(?:^|\b)(?:usuario|username|user)\s*[:=]\s*([a-zA-Z0-9._-]+)",
        re.IGNORECASE,
    )
    explicit_match = explicit_pattern.search(question)
    if explicit_match:
        username = explicit_match.group(1).strip()
        cleaned_question = (
            question[: explicit_match.start()] + question[explicit_match.end() :]
        ).strip(" ;,.-\n\t")
        return cleaned_question.strip(), username or None

    leading_tag_pattern = re.compile(r"^\s*([A-Za-z0-9._-]{3,})\s*:\s*(.*)$", re.DOTALL)
    leading_tag_match = leading_tag_pattern.match(question)
    if leading_tag_match:
        candidate_user = leading_tag_match.group(1).strip()
        remaining_question = leading_tag_match.group(2).strip()
        if _looks_like_username(candidate_user) and remaining_question:
            return remaining_question, candidate_user

    return question.strip(), None


def _extract_plan_lines(chunks: List[str]) -> List[str]:
    """Extract likely tariff/plan lines from retrieved chunks."""
    plan_lines: List[str] = []
    seen = set()
    keywords = {"tarifa", "plan", "tipo de tarifa", "tipo_tarifa"}

    for chunk in chunks:
        for raw_line in chunk.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            norm = _normalize_text(line)
            if not any(term in norm for term in keywords):
                continue
            if norm in seen:
                continue
            seen.add(norm)
            plan_lines.append(line)
            if len(plan_lines) >= 5:
                return plan_lines
    return plan_lines


def _candidate_usernames(username: str) -> List[str]:
    """Generate lookup variants for usernames that may come as emails."""
    candidates: List[str] = []
    for candidate in [username, username.split("@")[0] if "@" in username else ""]:
        candidate = candidate.strip()
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _postgres_enabled() -> bool:
    """Return True when enough config is present to query PostgreSQL."""
    if POSTGRES_DSN:
        return True
    return all([POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD])


def _fetch_user_profile_from_postgres(username: str) -> Dict[str, str]:
    """Fetch the user row from PostgreSQL using the provided username."""
    if not username or not _postgres_enabled():
        return {}

    connection_kwargs = {
        "row_factory": dict_row,
        "connect_timeout": 10,
    }

    try:
        if POSTGRES_DSN:
            connection = psycopg.connect(POSTGRES_DSN, **connection_kwargs)
        else:
            connection = psycopg.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                **connection_kwargs,
            )

        query = sql.SQL(
            "SELECT * FROM {} WHERE lower({}) = lower(%s) LIMIT 1"
        ).format(
            sql.Identifier(POSTGRES_TABLE),
            sql.Identifier(POSTGRES_USERNAME_COLUMN),
        )

        with connection as conn:
            with conn.cursor() as cursor:
                for candidate in _candidate_usernames(username):
                    cursor.execute(query, (candidate,))
                    row = cursor.fetchone()
                    if row:
                        return {
                            str(key): "" if value is None else str(value)
                            for key, value in dict(row).items()
                        }
    except Exception:
        return {}

    return {}


def _build_user_profile_context_from_postgres(username: str, row: Dict[str, str]) -> str:
    """Render the PostgreSQL row as a user-only context block."""
    if not row:
        return ""

    lines = ["[Perfil Usuario BD]", f"username: {username}"]

    preferred_keys = [
        "nombre",
        "usuario",
        "username",
        "tarifa",
        "tipo_tarifa",
        "plan",
    ]
    seen = set()

    for key in preferred_keys:
        value = row.get(key, "").strip()
        if value:
            seen.add(_normalize_text(key))
            lines.append(f"{key}: {value}")

    for key, value in row.items():
        if not value:
            continue
        if _normalize_text(key) in seen:
            continue
        preview = value.strip()
        if len(preview) > 240:
            preview = preview[:240] + "..."
        lines.append(f"{key}: {preview}")

    return "\n".join(lines)


def _build_sql_query_result_context(username: str, row: Dict[str, str]) -> str:
    """Build a SQL result block even when no row is found for the user."""
    if not username:
        return ""
    if row:
        return _build_user_profile_context_from_postgres(username=username, row=row)
    return "\n".join(
        [
            "[Perfil Usuario BD]",
            f"username: {username}",
            "resultado_sql: sin filas para este usuario",
        ]
    )


def _extract_tariff_from_row(row: Dict[str, str]) -> str:
    """Return the most likely tariff value from a PostgreSQL row."""
    if not row:
        return ""

    tariff_keys = ["tarifa", "tipo_tarifa", "plan", "tipo de tarifa"]
    normalized_row = {_normalize_text(key): value for key, value in row.items()}
    for key in tariff_keys:
        value = str(normalized_row.get(_normalize_text(key), "")).strip()
        if value and value.lower() != "nan":
            return value
    return ""


def _is_third_party_request(question: str, username: str, user_display_name: str) -> bool:
    """Detect if the user asks about someone else rather than their own profile."""
    if not question.strip():
        return False

    question_norm = _normalize_text(question)
    own_tokens = {
        _normalize_text(username) if username else "",
        _normalize_text(user_display_name) if user_display_name else "",
    }
    own_tokens = {token for token in own_tokens if token}
    self_reference_prefixes = ("mi ", "mis ", "mio", "mia", "mias", "mios")
    non_person_targets = {
        "telefono",
        "numero",
        "numero de telefono",
        "linea",
        "tarifa",
        "plan",
        "factura",
        "contrato",
        "saldo",
        "consumo",
        "datos",
        "correo",
        "email",
        "direccion",
    }

    for pattern in THIRD_PARTY_REQUEST_PATTERNS:
        match = re.search(pattern, question, re.IGNORECASE)
        if not match:
            continue

        candidate = match.group(1).strip()
        candidate_norm = _normalize_text(candidate)
        if not candidate_norm:
            continue

        if candidate_norm in {"mi", "mio", "mía", "mio", "mis"}:
            continue

        if candidate_norm.startswith(self_reference_prefixes):
            continue

        if candidate_norm in non_person_targets:
            continue

        if candidate_norm in own_tokens:
            continue

        # If the user explicitly references another person, block it.
        if candidate_norm not in own_tokens:
            return True

    # Also block generic requests that clearly ask for other people's data.
    suspicious_phrases = [
        "tarifa de",
        "contrato de",
        "datos de",
        "informacion de",
        "información de",
        "saldo de",
        "consumo de",
    ]
    for phrase in suspicious_phrases:
        if phrase in question_norm and "mi " not in question_norm and "mio" not in question_norm:
            return True

    return False


def _filter_profile_chunks_for_username(chunks: List[str], username: str) -> List[str]:
    """Keep only the parts of the retrieved profile chunks that mention the user."""
    if not chunks or not username:
        return chunks

    username_norm = _normalize_text(username)
    filtered_chunks: List[str] = []
    for chunk in chunks:
        if username_norm in _normalize_text(chunk):
            filtered_chunks.append(chunk)

    return filtered_chunks or chunks


def _is_personal_account_question(question: str) -> bool:
    """Detect if the user is asking about their own account/profile."""
    question_norm = _normalize_text(question)
    return any(keyword in question_norm for keyword in PERSONAL_ACCOUNT_KEYWORDS)


def _is_tariff_question(question: str) -> bool:
    """Detect tariff-focused questions that must be answered from structured data."""
    question_norm = _normalize_text(question)
    return any(keyword in question_norm for keyword in TARIFF_QUESTION_KEYWORDS)


def _build_profile_answer(username: str, question: str) -> Dict[str, object]:
    """Answer using only the user's profile-related chunks."""
    profile_row = _fetch_user_profile_from_postgres(username=username)
    sql_context = _build_sql_query_result_context(username=username, row=profile_row)
    rag_chunks = search_azure(
        question,
        username_filter=username,
    )
    rag_chunks = _filter_profile_chunks_for_username(rag_chunks, username)
    rag_context = build_context(rag_chunks)
    context = f"{sql_context}\n\n{rag_context}" if rag_context else sql_context

    if not context:
        return {
            "question": question,
            "chunks": [],
            "context": "",
            "answer": (
                "No encuentro informacion de tu perfil en la base de datos ni en los fragmentos recuperados. "
                "No puedo confirmar tu tarifa con lo que tengo disponible."
            ),
            "username": username,
            "user_display_name": "",
            "blocked": False,
        }

    answer = generate_answer(question, context)
    return {
        "question": question,
        "chunks": rag_chunks,
        "context": context,
        "answer": answer,
        "username": username,
        "user_display_name": "",
        "blocked": False,
        "source": "postgres+azure_search" if profile_row else "azure_search",
        "tarifa": _extract_tariff_from_row(profile_row) if profile_row else "",
    }


def _build_tariff_answer_from_postgres(username: str, question: str) -> Dict[str, object]:
    """Answer tariff questions using both SQL result and retrieved RAG chunks."""
    profile_row = _fetch_user_profile_from_postgres(username=username)
    tariff_value = _extract_tariff_from_row(profile_row)
    sql_context = _build_sql_query_result_context(
        username=username,
        row=profile_row,
    )
    rag_chunks = search_azure(
        question,
        username_filter=username,
    )
    rag_chunks = _filter_profile_chunks_for_username(rag_chunks, username)
    rag_context = build_context(rag_chunks)
    context = f"{sql_context}\n\n{rag_context}" if rag_context else sql_context
    answer = generate_answer(question, context)

    return {
        "question": question,
        "chunks": rag_chunks,
        "context": context,
        "answer": answer,
        "username": username,
        "user_display_name": "",
        "blocked": False,
        "source": "postgres+azure_search" if profile_row else "azure_search",
        "tarifa": tariff_value,
    }


def _build_user_profile_context_from_index(username: str) -> str:
    """Fetch user profile hints from Azure Search index (Blob-ingested content)."""
    if not username:
        return ""

    profile_query = f"{username} tarifa plan tipo de tarifa"
    profile_chunks = search_azure(
        profile_query,
        top_k=3,
        username_filter=username,
    )
    if not profile_chunks:
        return ""

    profile_chunks = _filter_profile_chunks_for_username(profile_chunks, username)

    lines = ["[Perfil Usuario Recuperado]", f"username: {username}"]
    plan_lines = _extract_plan_lines(profile_chunks)
    if plan_lines:
        lines.append("Datos potenciales de tarifa/plan:")
        for item in plan_lines:
            lines.append(f"- {item}")

    lines.append("Fragmentos de perfil relevantes:")
    for idx, chunk in enumerate(profile_chunks, start=1):
        preview = chunk.replace("\n", " ").strip()
        if len(preview) > 240:
            preview = preview[:240] + "..."
        lines.append(f"[{idx}] {preview}")

    return "\n".join(lines)


# =========================
# RAG FUNCTIONS
# =========================

def search_azure(
    question: str,
    top_k: int = TOP_K,
    username_filter: str = "",
) -> List[str]:
    """
    Hybrid search in Azure AI Search (lexical + vector, optional semantic).
    """
    url = (
        f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_NAME}/docs/"
        f"search?api-version={AZURE_SEARCH_API_VERSION}"
    )

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_SEARCH_API_KEY,
    }

    embedding_client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        timeout=AZURE_OPENAI_TIMEOUT,
    )
    embedding_response = embedding_client.embeddings.create(
        input=question,
        model=AZURE_EMBEDDING_DEPLOYMENT,
    )
    query_vector = embedding_response.data[0].embedding

    payload = {
        "search": question,
        "top": top_k,
        "select": AZURE_SEARCH_CONTENT_FIELD,
        "searchFields": AZURE_SEARCH_CONTENT_FIELD,
        "vectorQueries": [
            {
                "kind": "vector",
                "vector": query_vector,
                "fields": AZURE_SEARCH_VECTOR_FIELD,
                "k": top_k * 3,
            }
        ],
    }

    if username_filter and AZURE_SEARCH_USER_FILTER_FIELD:
        username_escaped = username_filter.replace("'", "''")
        payload["filter"] = (
            f"{AZURE_SEARCH_USER_FILTER_FIELD} eq '{username_escaped}'"
        )

    if AZURE_SEARCH_USE_SEMANTIC:
        payload["queryType"] = "semantic"
        payload["semanticConfiguration"] = AZURE_SEARCH_SEMANTIC_CONFIG

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=AZURE_SEARCH_TIMEOUT,
        )
        response.raise_for_status()
    except requests.HTTPError:
        # If semantic ranker isn't enabled, retry as hybrid without semantic options.
        if AZURE_SEARCH_USE_SEMANTIC:
            payload.pop("queryType", None)
            payload.pop("semanticConfiguration", None)
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=AZURE_SEARCH_TIMEOUT,
            )
            response.raise_for_status()
        else:
            raise

    docs = response.json().get("value", [])
    return [
        str(doc[AZURE_SEARCH_CONTENT_FIELD]).strip()
        for doc in docs
        if doc.get(AZURE_SEARCH_CONTENT_FIELD)
    ]


def build_context(chunks: List[str]) -> str:
    """
    Build a single context string from retrieved chunks.
    """
    if not chunks:
        return ""

    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[Fragmento {i}]\n{chunk}")

    return "\n\n".join(parts)


def generate_answer(question: str, context: str) -> str:
    """
    Call Azure OpenAI GPT-4o with system instructions and context.
    """
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        timeout=AZURE_OPENAI_TIMEOUT,
    )

    system_prompt = (
        "Eres un asistente experto en contratos de Vodafone. "
        "Responde SOLO usando el contexto proporcionado. "
        "Responde unicamente sobre el usuario autenticado que aparece en el contexto. "
        "No reveles ni infieras datos de otros usuarios, aunque aparezcan en los fragmentos recuperados. "
        "Si la pregunta pide informacion de otra persona o de otro cliente, responde que no puedes ayudar con datos de terceros. "
        "Si la respuesta no esta en el contexto del usuario autenticado, di claramente que no aparece en los fragmentos recuperados. "
        "Cuando sea util, cita el numero de fragmento, por ejemplo: [Fragmento 1]."
    )

    user_prompt = (
        f"Pregunta del usuario:\n{question}\n\n"
        f"Contexto recuperado:\n{context if context else 'No hay contexto recuperado.'}"
    )

    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_OUTPUT_TOKENS,
    )

    return response.choices[0].message.content.strip()


def rag(
    question: str,
    username: str = "",
    user_display_name: str = "",
) -> Dict[str, object]:
    """
    End-to-end RAG flow:
    1) Search in Azure AI Search
    2) Build context
    3) Generate answer with Azure OpenAI
    """
    cleaned_question, username_from_question = _extract_user_from_question(question)
    username = (username or "").strip() or (username_from_question or "")
    user_display_name = (user_display_name or "").strip()

    if _is_third_party_request(cleaned_question, username=username, user_display_name=user_display_name):
        return {
            "question": cleaned_question,
            "chunks": [],
            "context": "",
            "answer": (
                "No puedo ayudar con informacion de terceros. "
                "Solo puedo responder sobre tu propia informacion asociada al usuario autenticado."
            ),
            "username": username,
            "user_display_name": user_display_name,
            "blocked": True,
        }

    if username and _is_tariff_question(cleaned_question):
        return _build_tariff_answer_from_postgres(
            username=username,
            question=cleaned_question,
        )

    if username and _is_personal_account_question(cleaned_question):
        return _build_profile_answer(username=username, question=cleaned_question)

    chunks = search_azure(cleaned_question)
    context = build_context(chunks)

    profile_row = _fetch_user_profile_from_postgres(username=username)
    profile_context = _build_user_profile_context_from_postgres(username=username, row=profile_row)
    if not profile_context:
        profile_context = _build_user_profile_context_from_index(username=username)
    if profile_context:
        context = f"{profile_context}\n\n{context}" if context else profile_context

    answer = generate_answer(cleaned_question, context)

    return {
        "question": cleaned_question,
        "chunks": chunks,
        "context": context,
        "answer": answer,
        "username": username,
        "user_display_name": user_display_name,
        "blocked": False,
        "source": "postgres" if profile_row else "azure_search",
    }


if __name__ == "__main__":
    _validate_config()
    user_question = input("Escribe tu pregunta: ").strip()

    if not user_question:
        raise ValueError("La pregunta no puede estar vacia.")

    result = rag(user_question)

    print("\n=== Respuesta ===")
    print(result["answer"])

    print("\n=== Fragmentos recuperados ===")
    for idx, chunk in enumerate(result["chunks"], start=1):
        preview = chunk.replace("\n", " ")
        if len(preview) > 300:
            preview = preview[:300] + "..."
        print(f"[{idx}] {preview}")

    # Optional full JSON output for debugging
    # print(json.dumps(result, ensure_ascii=False, indent=2))
