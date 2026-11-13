# Revisión cualitativa de finales — Mixtral

Se revisaron las 446 salidas candidatas: las 354 del detector existente y las 92 del cribado amplio. Es una revisión exploratoria realizada por el asistente, sin evaluadores humanos independientes ni cegamiento. Se inspeccionaron las salidas completas y se consultaron fuentes completas para resolver dudas sobre cifras y términos técnicos. No se afirma haber evaluado fidelidad o cobertura completa de todas las salidas.

## Decisiones

dataset,candidates_reviewed,clear_apparent_cuts,no_clear_cut,uncertain,affected_test_rows,affected_unique_ids
cochrane,155,151,3,1,66,66
plaba,195,181,13,1,59,47
tsar2025,96,78,18,0,21,21

clear_apparent_cut significa final aparentemente cortado, no mecanismo de terminación demostrado. no_clear_cut significa que no hay corte claro del cierre, no que la simplificación sea buena o conserve todo el significado. uncertain conserva los casos ambiguos en lugar de forzar una decisión.

En total: 410 finales aparentemente cortados, 34 sin corte claro y dos dudosos. De los 354 candidatos iniciales, 353 se consideran cortes aparentes y uno es dudoso. De los 92 adicionales, 57 se consideran cortes aparentes, 34 no presentan corte claro y uno es dudoso.

Los dos dudosos son C057 (una sola oración con número de estudios/participantes, terminada en punto y coma) y C234 (solo un título). La falta de cobertura de la fuente no basta para afirmar un corte de generación. Las listas y notas completas sin punto son falsos positivos del cribado de puntuación.

## Alcance

Las 36 configuraciones contienen cortes aparentes. by_configuration_with_denominators.csv incluye las decisiones y los denominadores originales. Los recuentos por texto se basan en la posición de fila del test; PLABA contiene IDs repetidos, también desglosados. No se mezclan las 107 salidas con done_reason=length ni las dos vacías.

La revisión solo cubre candidatos: no certifica ausencia de fallos en las demás respuestas. No es una evaluación humana validada ni permite estimar sensibilidad/especificidad. Los resultados no identifican la causa del corte: repeat penalty, condiciones de parada y otros mecanismos siguen por comprobar.

## Siguiente decisión experimental

No se ha cambiado ni ejecutado el comando de generación. Dado que los cortes aparecen en todos los prompts y estrategias, es razonable seleccionar después un diagnóstico pequeño que cubra esos grupos y conserve los ejemplos exactos del revisor, manteniendo separados los fallos seleccionados deliberadamente y los controles aleatorios. Los archivos de generación todavía contienen el diseño anterior de 496 respuestas; no constituyen una selección nueva basada en esta revisión.

Las decisiones individuales, su motivo y la evidencia completa se encuentran en reviewed_candidates.csv, decisions.json y reviewed_evidence.html. Las predicciones originales, los informes previos y los archivos LaTeX permanecen sin modificar.
