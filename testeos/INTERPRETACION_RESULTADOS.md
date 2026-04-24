# 📊 Guía de Interpretación de Resultados RAGAS

## ¿Qué es RAGAS?

RAGAS (Retrieval Augmented Generation Assessment) es un framework que proporciona métricas cuantitativas para evaluar la calidad de sistemas RAG sin necesidad de anotaciones manuales exhaustivas.

## 📈 Métricas Principales

### 1. **Answer Relevancy** (0.0 - 1.0)
Mide qué tan relevante es la respuesta generada para la pregunta del usuario.

**Interpretación:**
- `> 0.8`: Excelente - La respuesta es muy relevante y directa
- `0.6 - 0.8`: Bueno - La respuesta es relevante pero puede tener información adicional
- `0.4 - 0.6`: Aceptable - La respuesta es parcialmente relevante
- `< 0.4`: Pobre - La respuesta no es muy relevante

**Qué significa:**
- Si es bajo, el modelo puede estar generando respuestas genéricas o no enfocadas
- Puede indicar que el contexto recuperado no fue óptimo

### 2. **Faithfulness** (0.0 - 1.0)
Evalúa si la respuesta es "fiel" al contexto recuperado, sin alucinar ni inventar información.

**Interpretación:**
- `> 0.8`: Excelente - Respuesta bien fundamentada en el contexto
- `0.6 - 0.8`: Bueno - Respuesta con algunas afirmaciones comprobables
- `0.4 - 0.6`: Aceptable - Respuesta parcialmente fundamentada
- `< 0.4`: Pobre - Respuesta contiene alucinaciones

**Qué significa:**
- Score bajo indica que el modelo está generando información no presente en el contexto
- Es la métrica más crítica para sistemas de atención al cliente

### 3. **Context Precision** (0.0 - 1.0)
Porcentaje del contexto recuperado que es realmente relevante para la pregunta.

**Interpretación:**
- `> 0.8`: Excelente - Casi todo el contexto es útil
- `0.6 - 0.8`: Bueno - Mayoría del contexto es relevante
- `0.4 - 0.6`: Aceptable - Aproximadamente la mitad es relevante
- `< 0.4`: Pobre - Contexto recuperado tiene mucho ruido

**Qué significa:**
- Score bajo indica que el motor de búsqueda está trayendo documentos irrelevantes
- Puede necesitar ajuste en índices o estrategia de búsqueda

### 4. **Context Recall** (0.0 - 1.0)
Mide si el contexto recuperado contiene toda la información necesaria para responder la pregunta.

**Interpretación:**
- `> 0.8`: Excelente - Contexto contiene casi toda la información necesaria
- `0.6 - 0.8`: Bueno - Contexto tiene la mayoría de la información
- `0.4 - 0.6`: Aceptable - Contexto tiene información parcial
- `< 0.4`: Pobre - Falta información importante

**Qué significa:**
- Score bajo indica problemas de cobertura en los documentos indexados
- Puede significar que los documentos originales no contienen toda la información

## 🎯 Métricas Compuestas

### RAG Score = (Faithfulness + Answer Relevancy + Context Precision + Context Recall) / 4

Proporciona una puntuación general del sistema.

- `> 0.75`: Sistema excelente
- `0.5 - 0.75`: Sistema aceptable (requiere mejoras)
- `< 0.5`: Sistema deficiente (requiere cambios importantes)

## 🔍 Análisis Específico por Test

Para cada una de las 10 preguntas, debes revisar:

### Test 1: Duración del contrato
- **Métrica crítica**: Faithfulness (debe ser muy alta, es un dato factual)
- **Esperado**: Score alto > 0.85 (es información estructurada)

### Tests 2-5: Detalles técnicos del contrato
- **Métrica crítica**: Context Recall (deben contener la información)
- **Esperado**: Scores moderados a altos (0.6-0.8)

### Tests 6-10: Procedimientos y políticas
- **Métrica crítica**: Answer Relevancy + Faithfulness
- **Esperado**: Scores altos (> 0.75)

## 💡 Recomendaciones por Problema

### Si Faithfulness es baja:
1. Revisar que la API está devolviendo el contexto correcto
2. Validar que los prompts del sistema están bien configurados
3. Revisar los documentos indexados en Azure Search

### Si Context Precision es baja:
1. Revisar la configuración de Azure Search
2. Ajustar estrategia de búsqueda (lexical vs vector)
3. Optimizar el índice y campos de búsqueda

### Si Context Recall es baja:
1. Validar que los documentos contienen la información requerida
2. Revisar la estrategia de chunking/fragmentación
3. Considerar añadir más documentos al índice

### Si Answer Relevancy es baja:
1. Revisar los prompts del sistema
2. Ajustar temperature del modelo (posiblemente demasiado baja)
3. Revisar si el contexto es suficientemente completo

## 📋 Tabla de Diagnóstico

| Síntoma | Causa Probable | Solución |
|---------|----------------|----------|
| Todas las métricas bajas | Sistema no funciona bien | Revisar configuración general |
| Faithfulness baja, otros altos | Alucinaciones del modelo | Revisar prompts o temperature |
| Context Precision baja | Búsqueda imprecisa | Ajustar índice de búsqueda |
| Context Recall baja | Documentos incompletos | Añadir o mejorar documentos |
| Answer Relevancy baja | Respuesta desenfocada | Revisar instrucciones del sistema |

## 🔄 Proceso de Mejora Iterativa

1. **Baseline**: Ejecutar tests y obtener métricas iniciales
2. **Diagnóstico**: Identificar qué métrica(s) son baja(s)
3. **Hipótesis**: Formular por qué esa métrica es baja
4. **Intervención**: Realizar cambio específico
5. **Validación**: Volver a ejecutar tests
6. **Repetir**: Continuar hasta alcanzar objetivos

## 📌 Benchmarks Sugeridos

Para un sistema de atención al cliente Vodafone:

| Métrica | Objetivo Mínimo | Objetivo Óptimo |
|---------|-----------------|-----------------|
| Faithfulness | 0.80 | > 0.90 |
| Answer Relevancy | 0.70 | > 0.85 |
| Context Precision | 0.60 | > 0.80 |
| Context Recall | 0.65 | > 0.85 |
| **RAG Score** | **0.69** | **> 0.85** |

## 🎓 Ejemplo de Análisis

**Pregunta 1: "¿Cuál es la duración total del contrato...?"**

**Resultados esperados:**
```
Ground Truth: "El contrato tiene una duración de 24 meses..."
API Answer: "El contrato tiene una duración de 24 meses..."
Chunks Retrieved: 2
```

**Análisis:**
- Faithfulness: 0.95 (excelente - respuesta fiel al contexto)
- Answer Relevancy: 0.92 (excelente - respuesta muy relevante)
- Context Precision: 0.85 (bueno - ambos chunks son relevantes)
- Context Recall: 0.90 (excelente - contexto contiene toda la info)
- **RAG Score: 0.91 (excelente)**

**Conclusión**: Este test funciona perfecto.

## 📚 Referencias

- Documentación oficial RAGAS: https://docs.ragas.io/
- Paper RAGAS: https://arxiv.org/abs/2309.15217
- Azure AI Search: https://learn.microsoft.com/en-us/azure/search/
- Azure OpenAI: https://learn.microsoft.com/en-us/azure/cognitive-services/openai/
