# Validación Cruzada: Frontend ↔ API RAG

## 🔄 Flujo Completo

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  FRONTEND (PHP + JS)                                        │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  1. Usuario escribe pregunta en el formulario               │
│  2. askRag(question) se invoca                              │
│  3. resolveUserName() obtiene usuario de:                   │
│     - cookie intranetUser                                   │
│     - HTTP_X_MS_CLIENT_PRINCIPAL_NAME                       │
│     - REMOTE_USER                                           │
│     - AUTH_USER                                             │
│  4. normalizeUserDisplayName() formatea el nombre           │
│  5. Crea payload JSON:                                      │
│     {                                                       │
│       "question": string,                                   │
│       "username": string (opcional),                        │
│       "user_display_name": string (opcional)                │
│     }                                                       │
│  6. Envía POST a ask-proxy.asp                              │
│                                                             │
│                          ↓↓↓↓↓↓                             │
│                        HTTP POST                            │
│                          ↓↓↓↓↓↓                             │
│                                                             │
│  API RAG (Python FastAPI)                                   │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  1. Endpoint /ask recibe POST                               │
│  2. AskRequest valida payload:                              │
│     - question (requerido)                                  │
│     - username (opcional)                                   │
│     - user_display_name (opcional)                          │
│  3. Limpia valores con .strip()                             │
│  4. Llama rag(question, username, user_display_name)        │
│  5. search_azure() busca con usuario opcional               │
│  6. generate_answer() genera respuesta (incluye usuario)     │
│  7. Retorna JSON:                                           │
│     {                                                       │
│       "question": string,                                   │
│       "answer": string,                                     │
│       "chunks": array,                                      │
│       "username": string                                    │
│     }                                                       │
│                          ↓↓↓↓↓↓                             │
│                        HTTP 200                             │
│                          ↓↓↓↓↓↓                             │
│                                                             │
│  FRONTEND (PHP + JS)                                        │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  1. Recibe response JSON                                    │
│  2. Muestra answer en el chat                               │
│  3. Conoce username para auditoría/logs                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Compatibilidad Punto por Punto

### Función Frontend: `askRag(question)`

```javascript
async function askRag(question) {
    var endpoint = 'ask-proxy.asp';
    var requestUserName = resolveUserName();
    var payload = { question: question };

    if (requestUserName) {
        userName = requestUserName;
        payload.username = requestUserName;
        payload.user_display_name = normalizeUserDisplayName(requestUserName);
    }
    
    // ... send to API ...
}
```

**Mapeo con API:**

| Frontend | API | Estado |
|----------|-----|--------|
| `question` | `AskRequest.question` | ✅ Requerido |
| `requestUserName` → `payload.username` | `AskRequest.username` | ✅ Opcional |
| `normalizeUserDisplayName(requestUserName)` → `payload.user_display_name` | `AskRequest.user_display_name` | ✅ Opcional |

---

### Endpoint API: POST `/ask`

```python
@app.post("/ask")
def ask(payload: AskRequest) -> dict:
    question = payload.question.strip()
    username = (payload.username or "").strip()
    user_display_name = (payload.user_display_name or "").strip()
    
    result = rag(
        question=question,
        username=username,
        user_display_name=user_display_name,
    )
    
    return {
        "question": result.get("question", question),
        "answer": result.get("answer", ""),
        "chunks": result.get("chunks", []),
        "username": result.get("username", username),
    }
```

**Validación:**

- ✅ Acepta `question` (requerido)
- ✅ Acepta `username` (opcional)
- ✅ Acepta `user_display_name` (opcional)
- ✅ Retorna `username` en respuesta

---

## 📊 Casos de Prueba

### Caso 1: Usuario Identificado

**Frontend envía:**
```json
{
  "question": "¿Cuál es la duración del contrato?",
  "username": "juan.perez",
  "user_display_name": "Juan Pérez"
}
```

**API retorna:**
```json
{
  "question": "¿Cuál es la duración del contrato?",
  "answer": "La duración típica es de 2 años...",
  "chunks": ["Fragmento 1...", "Fragmento 2..."],
  "username": "juan.perez"
}
```

**Validación:**
- ✅ Username en request
- ✅ Username en response
- ✅ Modelo sabe quién hace la pregunta

---

### Caso 2: Usuario No Identificado

**Frontend envía:**
```json
{
  "question": "¿Cuál es la duración del contrato?"
}
```

**API retorna:**
```json
{
  "question": "¿Cuál es la duración del contrato?",
  "answer": "La duración típica es de 2 años...",
  "chunks": ["Fragmento 1...", "Fragmento 2..."],
  "username": null
}
```

**Validación:**
- ✅ Request sin usuario es válido
- ✅ Response retorna null para username
- ✅ No rompe funcionalidad

---

### Caso 3: Solo Username, Sin Display Name

**Frontend envía:**
```json
{
  "question": "¿Cuál es la duración del contrato?",
  "username": "juan.perez"
}
```

