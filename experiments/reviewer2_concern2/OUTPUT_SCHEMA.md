# Datos de generación y evaluación — esquema vigente 3

La generación guarda la fuente, referencia e ID originales, prediction, configuración y los metadatos de simplify_one_ollama: tiempos, tokens de entrada y salida, done_reason, duraciones, velocidades, num_predict y num_ctx. También identifica modelo, dataset, prompt, estrategia, semilla de selección, semilla de generación y parámetros de repetición. Los sidecars conservan parámetros completos, hashes y metadatos reales del modelo y entorno.

No calcula ni añade columnas LEN_COMPLEX, LEN_PRED, LEN_REF, compression_ratio, copy_rate ni detectores de errores durante la generación. Este cambio se realizó antes de iniciar ninguna inferencia de las semillas nuevas. No cambian prompts, muestras, opciones ni los 72 trabajos planificados.

## Evaluación común de indicadores derivados

evaluate_descriptors.py aplica exactamente las mismas reglas a las selecciones 42, 44 y 46, lee las predicciones sin modificarlas y escribe resultados separados en evaluation/descriptors/.

- LEN_COMPLEX/LEN_PRED: palabras separadas por espacios.
- LEN_REF: media de longitudes de las referencias; TSAR usa ambas A2/B1.
- compression_ratio: palabras de salida / palabras de fuente; fuente vacía provoca error explícito.
- copy_rate: fracción de tokens de salida presentes en el conjunto de tokens de fuente, con mayúsculas y puntuación conservadas; salida vacía = 0. Es solapamiento léxico, no fidelidad ni copia de frases.
- references_json: referencias utilizadas en la evaluación, recuperadas del gold para TSAR.
- empty_prediction, reached_generation_limit, too_brief_vs_reference, ended_abruptly, format_related_marker, list_like_format y technical_or_statistical_markers: reglas de cribado existentes. No son etiquetas humanas validadas ni permiten afirmar que los acrónimos estén sin explicar.
- observed_input_plus_512_over_context: presupuesto basado en tokens procesados registrados; no excluye por sí solo un recorte previo.

La semilla 42 se evaluó con este script: 36 configuraciones one/few-random, 4476 filas. Los datos originales permanecen intactos, incluidas sus columnas de métricas y longitud anteriores. La rutina vuelve a calcular los indicadores desde los textos para asegurar definiciones comunes; no copia columnas antiguas como si fueran nuevas comprobaciones.

```powershell
.\.venv\Scripts\python.exe .\experiments\reviewer2_concern2\evaluate_descriptors.py --seed 42
```

Después de completar una etapa nueva puede evaluarse el bloque correspondiente:

```powershell
.\.venv\Scripts\python.exe .\experiments\reviewer2_concern2\evaluate_descriptors.py --seed 44 --model llama --dataset cochrane
```

También se admite --seed 46. Sin filtros, una semilla requiere sus 36 configuraciones completas; el script se detiene si falta alguna, no trata los archivos parciales como evaluaciones completas. Las semillas nuevas requieren el marcador de finalización y hash coincidente. No modificar CSV de predicciones durante la generación.

Cada configuración produce un CSV por fila en evaluation/descriptors/<model>/seed_<seed>/, y el resumen del conjunto solicitado queda en evaluation/descriptors/summaries/, con hashes y verificación de que las predicciones no cambiaron.

## Métricas originales

SARI, BLEU de corpus, BERTScore, MeaningBERT original fijado, FKGL y FRE corresponden a otra fase de evaluación sobre el texto guardado. El script evaluate_descriptors.py NO las calcula ni afirma que las semillas nuevas ya estén evaluadas con ellas. Deben reutilizarse sus implementaciones validadas, conservar TSAR multirreferencia y distinguir BLEU por oración de BLEU de corpus. No hace falta ninguna nueva generación de seed 42 para calcular indicadores adicionales.

La comparación histórica y las erratas de etiquetas corregidas siguen siendo limitaciones de interpretación, no razones para alterar resultados antiguos ni afirmar identidad literal entre todas las condiciones.
