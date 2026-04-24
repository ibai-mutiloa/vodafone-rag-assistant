# ⚙️ CONFIGURACIÓN - Suite RAGAS

## 🔧 URL de la API

Por defecto, los scripts de testing están configurados para usar:

```
http://localhost:5001
```

Esto corresponde a tu servicio systemd `rag-vodafone.service` que ya está corriendo.

### ✅ Tu Configuración Actual

- **Puerto**: 5001
- **Host**: localhost
- **Usuario systemd**: administrador
- **Working Directory**: /home/administrador/vodafone
- **Service**: rag-vodafone.service

### 📊 Verificar que el servicio está corriendo

```bash
# Revisar estado
sudo systemctl status rag-vodafone

# Ver logs
sudo journalctl -u rag-vodafone -f

# Iniciar servicio
sudo systemctl start rag-vodafone

# Detener servicio
sudo systemctl stop rag-vodafone

# Reiniciar servicio
sudo systemctl restart rag-vodafone

# Verificar health del API
curl http://localhost:5001/health
```

## 🌍 Cambiar URL de la API (si es necesario)

Si por alguna razón quieres usar otra URL o puerto:

### Opción 1: Variable de Entorno
```bash
export API_BASE_URL="http://otra.url:9000"
python simple_test.py
```

### Opción 2: Editar el script
```bash
# En simple_test.py o run_ragas_test.py, cambiar:
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5001")

# Por:
API_BASE_URL = os.getenv("API_BASE_URL", "http://tu.nueva.url:puerto")
```

### Opción 3: Con make
```bash
# Temporal para una ejecución
API_BASE_URL="http://otra.url:9000" make test
```

## 📋 Archivos de Configuración

### Variables de Entorno API (`/home/administrador/vodafone/.env`)
```bash
# Asegúrate que tiene todas estas variables:
AZURE_SEARCH_ENDPOINT=...
AZURE_SEARCH_API_KEY=...
AZURE_SEARCH_INDEX_NAME=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=...
# etc...
```

### Servicio systemd (`/home/administrador/vodafone/rag-vodafone.service`)
```ini
[Unit]
Description=Vodafone RAG FastAPI Service
After=network.target

[Service]
Type=simple
User=administrador
WorkingDirectory=/home/administrador/vodafone
EnvironmentFile=/home/administrador/vodafone/.env
ExecStart=/home/administrador/vodafone/.venv/bin/python -m uvicorn api:app --host 0.0.0.0 --port 5001 --timeout-keep-alive 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 🔐 Permisos del Servicio

Si necesitas instalar/actualizar el servicio:

```bash
# Copiar servicio a directorio systemd
sudo cp /home/administrador/vodafone/rag-vodafone.service /etc/systemd/system/

# Recargar daemon
sudo systemctl daemon-reload

# Habilitar servicio (inicia con el sistema)
sudo systemctl enable rag-vodafone

# Iniciar servicio
sudo systemctl start rag-vodafone
```

## 🧪 Test de Conectividad

Verificar que la API responde correctamente:

```bash
# Health check simple
curl http://localhost:5001/health

# Respuesta esperada:
# {"status":"ok"}

# Test completo con pregunta
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuál es la duración del contrato?",
    "username": "test_user",
    "response_language": "es"
  }'
```

## 🚀 Flujo de Uso Correcto

1. **Verificar que el servicio está corriendo:**
   ```bash
   curl http://localhost:5001/health
   ```

2. **Ejecutar los tests:**
   ```bash
   cd /home/administrador/vodafone/testeos
   make test
   ```

3. **Ver resultados:**
   ```bash
   make view-detailed
   ```

## 🐛 Troubleshooting

### ❌ Error: "Connection refused"
```bash
# Verificar estado del servicio
sudo systemctl status rag-vodafone

# Si no está corriendo, iniciar
sudo systemctl start rag-vodafone

# Ver logs
sudo journalctl -u rag-vodafone -f
```

### ❌ Error: "Port already in use"
```bash
# Ver qué está usando el puerto
sudo lsof -i :5001

# Cambiar puerto en servicio y volver a iniciar
```

### ❌ Error: "Permission denied"
```bash
# Asegúrate que el usuario administrador tiene permisos
sudo chown -R administrador:administrador /home/administrador/vodafone
```

## ✅ Resumen

Tu setup está optimizado:
- ✅ API corriendo en puerto 5001 con systemd
- ✅ Tests configurados para usar puerto 5001
- ✅ Logs persistentes con journalctl
- ✅ Auto-restart en caso de fallo
- ✅ Ambiente de producción

**No necesitas hacer nada más.** Solo ejecuta:
```bash
cd /home/administrador/vodafone/testeos && make test
```
