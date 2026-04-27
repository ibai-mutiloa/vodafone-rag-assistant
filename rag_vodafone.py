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

SUPPORTED_RESPONSE_LANGUAGES = {"es", "eus"}

ZONA_WORLD_COUNTRY_KEYWORDS = {"canada", "japon", "mexico"}
FAIR_USE_ZONE1_COUNTRY_KEYWORDS = {
    "alemania",
    "francia",
    "italia",
    "portugal",
    "noruega",
    "suiza",
    "turquia",
    "albania",
    "monaco",
    "islandia",
    "liechtenstein",
    "estados unidos",
    "eeuu",
    "usa",
    "reino unido",
}


def _normalize_response_language(language: str) -> str:
    """Normalize requested response language to supported values."""
    value = _normalize_text((language or "").strip())
    if value in {"eus", "eu", "euskera", "basque"}:
        return "eus"
    return "es"


def _third_party_block_message(response_language: str) -> str:
    """Return localized message for third-party data requests."""
    if response_language == "eus":
        return (
            "Ezin dut hirugarrenen informazioarekin lagundu. "
            "Soilik autentifikatutako erabiltzaileari lotutako zure informazioari buruz erantzun dezaket."
        )
    return (
        "No puedo ayudar con informacion de terceros. "
        "Solo puedo responder sobre tu propia informacion asociada al usuario autenticado."
    )


def _missing_profile_message(response_language: str) -> str:
    """Return localized message when no user profile context is available."""
    if response_language == "eus":
        return (
            "Ez dut zure profileko informaziorik aurkitzen ez datu-basean ezta berreskuratutako zatietan ere. "
            "Ezin dut zure tarifa baieztatu eskuragarri dudan informazioarekin."
        )
    return (
        "No encuentro informacion de tu perfil en la base de datos ni en los fragmentos recuperados. "
        "No puedo confirmar tu tarifa con lo que tengo disponible."
    )


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
    """Detect if the user asks about someone else rather than their own profile.
    
    SIMPLIFIED LOGIC:
    - If a valid username is provided, the user is authenticated
    - Allow authenticated users to ask about their own account
    - Only check for third-party requests if NO username is provided
    """
    
    # If we have a valid username, consider the user authenticated
    # and allow them to ask questions about their own account
    if username and len(username.strip()) > 3:
        # User is authenticated - only block if explicitly asking about another person
        question_norm = _normalize_text(question)
        explicit_third_party_phrases = [
            "del usuario ",
            "de otro usuario",
            "de otra persona",
            "de juan",
            "de maria",
            "de carlos",
            "de mi jefe",
            "de mi compañero ",
            "de mi amigo ",
        ]
        if any(phrase in question_norm for phrase in explicit_third_party_phrases):
            return True
        # Allow authenticated user to proceed
        return False
    
    # No username provided - apply original restrictive logic
    if not question.strip():
        return False

    question_norm = _normalize_text(question)
    # Without authentication, be very restrictive
    return True


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


def _enrich_roaming_query(question: str) -> str:
    """Enrich retrieval query for known roaming scenarios that need contract anchors."""
    question_norm = _normalize_text(question)
    enriched = question

    if any(country in question_norm for country in ZONA_WORLD_COUNTRY_KEYWORDS):
        enriched += (
            " Zona World Zona 2 Grandes Clientes Bono Compartido Zona 2 "
            "500 MB 140 euros"
        )

    if any(term in question_norm for term in {"sms", "llamada", "llamadas", "recibida", "recibidas"}):
        enriched += " descuento 100 por ciento coste final 0 euros"

    return enriched


def _inject_fair_use_context(question: str, context: str) -> str:
    """Inject contractual warning for long stays in Zona 1 (>4 months)."""
    question_norm = _normalize_text(question)
    has_long_stay = bool(re.search(r"\b([5-9]|[1-9][0-9]+)\s*mes", question_norm))
    mentions_remote_stay = any(
        marker in question_norm
        for marker in {"6 meses", "5 meses", "trabajando en remoto", "quedarme", "larga estancia"}
    )
    mentions_zona1_country = any(
        country in question_norm for country in FAIR_USE_ZONE1_COUNTRY_KEYWORDS
    )

    if (has_long_stay or mentions_remote_stay) and mentions_zona1_country:
        note = (
            "\n[Nota contractual MGEP - Politica de Uso Razonable]\n"
            "Si en un periodo de 4 meses el consumo y la estancia en Zona 1 superan al uso en Espana, "
            "Vodafone puede notificar uso abusivo y aplicar recargos. "
            "Para estancias superiores a 4 meses en Zona 1, advertir siempre este riesgo.\n"
        )
        return note + context

    return context