**API retorna:**
```json
{
  "question": "¿Cuál es la duración del contrato?",
  "answer": "La duración típica es de 2 años...",
  "chunks": ["Fragmento 1...", "Fragmento 2..."],
  "username": "juan.perez"
}
```

**En el modelo GPT-4o:**
```
Pregunta del usuario:
[Usuario: juan.perez]
¿Cuál es la duración del contrato?
```

**Validación:**
- ✅ Username se usa aún sin display_name
- ✅ Modelo recibe información de usuario

---

## 🔍 Validación de Cambios

### En `api.py`

**Cambio 1:** Modelo `AskRequest` ✅
```python
# ANTES:
class AskRequest(BaseModel):
    question: str

# DESPUÉS:
class AskRequest(BaseModel):
    question: str
    username: str = None
    user_display_name: str = None
```

**Estado:** Compatible con `askRag()`

**Cambio 2:** Endpoint `/ask` ✅
```python
# ANTES:
result = rag(question)

# DESPUÉS:
result = rag(
    question=question,
    username=username,
    user_display_name=user_display_name,
)
```

**Estado:** Pasa todos los parámetros a `rag()`

---

### En `rag_vodafone.py`

**Cambio 1:** Función `search_azure()` ✅
```python
# ANTES:
def search_azure(question: str, top_k: int = TOP_K)

# DESPUÉS:
def search_azure(question: str, username: str = None, top_k: int = TOP_K)
```

**Estado:** Acepta username para filtrado futuro

**Cambio 2:** Función `generate_answer()` ✅
```python
# ANTES:
def generate_answer(question: str, context: str)

# DESPUÉS:
def generate_answer(question: str, context: str, username: str = None, user_display_name: str = None)
```

**Estado:** Incluye usuario en prompt para modelo

**Cambio 3:** Función `rag()` ✅
```python
# ANTES:
def rag(question: str)

# DESPUÉS:
def rag(question: str, username: str = None, user_display_name: str = None)
```

**Estado:** Recibe y propaga usuario a través del pipeline

---

## 🧪 Tests de Integración

### Test 1: Payload Completo
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuál es la duración del contrato?",
    "username": "juan.perez",
    "user_display_name": "Juan Pérez"
  }'
```

**Validaciones:**
- [ ] Response contiene `"username": "juan.perez"`
- [ ] Response contiene respuesta en `"answer"`
- [ ] Response contiene chunks en `"chunks"`

### Test 2: Sin Usuario
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuál es la duración del contrato?"}'
```

**Validaciones:**
- [ ] Response retorna correctamente sin error
- [ ] Username es null o no presente

### Test 3: Health Check
```bash
curl http://localhost:8000/health
```

**Validaciones:**
- [ ] Retorna `{"status": "ok"}`

---

## 📋 Checklist de Validación

### Funcionalidad del Frontend

- [ ] `resolveUserName()` obtiene usuario correctamente
- [ ] `normalizeUserDisplayName()` formatea el nombre
- [ ] `askRag()` crea payload con `question`, `username`, `user_display_name`
- [ ] Payload se envía a `ask-proxy.asp`

### Funcionalidad de la API

- [ ] POST `/ask` recibe payload
- [ ] `AskRequest` valida los campos
- [ ] Campos opcionales se handlean correctamente
- [ ] `rag()` recibe todos los parámetros
- [ ] Response contiene `username`

### End-to-End

- [ ] Frontend → API comunican correctamente
- [ ] Usuario se propaga desde frontend a API
- [ ] API retorna username en response
- [ ] Sin usuario, todo funciona igual
- [ ] No se rompe funcionalidad existente

---

## 🚀 Próximos Pasos

1. **Validar** que `ask-proxy.asp` hace forward correcto a la API
2. **Monitorear** logs para confirmar username llega
3. **Probar** con usuarios reales del sistema
4. **Configurar** filtrado en Azure Search (opcional)
5. **Auditar** logs para saber quién hace qué preguntas

---

## 📝 Notas de Implementación

**✅ Lo que está bien:**
- Frontend `askRag()` está correctamente implementado
- Envía todos los parámetros necesarios
- API está lista para recibirlos
- Backward compatible (funciona sin usuario)

**⚠️ Puntos de atención:**
- `ask-proxy.asp` debe hacer forward correcto del JSON
- Headers `Content-Type: application/json` deben ser preserved
- Los datos de usuario no se validan (responsabilidad del frontend)

**🔐 Seguridad:**
- Username viene del frontend (confiar en frontend)
- No hay verificación de permisos en API RAG
- Filtrado en Azure Search requiere configuración adicional

---

## 📞 Soporte

Si hay problemas:

1. **API no recibe username:** Verificar que `ask-proxy.asp` hace forward
2. **Usuario sale nulo:** Verificar que `resolveUserName()` retorna valor
3. **Error de validación:** Verificar JSON es válido (Content-Type: application/json)
4. **No funciona sin usuario:** Es normal, debe ser compatible

---
