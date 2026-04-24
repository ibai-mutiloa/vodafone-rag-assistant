# 🚀 QUICK START - RAGAS Test Suite

## 🚀 Inicio Rápido (2 Minutos)

**Importante**: Tu API ya está corriendo en `http://localhost:5001` 🎉

Solo necesitas ejecutar los tests en otra terminal:

```bash
cd /home/administrador/vodafone/testeos
make test
```

¡Eso es! Los resultados aparecerán en unos segundos.

Ejecuta:

```bash
cd /home/administrador/vodafone/testeos
make test
```

## 📊 Que verás

```
100 Test Suite - Vodafone RAG API
=====================================

📥 Loading test data from testeos/test_data.csv...
✅ Loaded 10 test cases

📞 Calling API for each test case...

[1/10] Processing: ¿Cuál es la duración total del contrato...
[2/10] Processing: ¿Qué sucede con las tarifas si el...
...
[10/10] Processing: ¿Cómo se aplican las compensaciones...

💾 JSON results saved to: testeos/results/test_results_20260424_120530.json
📊 CSV results saved to: testeos/results/test_results_20260424_120530.csv

=====================================
Test Summary Report
=====================================

Total Tests: 10
✅ Successful: 10
❌ Failed: 0
📚 Average chunks retrieved: 2.5

[Test 1] ¿Cuál es la duración...
...
```

## 📂 Resultados

Los resultados se guardan automáticamente en:
```
testeos/
└── results/
    ├── test_results_YYYYMMDD_HHMMSS.json    # Completo en JSON
    ├── test_results_YYYYMMDD_HHMMSS.csv     # En CSV para Excel
    └── evaluation_results.json               # Métricas RAGAS
```

## 🔍 Ver Resultados

```bash
# Ver resumen
cd testeos
python view_results.py

# Ver todos los detalles
python view_results.py --detailed

# Modo interactivo
python view_results.py --interactive
```

O con make:
```bash
make view              # Resumen
make view-detailed     # Todos los detalles
make view-interactive  # Interactivo
```

## 📝 Estructura de Archivos

```
testeos/
├── test_data.csv                  ← Datos de prueba (10 preguntas)
├── simple_test.py                 ← Script principal de tests
├── run_ragas_test.py              ← Tests con métricas RAGAS
├── view_results.py                ← Visualizador de resultados
├── run_tests.sh                   ← Script bash para ejecutar
├── Makefile                       ← Automatización con make
├── README.md                      ← Documentación completa
├── INTERPRETACION_RESULTADOS.md   ← Guía de análisis
├── QUICK_START.md                 ← Este archivo
├── requirements_ragas.txt         ← Dependencias (opcional)
└── results/                       ← Resultados de tests
    └── (generados automáticamente)
```

## 🎯 Opciones Disponibles

### Con make (Recomendado)
```bash
cd testeos

make help              # Ver todas las opciones
make test              # Ejecutar tests
make test-simple       # Tests sin RAGAS
make test-ragas        # Tests completo con RAGAS
make view              # Ver resultados
make view-detailed     # Ver detalles
make api               # Arranca la API
make clean             # Limpiar resultados
make install-deps      # Instalar dependencias RAGAS
```

### Con scripts directos
```bash
cd testeos

# Tests simple
python simple_test.py

# Tests con RAGAS
python run_ragas_test.py

# Ver resultados
python view_results.py
python view_results.py --detailed
python view_results.py --interactive

# Script automático
bash run_tests.sh
```

## 🔧 Troubleshooting

### ❌ Error: "Connection refused"
```bash
# Verifica que la API está corriendo
curl http://localhost:8000/health

# Si no, arranca la API
cd /home/administrador/vodafone
python -m uvicorn api:app --reload
```

### ❌ Error: "Missing environment variables"
```bash
# Verifica el .env
cat /home/administrador/vodafone/.env

# Asegúrate que tiene:
# - AZURE_SEARCH_ENDPOINT
# - AZURE_SEARCH_API_KEY
# - AZURE_SEARCH_INDEX_NAME
# - AZURE_OPENAI_ENDPOINT
# - AZURE_OPENAI_API_KEY
# - AZURE_OPENAI_DEPLOYMENT
```

### ❌ Error: "ModuleNotFoundError: No module named 'ragas'"
```bash
# Instala las dependencias RAGAS
pip install -r testeos/requirements_ragas.txt

# O con make
cd testeos && make install-deps
```

## 📈 Próximos Pasos

1. ✅ **Ejecuta los tests**: `make test`
2. 📊 **Revisa los resultados**: `make view`
3. 📖 **Lee la guía de interpretación**: [INTERPRETACION_RESULTADOS.md](INTERPRETACION_RESULTADOS.md)
4. 🔄 **Itera si es necesario**: Ajusta configuración y repite

## 📞 Soporte

- 📖 Documentación completa: [README.md](README.md)
- 📊 Análisis de resultados: [INTERPRETACION_RESULTADOS.md](INTERPRETACION_RESULTADOS.md)
- 🐛 Issues: Revisa logs en `testeos/results/`

## ✨ Tips

- Siempre ejecuta `make test` primero (es más rápido)
- Los resultados se guardan automáticamente en `testeos/results/`
- Puedes comparar múltiples ejecuciones revisando todos los archivos JSON
- Usa `make view-detailed` para análisis profundo

---

**¡Listo para empezar!** 🎉

Ejecuta en una terminal:
```bash
cd /home/administrador/vodafone/testeos && make test
```

Tu API ya está corriendo en puerto 5001 ✅
