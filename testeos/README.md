# 🧪 RAGAS Test Suite - Vodafone RAG API

Suite de pruebas RAGAS para evaluar la calidad del sistema RAG de Vodafone.

## 📋 Estructura

```
testeos/
├── test_data.csv              # Datos de prueba con 10 preguntas y ground truth
├── simple_test.py             # Script de prueba simplificado (sin RAGAS)
├── run_ragas_test.py          # Script completo con métricas RAGAS
├── requirements_ragas.txt     # Dependencias adicionales
├── results/                   # Directorio con resultados
│   ├── test_results_*.json    # Resultados en JSON
│   ├── test_results_*.csv     # Resultados en CSV
│   └── evaluation_results.json # Métricas RAGAS detalladas
└── README.md                  # Este archivo
```

## 🚀 Instalación

### 1. Instalar dependencias RAGAS (opcional, solo si usas run_ragas_test.py)

```bash
cd /home/administrador/vodafone
pip install -r testeos/requirements_ragas.txt
```

### 2. Asegurar que la API está corriendo en puerto 5001

Tu API ya está configurada para correr en `http://localhost:5001` a través del servicio systemd.

Verifica que está corriendo:
```bash
curl http://localhost:5001/health
sudo systemctl status rag-vodafone
```

Para más detalles de configuración, ver [CONFIGURACION.md](CONFIGURACION.md)

## 📊 Ejecutar Tests

### Opción 1: Test Simplificado (Recomendado para empezar)

Genera un reporte CSV con las respuestas de la API comparadas con el ground truth:

```bash
cd /home/administrador/vodafone/testeos
python simple_test.py
```

Esto creará:
- `results/test_results_YYYYMMDD_HHMMSS.json` - Resultados completos en JSON
- `results/test_results_YYYYMMDD_HHMMSS.csv` - Resultados en CSV

### Opción 2: Test Completo con RAGAS

Ejecuta evaluación completa con métricas RAGAS:

```bash
cd /home/administrador/vodafone/testeos
python run_ragas_test.py
```

## 📈 Métricas RAGAS

El framework RAGAS evalúa los siguientes aspectos:

| Métrica | Descripción |
|---------|-------------|
| **Answer Relevancy** | ¿Qué tan relevante es la respuesta a la pregunta del usuario? |
| **Faithfulness** | ¿La respuesta es fiel al contexto recuperado sin alucinar? |
| **Context Precision** | ¿Qué porcentaje del contexto recuperado es relevante? |
| **Context Recall** | ¿El contexto contiene toda la información necesaria para responder? |

## 📝 Datos de Prueba

El archivo `test_data.csv` contiene 10 preguntas sobre contratos Vodafone con sus respuestas esperadas (ground truth):

1. Duración y fechas del contrato
2. Tarifas durante negociaciones post-contrato
3. Límites de datos para Infinity Business Total
4. Beneficio de Datos Compartidos Nacional
5. Esquema de tarificación de llamadas
6. Nivel de disponibilidad de voz
7. Perfiles de autorización para firmar
8. Procedimiento de notificación de incidencias
9. Solicitud de aumento de créditos
10. Aplicación de compensaciones

## 📂 Interpretación de Resultados

### JSON Results (`test_results_*.json`)

```json
[
  {
    "id": 1,
    "question": "¿Cuál es la duración total del contrato...?",
    "ground_truth": "El contrato tiene una duración de 24 meses...",
    "api_answer": "[Respuesta de la API]",
    "chunks_count": 3,
    "error": ""
  }
]
```

### CSV Results (`test_results_*.csv`)

Formato tabular para análisis en Excel o similar:
- **id**: Número del test
- **question**: Pregunta realizada
- **ground_truth**: Respuesta esperada
- **api_answer**: Respuesta generada por la API
- **chunks_count**: Número de fragmentos recuperados
- **error**: Cualquier error durante la ejecución

### Evaluation Results (`evaluation_results.json`)

```json
{
  "total_tests": 10,
  "timestamp": "2026-04-24T...",
  "metrics": {
    "Answer Relevancy": 0.8234,
    "Faithfulness": 0.7856,
    "Context Precision": 0.6234,
    "Context Recall": 0.7123
  },
  "detailed_results": [...]
}
```

## 🔧 Configuración

### Variables de Entorno

Puedes configurar:

```bash
export API_BASE_URL="http://localhost:8000"  # URL de la API (default)
```

### Customización de Tests

Para añadir más tests, edita `test_data.csv` con el siguiente formato:

```csv
id,question,ground_truth
11,Tu nueva pregunta aquí,La respuesta esperada aquí
```

## 📋 Checklist de Uso

- [ ] API corriendo en `http://localhost:8000`
- [ ] Variables de entorno configuradas en `.env`
- [ ] Dependencias instaladas
- [ ] Ejecutar `python simple_test.py`
- [ ] Revisar resultados en `results/`
- [ ] Analizar métricas y ajustar si es necesario

## 🐛 Troubleshooting

### Error: "Connection refused"
- Asegúrate de que la API está corriendo: `python -m uvicorn api:app --reload`

### Error: "Missing environment variables"
- Verifica que `.env` contiene todas las variables requeridas (Azure Search, OpenAI, etc.)

### Error al instalar RAGAS
- Intenta con: `pip install ragas==0.1.0 --no-cache-dir`

## 📞 Soporte

Para más información sobre RAGAS: https://docs.ragas.io/
