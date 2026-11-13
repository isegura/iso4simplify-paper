# Mixtral: screening de finales abruptos

Ámbito: 36 configuraciones originales, 4476 respuestas. No se incluyen ablaciones ni se generan nuevas salidas.

El detector existente marca **354 candidatos** con done_reason=stop. Se reproduce exactamente su recuento previo. Detecta terminaciones numéricas sospechosas y respuestas de diez palabras o menos sin puntuación final. No es un clasificador validado ni un recuento exhaustivo de fallos confirmados.

Una búsqueda más amplia añade **92 candidatos** sin puntuación terminal, excluidos los ya marcados. Incluye falsos positivos esperables: listas completas, citas o notas. No deben sumarse como fallos confirmados. Los 446 candidatos pueden revisarse con fuente y salida completas en candidate_review.html; candidate_entries.csv contiene fila, ID, configuración y texto completo.

Hay además **107 salidas con done_reason=length**, separadas de estos candidatos stop, y **2 salidas vacías**. Alcanzar el límite no prueba por sí solo que el final sea lingüísticamente incompleto. Tampoco stop prueba que sea completo.

Las 36 configuraciones tienen al menos un candidato del detector existente. by_configuration.csv contiene denominadores y ambos grupos, límites y vacíos; existing_detector_counts_table.csv ofrece la tabla compacta.

Los IDs repetidos de PLABA se conservan: se cuentan respuestas por fila y configuración, no documentos independientes. No inferir que todos los fallos tengan la misma causa ni que respondan a la penalización de repetición. Estos datos amplían la evidencia más allá de los cuatro ejemplos exactos del revisor y deben tenerse en cuenta antes de fijar el subconjunto diagnóstico.

No se modifica el diseño de generación ni se ejecuta el comando de penalización como parte de este análisis. Una revisión contextual completa y etiquetado independiente siguen pendientes; no se afirma una tasa humana definitiva.
