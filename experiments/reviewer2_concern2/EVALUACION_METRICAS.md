# Evaluación de las tres selecciones

El evaluador `evaluate_metrics.py` está preparado. No usa Ollama, no modifica predicciones ni archivos de generación y no regenera la selección 42. Los cálculos semánticos de 44/46 se lanzan manualmente cuando termine la generación; comparten recursos con Ollama, por lo que conviene esperar a que la GPU esté libre.

## Comandos desde la raíz del proyecto

Validar un bloque terminado, sin calcular métricas ni cargar modelos:

```powershell
.\.venv\Scripts\python.exe .\experiments\reviewer2_concern2\evaluate_metrics.py --seed 44 --model llama --dataset cochrane
```

Evaluar ese bloque con el entorno de evaluación existente:

```powershell
.\.venv-eval\Scripts\python.exe -u .\experiments\reviewer2_concern2\evaluate_metrics.py --seed 44 --model llama --dataset cochrane --execute
```

Cambiar a semilla 46, modelo mixtral o el dataset correspondiente. Omitir `--dataset` exige que estén completas las 18 configuraciones del modelo/semilla; omitir también `--model` exige las 36. Si falta un certificado de finalización, el evaluador se detiene antes de abrir esa predicción. Se comprueban hashes, número y orden de filas, fuentes y referencias. No elimina salidas vacías ni limitadas a 512 tokens.

La selección 42 se incorpora mediante sus cinco métricas por ítem ya guardadas y verificadas; BLEU se recalcula sobre el corpus completo. Esta incorporación no carga BERTScore ni MeaningBERT. El comando es:

```powershell
.\.venv-eval\Scripts\python.exe .\experiments\reviewer2_concern2\evaluate_metrics.py --seed 42 --execute
```

Una vez evaluadas las tres selecciones de un bloque:

```powershell
.\.venv\Scripts\python.exe .\experiments\reviewer2_concern2\evaluate_metrics.py --summarize --model llama --dataset cochrane
```

Para resumir todo el estudio, omitir ambos filtros. El resumen exige las tres semillas completas y comprobadas: nunca calcula una desviación con solo una o dos selecciones.

## Resultados

- `evaluation/metrics/{modelo}/seed_{semilla}/{dataset}_{prompt}_{estrategia}_items.csv`: SARI, BERTScore-F1, MeaningBERT, FKGL y FRE por fila, identificadores y referencias usadas. BLEU se guarda como métrica de corpus en el JSON, no como promedio de BLEU por oración.
- JSON del mismo nombre: seis puntuaciones de configuración, número de salidas vacías/capadas, versiones, hashes, firma de SacreBLEU, duración y procedencia.
- `evaluation/metrics/summaries/*_seed_42.csv` (o 44/46): tabla del bloque evaluado.
- `evaluation/metrics/summaries/*_per_seed.csv`: configuraciones de las tres selecciones.
- `evaluation/metrics/summaries/*_mean_sd.csv`: una fila por condición/métrica, puntuaciones 42/44/46, media, desviación muestral (`ddof=1`), mínimo y máximo.

Los checkpoints completos se reutilizan únicamente si coinciden entradas, código, versiones y hash del CSV de métricas. Si cambian, se detiene para revisar; no reemplaza silenciosamente un resultado previo.

## Comparabilidad

Se reutilizan las funciones de `eval_utils.py` y el entorno fijado en `focused_metric_runtime.py`. MeaningBERT conserva su implementación original validada y se compara con la fuente; BERTScore usa roberta-large sin reescalar. Se trabaja offline con la caché existente. TSAR usa A2 y B1 conjuntamente, conservando el orden de las predicciones. SARI es la implementación estándar, sin alternativa legacy.

Para reproducir las tablas originales, las cinco métricas por ítem conservan su redondeo histórico (dos decimales; BERTScore cuatro) y se promedian sin redondear de nuevo. La misma regla se aplica a 44/46. BLEU se calcula mediante SacreBLEU de corpus y se conserva sin redondear. BERTScore permanece en escala 0–1; multiplicarlo por 100 solo al presentar, también para su desviación estándar.

La variación entre tres selecciones es descriptiva. No se añaden pruebas estadísticas ni se duplican zero-shot/few-metric. El análisis conjunto y los contrastes corresponden al siguiente paso, todavía pendiente. Los descriptores se calculan por separado con `evaluate_descriptors.py`.