def _build_profile_answer(
    username: str,
    question: str,
    response_language: str,
) -> Dict[str, object]:
    """Answer using only the user's profile-related chunks."""
    profile_row = _fetch_user_profile_from_postgres(username=username)
    sql_context = _build_sql_query_result_context(username=username, row=profile_row)
    rag_question = _enrich_roaming_query(question)
    rag_chunks = search_azure(
        rag_question,
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
            "answer": _missing_profile_message(response_language),
            "username": username,
            "user_display_name": "",
            "blocked": False,
            "response_language": response_language,
        }

    context = _inject_fair_use_context(question, context)
    answer = generate_answer(
        question,
        context,
        response_language=response_language,
    )
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
        "response_language": response_language,
    }


def _build_tariff_answer_from_postgres(
    username: str,
    question: str,
    response_language: str,
) -> Dict[str, object]:
    """Answer tariff questions using both SQL result and retrieved RAG chunks."""
    profile_row = _fetch_user_profile_from_postgres(username=username)
    tariff_value = _extract_tariff_from_row(profile_row)
    sql_context = _build_sql_query_result_context(
        username=username,
        row=profile_row,
    )
    rag_question = _enrich_roaming_query(question)
    rag_chunks = search_azure(
        rag_question,
        username_filter=username,
    )
    rag_chunks = _filter_profile_chunks_for_username(rag_chunks, username)
    rag_context = build_context(rag_chunks)
    context = f"{sql_context}\n\n{rag_context}" if rag_context else sql_context
    context = _inject_fair_use_context(question, context)
    answer = generate_answer(
        question,
        context,
        response_language=response_language,
    )

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
        "response_language": response_language,
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


