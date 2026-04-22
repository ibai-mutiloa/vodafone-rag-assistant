# Changelog: User Integration en API RAG

## Resumen de cambios
La API RAG ha sido actualizada para recibir y procesar información del usuario desde el frontend (PHP + JS). Esto permite rastrear quién realiza cada pregunta y potencialmente filtrar documentación por usuario.

---

## Cambios en `api.py`

### 1. Modelo `AskRequest` actualizado
**Antes:**
```python
class AskRequest(BaseModel):
    question: str
```

**Después:**
```python
class AskRequest(BaseModel):
    question: str
    username: str = None  # Usuario que realiza la pregunta
    user_display_name: str = None  # Nombre visible del usuario
```

**Impacto:** Ahora el endpoint `/ask` acepta tres campos en el JSON:
- `question` (requerido): La pregunta del usuario
- `username` (opcional): Identificador único del usuario (ej: "juan.perez")
- `user_display_name` (opcional): Nombre visible para UI (ej: "Juan Pérez")

### 2. Endpoint `/ask` actualizado
**Cambios:**
- Extrae `username` y `user_display_name` del payload
- Los limpia con `.strip()`
- Los pasa a la función `rag()`
- Los incluye en el JSON de respuesta

**Ejemplo de request:**
```json
{
  "question": "¿Cuál es la duración del contrato?",
  "username": "juan.perez",
  "user_display_name": "Juan Pérez"
}
```

**Ejemplo de response:**
```json
{
  "question": "¿Cuál es la duración del contrato?",
  "answer": "...",
  "chunks": [...],
  "username": "juan.perez"
}
```

---

## Cambios en `rag_vodafone.py`

### 1. Función `search_azure()` actualizada
**Antes:**
```python
def search_azure(question: str, top_k: int = TOP_K) -> List[str]:
```

**Después:**
```python
def search_azure(question: str, username: str = None, top_k: int = TOP_K) -> List[str]:
```

**Cambios:**
- Acepta parámetro `username` opcional
- Incluye comentario sobre filtrado por usuario (deshabilitado por defecto)
- Preparado para filtrar resultados cuando el índice Azure tenga un campo de usuario

**Nota:** El filtrado está comentado. Para habilitarlo, descomenta esta línea si tu índice tiene un campo `user` o `username`:
```python
# payload["filter"] = f"user eq '{username}' or access eq 'public'"
```

### 2. Función `generate_answer()` actualizada
**Antes:**
```python
def generate_answer(question: str, context: str) -> str:
```

**Después:**
```python
def generate_answer(question: str, context: str, username: str = None, user_display_name: str = None) -> str:
```

**Cambios:**
- Acepta parámetros `username` y `user_display_name`
- Incluye información del usuario en el prompt si están disponibles
- El modelo GPT-4o ahora recibe: `[Usuario: Juan Pérez]` en el contexto

**Ejemplo de prompt generado:**
```
Pregunta del usuario:
[Usuario: Juan Pérez]
¿Cuál es la duración del contrato?

Contexto recuperado:
[Fragmento 1]
...
```

### 3. Función `rag()` actualizada
**Antes:**
```python
def rag(question: str) -> Dict[str, object]:
```

**Después:**
```python
def rag(question: str, username: str = None, user_display_name: str = None) -> Dict[str, object]:
```

**Cambios:**
- Acepta parámetros `username` y `user_display_name`
- Los pasa a `search_azure()` para filtrado opcional
- Los pasa a `generate_answer()` para contexto del modelo
- Los incluye en el diccionario de retorno

**Retorno:**
```python
{
    "question": question,
    "chunks": chunks,
    "context": context,
    "answer": answer,
    "username": username,
    "user_display_name": user_display_name,
}
```

### 4. Sección `__main__` actualizada
**Cambios:**
- Permite entrada interactiva de `username` y `user_display_name` cuando se ejecuta como script
- Muestra la información del usuario en la salida si está disponible

---

## Validación esperada (Test Checklist)

### ✅ Test 1: Payload completo
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuál es la duración del contrato?",
    "username": "juan.perez",
    "user_display_name": "Juan Pérez"
  }'
```

**Validación:**
- [ ] Response contiene `"username": "juan.perez"`
- [ ] Response contiene respuesta en `"answer"`
- [ ] Response contiene chunks en `"chunks"`

### ✅ Test 2: Sin usuario
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuál es la duración del contrato?"
  }'
```

**Validación:**
- [ ] Response contiene `"username": null` o no incluye el campo
- [ ] Response sigue mostrando respuesta correctamente

### ✅ Test 3: Username pero sin display_name
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuál es la duración del contrato?",
    "username": "juan.perez"
  }'
```

**Validación:**
- [ ] Response contiene `"username": "juan.perez"`
- [ ] La respuesta del modelo muestra `[Usuario: juan.perez]`

### ✅ Test 4: Ejecución manual (CLI)
```bash
cd /home/administrador/vodafone
source .venv/bin/activate
python rag_vodafone.py
```

**Validación:**
- [ ] Permite entrada de pregunta
- [ ] Permite entrada de username (opcional)
- [ ] Permite entrada de user_display_name (opcional)
- [ ] Muestra respuesta completa
- [ ] Muestra información del usuario si fue proporcionada

---

## Impacto en el flujo actual

```
Frontend (PHP + JS)
    ↓
    Resuelve usuario (normalize_proxy_user_name)
    ↓
    Extrae: username, user_display_name
    ↓
    Envía JSON con: question, username, user_display_name
    ↓
API /ask (api.py)
    ↓
    Recibe y valida parámetros
    ↓
    Función rag() (rag_vodafone.py)
    ↓
    search_azure() - búsqueda (+ filtrado opcional por usuario)
    ↓
    generate_answer() - genera respuesta (incluye contexto de usuario)
    ↓
    Retorna respuesta con username
    ↓
Frontend recibe y muestra respuesta
```

---

## Configuración futura (Opcional)

### Para habilitar filtrado por usuario en Azure Search:

Si tu índice de Azure AI Search tiene un campo `user` o `username`:

**Edita `rag_vodafone.py` línea ~205:**
```python
# Descomenta esta línea:
payload["filter"] = f"user eq '{username}' or access eq 'public'"
```

Esto permitirá:
- Usuarios vean SOLO sus documentos + documentos públicos
- Documentos privados de otros usuarios se filteren automáticamente

---

## Notas de seguridad

⚠️ **IMPORTANTE:**
- El campo `username` se recibe del frontend y se usa internamente
- No hay validación de permisos en la API RAG (la responsabilidad es del frontend)
- Si usas filtrado en Azure Search, verifica que el índice esté configurado correctamente
- Los usernames se pasan al modelo GPT-4o en el prompt

---

## Compatibilidad hacia atrás

✅ **Completamente compatible**
- Si no se envía `username` ni `user_display_name`, funciona igual que antes
- Todos los parámetros son opcionales
- No rompe la funcionalidad existente del chat

---

## Próximos pasos

1. **Validar** con el frontend PHP que envía los datos correctamente
2. **Monitorear** logs para confirmar que username llega correctamente
3. **Configurar** filtrado en Azure Search si es necesario
4. **Auditar** quién hace qué preguntas (logs futuros)
