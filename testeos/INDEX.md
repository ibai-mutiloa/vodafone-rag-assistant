# 📑 ÍNDICE - Suite de Tests RAGAS para Vodafone

Bienvenido a la suite de tests RAGAS para validar tu sistema RAG de Vodafone.

## 🚀 Inicio Rápido (1 minuto)

```bash
# Terminal 1: API
cd /home/administrador/vodafone
python -m uvicorn api:app --reload

# Terminal 2: Tests
cd /home/administrador/vodafone/testeos
make test
```

Ver [QUICK_START.md](QUICK_START.md) para más detalles.

---

## 📁 Archivos Principales

### 🧪 Scripts de Tests
- **[simple_test.py](simple_test.py)** - Tests simplificados (recomendado)
- **[run_ragas_test.py](run_ragas_test.py)** - Tests completos con RAGAS
- **[run_tests.sh](run_tests.sh)** - Script bash para ejecutar automáticamente

### 📊 Utilidades
- **[view_results.py](view_results.py)** - Visualizador de resultados
- **[Makefile](Makefile)** - Automatización con make

### 📝 Datos
- **[test_data.csv](test_data.csv)** - 10 preguntas con ground truth

### 📚 Documentación
| Archivo | Contenido |
|---------|-----------|
| [QUICK_START.md](QUICK_START.md) | 👈 **EMPIEZA AQUÍ** - Guía de 5 minutos |
| [README.md](README.md) | Documentación completa del proyecto |
| [COMANDOS.md](COMANDOS.md) | Lista de todos los comandos disponibles |
| [INTERPRETACION_RESULTADOS.md](INTERPRETACION_RESULTADOS.md) | Cómo analizar las métricas RAGAS |
| [INDEX.md](INDEX.md) | Este archivo |

---

## 🎯 Casos de Uso

### 📌 "Quiero hacer una prueba rápida"
```bash
cd testeos && make test
```
👉 Ve a [QUICK_START.md](QUICK_START.md)

### 📌 "Quiero entender los resultados"
- Lee [INTERPRETACION_RESULTADOS.md](INTERPRETACION_RESULTADOS.md)
- Ejecuta `make view-detailed`

### 📌 "Quiero ver todos los comandos disponibles"
👉 Ve a [COMANDOS.md](COMANDOS.md)

### 📌 "Quiero automatizar los tests"
👉 Lee la sección de "Automatización" en [COMANDOS.md](COMANDOS.md)

### 📌 "Quiero entender la arquitectura"
👉 Ve a [README.md](README.md) - Sección "Estructura"

---

## 📊 Flujo de Trabajo Estándar

```
1. Configurar API
   └─ python -m uvicorn api:app --reload

2. Ejecutar Tests
   └─ cd testeos && make test

3. Ver Resultados
   └─ make view-detailed

4. Analizar Métricas
   └─ Leer INTERPRETACION_RESULTADOS.md

5. Iterar (si es necesario)
   └─ Ajustar configuración y volver al paso 2
```

---

## 📈 Que Miden los Tests

Las 10 preguntas evalúan:

1. ✅ **Hechos básicos** - Duración del contrato
2. ✅ **Políticas** - Tarifas post-contrato
3. ✅ **Límites técnicos** - Datos y velocidad
4. ✅ **Beneficios** - Datos compartidos
5. ✅ **Tarificación** - Esquemas de llamadas
6. ✅ **Garantías** - Disponibilidad de red
7. ✅ **Autorización** - Perfiles de firma
8. ✅ **Procesos** - Notificación de incidencias
9. ✅ **Cambios** - Solicitud de aumento
10. ✅ **Compensaciones** - Aplicación de descuentos

---

## 🔍 Estructura del Directorio

```
testeos/
├── INDEX.md                          ← TÚ ESTÁS AQUÍ
├── QUICK_START.md                    ← Guía de 5 minutos
├── README.md                         ← Documentación completa
├── COMANDOS.md                       ← Lista de comandos
├── INTERPRETACION_RESULTADOS.md      ← Análisis de métricas
│
├── Makefile                          ← Automatización
├── simple_test.py                    ← Script principal (recomendado)
├── run_ragas_test.py                 ← Tests con RAGAS
├── run_tests.sh                      ← Script bash
├── view_results.py                   ← Visualizador
│
├── test_data.csv                     ← Datos de prueba
├── requirements_ragas.txt            ← Dependencias
│
└── results/                          ← Resultados (generados)
    ├── test_results_20260424_120530.json
    ├── test_results_20260424_120530.csv
    └── evaluation_results.json
```

---

## 💻 Requisitos

- ✅ Python 3.8+
- ✅ FastAPI (para la API)
- ✅ Azure OpenAI SDK configurado
- ✅ Variables de entorno en `.env`

---

## ⚡ Comandos Clave

```bash
# Ejecutar tests
make test                   # Lo más común

# Ver resultados
make view                   # Resumen
make view-detailed          # Todos los detalles

# Gestión
make api                    # Arrancar API
make clean                  # Limpiar resultados
make help                   # Ver opciones

# Ayuda
make --version              # Ver versión de make
```

---

## 🎓 Primeros Pasos

### Para principiantes:
1. Lee [QUICK_START.md](QUICK_START.md)
2. Ejecuta `make test`
3. Revisa resultados con `make view-detailed`

### Para expertos:
1. Revisa [COMANDOS.md](COMANDOS.md) para opciones avanzadas
2. Lee el código en `simple_test.py` y `run_ragas_test.py`
3. Customiza `test_data.csv` si es necesario

---

## 📞 Soporte

| Pregunta | Respuesta |
|----------|-----------|
| ¿Cómo empiezo? | Lee [QUICK_START.md](QUICK_START.md) |
| ¿Qué significan las métricas? | Lee [INTERPRETACION_RESULTADOS.md](INTERPRETACION_RESULTADOS.md) |
| ¿Qué comandos hay disponibles? | Ve a [COMANDOS.md](COMANDOS.md) |
| ¿Cómo funciona todo? | Lee [README.md](README.md) |

---

## ✨ Características

✅ 10 preguntas de prueba pre-configuradas
✅ Evaluación automática con métricas RAGAS
✅ Generación de reportes en JSON y CSV
✅ Visualización de resultados interactiva
✅ Fácil automatización con make
✅ Documentación completa

---

**¡Listo para empezar?** 🚀

Ejecuta esto en dos terminales:
```bash
# Terminal 1
python -m uvicorn api:app --reload

# Terminal 2  
cd testeos && make test
```

O ve directamente a [QUICK_START.md](QUICK_START.md) ⬇️