def generate_answer(
    question: str,
    context: str,
    response_language: str = "es",
) -> str:
    """
    Call Azure OpenAI GPT-4o with system instructions and context.
    """
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        timeout=AZURE_OPENAI_TIMEOUT,
    )

    response_language = _normalize_response_language(response_language)
    language_instruction = (
        "Responde siempre en euskera."
        if response_language == "eus"
        else "Responde siempre en castellano."
    )

    system_prompt = (
        "Eres un asistente experto en contratos de Vodafone para flotas móviles corporativas de MGEP. "
        f"{language_instruction} "
        "Responde SOLO usando el contexto proporcionado. "
        "Responde unicamente sobre el usuario autenticado que aparece en el contexto. "
        "No reveles ni infieras datos de otros usuarios, aunque aparezcan en los fragmentos recuperados. "
        "\n"

        "ZONAS DE ROAMING - CLASIFICACIÓN OFICIAL (CRÍTICO, NO CONTRADECIR NUNCA):\n"
        "Zona 1 (Europa): Países de la UE, Reino Unido, Noruega, Islandia, Liechtenstein, Suiza, "
        "Turquía, Gibraltar, Mónaco, San Marino, Kosovo, Caribe Francés, La Reunión. "
        "BAJO NINGÚN CONCEPTO incluyas EE.UU., Canadá, México, Puerto Rico ni ningún país americano en Zona 1.\n"
        "Zona 2 (World Grandes Clientes): EE.UU., Canadá, México, Japón, Argentina, Brasil, Australia, "
        "Marruecos, China, India, Puerto Rico y muchos otros. "
        "Los datos en Zona 2 van contra el Bono Compartido Zona 2. "
        "Si se supera el bono, se aprovisiona automáticamente un bono adicional de 500 MB a 140 euros.\n"
        "Zona 3: Bolivia, Venezuela, Nigeria, Pakistán, y otros países no incluidos en Zona 1 ni Zona 2.\n"
        "Zona 4: Cuba, Angola, Iraq, Kuwait, Emiratos Árabes Unidos (Dubai), y otros. "
        "Es la zona más cara del contrato.\n"
        "Zona 5: Andorra (únicamente). No pertenece a Zona 1 pese a ser país vecino.\n"
        "Andorra NO es Zona 1. Las Islas Canarias son territorio nacional, sin roaming.\n"
        "\n"

        # NUEVO: precios roaming Zona 4 hardcodeados para evitar que el RAG recupere
        # la tabla de llamadas internacionales desde España (precios distintos)
        "TARIFAS DE ROAMING EN ZONA 4 (CRÍTICO - USAR SIEMPRE ESTOS PRECIOS PARA ZONA 4):\n"
        "Cuando el usuario esté físicamente EN un país de Zona 4 (Cuba, Dubai, Kuwait, Angola...):\n"
        "- Llamadas realizadas desde Zona 4: establecimiento 0,49 € + 4,96 €/min.\n"
        "- Llamadas recibidas en Zona 4: establecimiento 0,49 € + 1,95 €/min.\n"
        "- SMS enviados desde Zona 4: 1 €/SMS.\n"
        "- Datos: tarifa Mega Libre, precios muy elevados. Recomendar siempre uso de WiFi.\n"
        "NUNCA uses el precio de 1,00 €/min para llamadas realizadas en Zona 4. "
        "Ese precio corresponde a llamadas INTERNACIONALES desde España, no a roaming.\n"
        "\n"

        # NUEVO: precios roaming Zona 2 hardcodeados para evitar mezcla con Zona 3
        "TARIFAS DE ROAMING EN ZONA 2 (USAR SIEMPRE ESTOS PRECIOS PARA ZONA 2):\n"
        "Cuando el usuario esté físicamente EN un país de Zona 2 (EE.UU., Canadá, Japón, Argentina...):\n"
        "- Llamadas realizadas desde Zona 2 a Zona 1: establecimiento 0,49 € + 1,45 €/min.\n"
        "- Llamadas recibidas en Zona 2: establecimiento 0,49 € + 1,45 €/min.\n"
        "- SMS enviados desde Zona 2: 1 €/SMS.\n"
        "NUNCA uses 1,95 €/min para llamadas en Zona 2. Ese precio corresponde a Zona 3.\n"
        "\n"

        "TARIFAS ESPECÍFICAS EE.UU. (SOLO APLICAN A EE.UU., NO A CANADÁ NI PUERTO RICO):\n"
        "Para viajes a EE.UU. existen dos opciones específicas que el usuario puede activar expresamente:\n"
        "- Tarifa diaria: 5 euros cada 24h, incluye 200 minutos y 200 MB. Solo se cobra los días de uso.\n"
        "- Bono mensual: 20 euros/mes, incluye 1.000 minutos y 1 GB.\n"
        "IMPORTANTE - COMPARATIVA ECONÓMICA: el bono mensual (20 €) es siempre más barato que la tarifa "
        "diaria para estancias de MÁS DE 4 DÍAS (4 días × 5 € = 20 €). Para 5 o más días, recomienda "
        "siempre el bono mensual. Para 1-3 días, recomienda la tarifa diaria.\n"
        "Canadá, Puerto Rico y el resto de países de Zona 2 NO tienen acceso a estas tarifas EE.UU. "
        "Para ellos aplica únicamente el Bono Compartido Zona 2.\n"
        "Sin estas tarifas activas, EE.UU. se rige por las condiciones generales de Zona 2.\n"
        "\n"

        "IMPORTANTE - REGLAS TRANSVERSALES A TODAS LAS TARIFAS INFINITY BUSINESS:\n"
        "- Zona 1: datos y llamadas incluidos en la tarifa como si fuera España (sujeto a uso razonable).\n"
        "- Llamadas recibidas en Zona 1: coste 0 euros (descuento 100%).\n"
        "- Llamadas GCU (entre líneas MGEP del mismo grupo): coste 0 euros, incluso en roaming Zona 1.\n"
        "- Soporte técnico 24x7: teléfono 900 878 007 (gratuito desde España), "
        "+34 91 235 99 97 desde el extranjero (coste según tarifa).\n"
        "- Restricción por robo o pérdida: inmediata llamando al 900 878 007.\n"
        "- Duplicado de SIM: 5 euros, gestionar con el responsable de telefonía de MGEP.\n"
        "\n"

        "VELOCIDADES TRAS AGOTAR DATOS:\n"
        "- Perfil Ilimitado (predeterminado si no se ha configurado otro): velocidad reducida a 128 Kbps.\n"
        "- Perfiles con límite fijo (300 MB, 1 GB, 2 GB, 3 GB, 5 GB, 10 GB, 20 GB, 25 GB, 50 GB): "
        "velocidad reducida a 8 Kbps.\n"
        # NUEVO: instrucción explícita de consultar el perfil del usuario en BD antes de responder
        "CRÍTICO: consulta siempre el [Perfil Usuario BD] para saber qué perfil tiene el usuario. "
        "Si su tarifa es 'Infinity Business 10GB' u otro perfil con GB fijos, la velocidad reducida "
        "es 8 Kbps. Si el perfil es 'Ilimitado', es 128 Kbps. "
        "Si no se puede determinar el perfil, indica ambas opciones y pide al usuario que lo confirme "
        "con el responsable de telefonía.\n"
        "\n"

        "POLÍTICA DE USO RAZONABLE EN ZONA 1:\n"
        "Si el usuario menciona estancias en Zona 1 superiores a 4 meses, advierte siempre que "
        "Vodafone puede considerar uso abusivo si la presencia y consumo en Zona 1 supera al realizado "
        "en España durante ese período, y que pueden aplicarse recargos tras notificación de 15 días.\n"
        "\n"

        "LÍMITE DE GASTO EN ROAMING:\n"
        "Existe un límite automático de 500 euros/mes para roaming de datos fuera de Zona 1 "
        "(en Zona 1 dentro de uso razonable no aplica). En Zona 2 hay además un límite de 1 GB por línea. "
        "Ambos límites son modificables desde Mi Vodafone Business sin coste.\n"
        "\n"

        "INTERPRETACIÓN SEMÁNTICA:\n"
        "Cuando el usuario pregunta por:\n"
        "- 'Llamadas a compañeros / colegas / empleados de MGEP' → reglas GCU, coste 0 euros.\n"
        "- 'Datos en viaje' → identifica primero el país y su zona antes de responder.\n"
        "- 'Soporte técnico / atención al cliente / problema con la línea' → 900 878 007, 24x7.\n"
        "- 'Me han robado / he perdido el móvil' → restricción inmediata llamando al 900 878 007.\n"
        "- 'Hotspot / compartir datos / tethering' → permitido, consume del bono compartido habitual.\n"
        # NUEVO: patrón para preguntas de comparativa económica
        "- '¿Es mejor...?' / '¿Qué me conviene...?' / '¿Cuál es más barato...?' → haz el cálculo "
        "numérico explícito antes de dar la recomendación. No des una respuesta condicional si puedes "
        "calcular la respuesta exacta con los datos disponibles.\n"
        "\n"

        "REGLAS DE PRESENTACIÓN:\n"
        "- Si una condición indica descuento del 100%, el coste final para el usuario es 0 euros.\n"
        "- Antes de responder sobre roaming, identifica explícitamente la zona del país de destino.\n"
        "- Recomienda siempre confirmar con el responsable de telefonía de MGEP antes de viajar "
        "a destinos fuera de Zona 1.\n"
        "- Cuando sea útil, cita el número de fragmento: [Fragmento N].\n"
        # NUEVO: evitar que el chatbot sugiera tarifas EE.UU. para destinos que no son EE.UU.
        "- NUNCA sugieras las tarifas diaria o mensual de EE.UU. para destinos que no sean EE.UU. "
        "continental. Para cualquier otro país de Zona 2 usa únicamente el Bono Compartido Zona 2.\n"
        "\n"

        "FUENTES DE INFORMACIÓN:\n"
        "- [Perfil Usuario BD]: tarifa actual, número de línea, nombre — FUENTE AUTORITARIA.\n"
        "- [Fragmento N]: cláusulas del contrato marco — aplica a todas las tarifas salvo indicación expresa.\n"
        "\n"

        "Si la pregunta pide información de otra persona o cliente, responde que no puedes ayudar con datos de terceros. "
        "Si la respuesta no está en el contexto, indícalo claramente en lugar de inferir o inventar."
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
    response_language: str = "es",
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
    response_language = _normalize_response_language(response_language)

    if _is_third_party_request(cleaned_question, username=username, user_display_name=user_display_name):
        return {
            "question": cleaned_question,
            "chunks": [],
            "context": "",
            "answer": _third_party_block_message(response_language),
            "username": username,
            "user_display_name": user_display_name,
            "blocked": True,
            "response_language": response_language,
        }

    if username and _is_tariff_question(cleaned_question):
        return _build_tariff_answer_from_postgres(
            username=username,
            question=cleaned_question,
            response_language=response_language,
        )

    if username and _is_personal_account_question(cleaned_question):
        return _build_profile_answer(
            username=username,
            question=cleaned_question,
            response_language=response_language,
        )

    rag_question = _enrich_roaming_query(cleaned_question)
    chunks = search_azure(rag_question)
    context = build_context(chunks)

    profile_row = _fetch_user_profile_from_postgres(username=username)
    profile_context = _build_user_profile_context_from_postgres(username=username, row=profile_row)
    if not profile_context:
        profile_context = _build_user_profile_context_from_index(username=username)
    if profile_context:
        context = f"{profile_context}\n\n{context}" if context else profile_context

    context = _inject_fair_use_context(cleaned_question, context)
    answer = generate_answer(
        cleaned_question,
        context,
        response_language=response_language,
    )

    return {
        "question": cleaned_question,
        "chunks": chunks,
        "context": context,
        "answer": answer,
        "username": username,
        "user_display_name": user_display_name,
        "blocked": False,
        "source": "postgres" if profile_row else "azure_search",
        "response_language": response_language,
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
