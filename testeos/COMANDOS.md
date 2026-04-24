# 🎯 Comandos Disponibles - RAGAS Test Suite

## 📋 Índice Rápido

- [Ejecutar Tests](#ejecutar-tests)
- [Ver Resultados](#ver-resultados)
- [Gestión](#gestión)
- [Desarrollo](#desarrollo)

---

## 🧪 Ejecutar Tests

### Opción 1: Make (Recomendado)
```bash
cd /home/administrador/vodafone/testeos
make test              # Ejecutar tests + ver resumen
```

### Opción 2: Python directo
```bash
cd /home/administrador/vodafone/testeos
python simple_test.py  # Tests sin RAGAS (rápido)
```

### Opción 3: Script bash
```bash
/home/administrador/vodafone/testeos/run_tests.sh
```

### Opción 4: Tests completos con RAGAS
```bash
cd /home/administrador/vodafone/testeos
python run_ragas_test.py  # Completo (más lento)
```

---

## 📊 Ver Resultados

### Resumen rápido
```bash
cd /home/administrador/vodafone/testeos
make view                    # O:
python view_results.py
```

### Ver todos los detalles
```bash
cd /home/administrador/vodafone/testeos
make view-detailed           # O:
python view_results.py --detailed
```

### Modo interactivo
```bash
cd /home/administrador/vodafone/testeos
make view-interactive        # O:
python view_results.py --interactive
```

### Listar archivos de resultados
```bash
cd /home/administrador/vodafone/testeos
make results                 # O:
ls -lh results/
```

---

## 🔧 Gestión

### Instalar dependencias RAGAS (opcional)
```bash
cd /home/administrador/vodafone/testeos
make install-deps    # O:
pip install -r requirements_ragas.txt
```

### Limpiar resultados
```bash
cd /home/administrador/vodafone/testeos
make clean          # O:
rm -rf results/*
```

### Mostrar ayuda
```bash
cd /home/administrador/vodafone/testeos
make help           # O:
make                # Sin argumentos también muestra ayuda
```

---

## 🚀 Servidor

### Arrancar API
```bash
cd /home/administrador/vodafone
make api              # O:
python -m uvicorn api:app --reload

# Con opciones personalizadas
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Verificar que la API funciona
```bash
curl http://localhost:8000/health

# Respuesta esperada:
# {"status":"ok"}
```

### Hacer una prueba manual
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Cuál es la duración del contrato?"}'
```

---

## 🛠️ Desarrollo

### Ver el código de tests
```bash
cd /home/administrador/vodafone/testeos
cat simple_test.py    # Tests simples
cat run_ragas_test.py # Tests completos
cat view_results.py   # Visualizador
```

### Editar datos de prueba
```bash
# Abrir en editor
nano /home/administrador/vodafone/testeos/test_data.csv

# O en VS Code
code /home/administrador/vodafone/testeos/test_data.csv
```

### Ver logs detallados
```bash
cd /home/administrador/vodafone/testeos
tail -f results/test_results_*.json  # Ver último resultado en tiempo real
```

---

## 📚 Archivos Generados

Después de ejecutar los tests, encontrarás en `testeos/results/`:

```
results/
├── test_results_20260424_120530.json      # Resultados completos en JSON
├── test_results_20260424_120530.csv       # Resultados en CSV para Excel
└── evaluation_results.json                # Métricas RAGAS
```

### Estructura JSON
```json
[
  {
    "id": 1,
    "question": "¿Cuál es la duración...",
    "ground_truth": "El contrato tiene...",
    "api_answer": "[Respuesta generada]",
    "chunks_count": 3,
    "error": ""
  },
  ...
]
```

### Estructura CSV
```csv
id,question,ground_truth,api_answer,chunks_count,error
1,¿Cuál es la duración...,"El contrato tiene...","[Respuesta]",3,
...
```

---

## 🔄 Flujo Recomendado

### Primera ejecución (setup)
```bash
# Terminal 1: Arranca la API
cd /home/administrador/vodafone
python -m uvicorn api:app --reload

# Terminal 2: Ejecuta tests (espera 2-3 segundos)
cd /home/administrador/vodafone/testeos
make test
```

### Iteraciones posteriores
```bash
# Para volver a ejecutar
make test          # Tests + resumen

# Para analizar en profundidad
make view-detailed
```

### Para comparar múltiples ejecuciones
```bash
# Los resultados se guardan con timestamp
ls -lh testeos/results/

# Comparar manualmente
diff testeos/results/test_results_old.json testeos/results/test_results_new.json
```

---

## 🐛 Troubleshooting Commands

### Verificar salud del API
```bash
curl http://localhost:8000/health
```

### Ver logs de la API (si está en background)
```bash
# Buscar procesos Python corriendo
ps aux | grep uvicorn

# Matar si es necesario
pkill -f "uvicorn"
```

### Ver variables de entorno
```bash
cd /home/administrador/vodafone
grep -E "^AZURE_" .env
```

### Validar configuración
```bash
cd /home/administrador/vodafone
python -c "from rag_vodafone import _validate_config; _validate_config(); print('✅ Configuración OK')"
```

---

## 🎯 Automatización

### Ejecutar tests cada hora
```bash
# Linux/Mac
(crontab -l 2>/dev/null; echo "0 * * * * cd /home/administrador/vodafone/testeos && python simple_test.py >> tests.log 2>&1") | crontab -

# Verificar
crontab -l | grep simple_test
```

### Script para ejecutar y guardar resultados
```bash
#!/bin/bash
cd /home/administrador/vodafone/testeos
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
python simple_test.py | tee "logs/test_$TIMESTAMP.log"
cp results/test_results_*.json "results/archived/test_$TIMESTAMP.json"
```

---

## 📖 Documentación

- [README.md](README.md) - Documentación completa
- [QUICK_START.md](QUICK_START.md) - Inicio rápido
- [INTERPRETACION_RESULTADOS.md](INTERPRETACION_RESULTADOS.md) - Cómo analizar resultados

---

## 💡 Tips Pro

1. **Usa `make` siempre que sea posible** - Automatiza todo
2. **Guarda los resultados** - Compara ejecuciones a lo largo del tiempo
3. **Verifica `--detailed`** - Para análisis profundo
4. **Usa `view_results.py --interactive`** - Para navegar resultados
5. **Lee `INTERPRETACION_RESULTADOS.md`** - Antes de hacer cambios

---

¿Necesitas ayuda? Revisa la [documentación completa](README.md) 📚
