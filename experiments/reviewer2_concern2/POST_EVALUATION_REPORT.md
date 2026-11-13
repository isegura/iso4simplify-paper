# Concern 2 — evaluación y análisis completados, 28/10/2026

## Estado comprobado

- 72 configuraciones nuevas, 8952 generaciones, certificadas para selecciones 44/46.
- Métricas completas de 108 configuraciones one/few-random: 36 por selección 42/44/46; la 42 se reutilizó con las comprobaciones originales, sin regeneración.
- Seis métricas resumidas para 36 condiciones, con media y desviación muestral entre las tres selecciones (216 filas de resumen).
- Descriptores de las mismas 108 configuraciones, 13428 respuestas contando las tres selecciones; medias y desviaciones de cinco descriptores (180 filas). Los 72 originales ya preparados para Concern 3 mantienen su ámbito histórico.
- Análisis conjunto SARI: 144 celdas observadas, 17904 respuestas y 335 grupos por identificador. Los zero/few-metric fijos no se triplican. Se conservan todas las filas de PLABA y se agrupa su incertidumbre por identificador compartido.
- Siete contrastes primarios y 36 secundarios, BH en familias separadas; 10000 remuestreos por grupos. Los hashes de entradas estadísticas se volvieron a comprobar tras la ejecución y las medias/SD se verificaron directamente desde las tres columnas individuales.

## Efectos globales primarios

Son contrastes marginales con los pesos fijados en PLAN_ESTADISTICO.md, no efectos uniformes en cada dataset/configuración. Los IC bootstrap son puntuales y q corresponde a la prueba con covarianza agrupada y BH de siete contrastes; no son el mismo objeto estadístico.

| Contraste | Δ SARI | IC bootstrap 95% | q BH | Rechazo q<.05 |
|---|---:|---|---:|---|
| ISO − baseline | -0.183 | [-0.409, +0.047] | 0.133 | No |
| ISO+examples − baseline | +0.126 | [-0.173, +0.436] | 0.4136 | No |
| ISO+examples − ISO | +0.309 | [+0.110, +0.511] | 0.004667 | Sí |
| One-shot − zero-shot | +0.820 | [+0.599, +1.054] | 2.861e-11 | Sí |
| Few-random − one-shot | +0.696 | [+0.542, +0.851] | 9.461e-16 | Sí |
| Few-metric − few-random | -0.505 | [-0.721, -0.290] | 1.458e-05 | Sí |
| Mixtral − Llama | +0.545 | [+0.075, +1.011] | 0.03154 | Sí |

No hay evidencia de una ventaja global de ISO o ISO+examples frente al baseline en estos contrastes; no significa equivalencia. ISO+examples supera a ISO en el promedio definido, y las comparaciones entre settings también muestran diferencias globales. Deben revisarse los 36 contrastes por modelo/dataset antes de redactar afirmaciones generales. La comparación few-metric/few-random corresponde al selector fijo y las selecciones aleatorias observadas; no incluye recuperación por entrada del Concern 5.

Las tres selecciones no permiten estimar toda la variabilidad posible: 44/46 se eligieron bajo restricciones de diversidad. Los IC agrupados describen incertidumbre por textos condicionada a los conjuntos observados. No se atribuye toda diferencia frente a 42 únicamente a la selección: se conservan las limitaciones históricas y de corrección de etiquetas de prompts.

## Archivos principales (relativos al repositorio)

- `experiments/reviewer2_concern2/evaluation/metrics/summaries/all_models_all_datasets_mean_sd.csv`
- `experiments/reviewer2_concern2/evaluation/metrics/summaries/all_models_all_datasets_per_seed.csv`
- `experiments/reviewer2_concern2/evaluation/descriptors/summaries/all_models_all_datasets_mean_sd.csv`
- `experiments/reviewer2_concern2/statistics_results/joint_sari/primary_sari.csv`
- `experiments/reviewer2_concern2/statistics_results/joint_sari/secondary_sari.csv`
- `experiments/reviewer2_concern2/statistics_results/joint_sari/complete.json`

## Siguiente fase

Interpretar la variación por selección y los contrastes por modelo/dataset; revisar las afirmaciones y recuentos de victorias originales; preparar tablas/textos y guía de inserción de Concern 2 y completar las de Concern 3 con el nuevo alcance. Coordinar abstract/conclusiones con Concerns 5/6. No se ha modificado ningún original .tex ni Word, ni subido estos resultados nuevos a GitHub. No se han iniciado experimentos del Concern 5.
