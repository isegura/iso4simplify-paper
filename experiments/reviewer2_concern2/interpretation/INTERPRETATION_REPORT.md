# Interpretación del estudio de selecciones — Concern 2

Fecha: 28 de octubre de 2026. Este informe interpreta resultados existentes sin cambiar modelos, pruebas, contrastes, familias o predicciones. No sustituye la revisión científica de los autores. No modifica artículo, suplementario ni Word de respuestas.

## 1. Qué cambia respecto a una única selección

La elección de demostraciones puede afectar materialmente a una configuración, sobre todo one-shot. No conviene describir las tendencias como inmunes a la selección de ejemplos. Los efectos globales se mantienen en algunos contrastes, pero el alcance por modelo/dataset y los recuentos descriptivos necesitan actualizarse.

Los conjuntos de selección son 42, 44 y 46; la semilla de generación permanece fija. Los nuevos conjuntos fueron escogidos bajo restricciones de diversidad/no solapamiento. No constituyen una muestra aleatoria amplia de todas las selecciones posibles, y no permiten separar efectos del contenido de la demostración de todos los detalles de ejecución histórica. La corrección de etiquetas de ejemplos también limita la atribución exclusiva a la selección.

## 2. Resultados globales de SARI

| Contraste | Δ SARI | IC bootstrap 95% | q BH (7) | Rechazo |
|---|---:|---|---:|---|
| ISO − baseline | -0.183 | [-0.409, +0.047] | 0.133 | No |
| ISO+examples − baseline | +0.126 | [-0.173, +0.436] | 0.4136 | No |
| ISO+examples − ISO | +0.309 | [+0.110, +0.511] | 0.004667 | Sí |
| One − zero | +0.820 | [+0.599, +1.054] | 2.861e-11 | Sí |
| Few-random − one | +0.696 | [+0.542, +0.851] | 9.461e-16 | Sí |
| Few-metric − few-random | -0.505 | [-0.721, -0.290] | 1.458e-05 | Sí |
| Mixtral − Llama | +0.545 | [+0.075, +1.011] | 0.03154 | Sí |

Interpretación:

- **ISO frente a baseline:** no se detecta ventaja global de ISO (−0.183; q=.133). Esto no prueba equivalencia ni que las instrucciones ISO carezcan de efecto.
- **ISO+examples frente a baseline:** tampoco se detecta ventaja global (+0.126; q=.414).
- **ISO+examples frente a ISO:** diferencia positiva media de +0.309. Es una mejora pequeña en esta escala observada; no se ha fijado un umbral de relevancia práctica ni se deduce mayor comprensión.
- **Demostraciones:** one supera a zero en +0.820 y few-random supera a one en +0.696 como promedios definidos. No significa que añadir ejemplos mejore cada configuración.
- **Selector fijo basado en métricas:** queda 0.505 puntos por debajo de few-random en el promedio. Solo se evalúan los umbrales, pesos y conjuntos de este estudio, no la utilidad general de selección automática ni recuperación por entrada.
- **Modelos:** Mixtral tiene +0.545 puntos en el contraste global. No implica superioridad en todos los datasets, métricas o settings, ni evalúa ventajas de arquitectura o tamaño de forma aislada.

Los contrastes asignan igual peso a datasets/modelos/prompts/condiciones pertinentes y 1/3 a cada selección dentro de one/few-random. No son el promedio indiscriminado de todas las filas ni triplican el peso de las condiciones aleatorias. Los IC son puntuales; q procede del test agrupado y BH. No son intervalos simultáneos ni corregidos por BH.

## 3. Desglose: dónde se sostienen las tendencias

Las comparaciones de prompt promedian las cuatro condiciones; las de condición promedian los tres prompts. Asterisco: q<.05 en la familia secundaria de 36 contrastes. Ausencia de asterisco no significa igualdad. No se han añadido pruebas de interacción: que una comparación rechace en un grupo y no en otro no demuestra, por sí solo, una diferencia significativa entre grupos.

| Modelo/dataset | ISO−B | E−B | E−ISO | One−zero | R−one | M−R |
|---|---:|---:|---:|---:|---:|---:|
| llama / cochrane | +0.925 * | +0.909 * | -0.016 | -0.107 | +0.173 | +0.055 |
| llama / plaba | +2.043 * | +2.657 * | +0.615 * | -0.106 | +1.652 * | -1.215 * |
| llama / tsar2025 | -0.317 | -0.623 | -0.306 | +0.982 * | +0.694 * | -0.239 |
| mixtral / cochrane | -0.944 * | -1.469 * | -0.525 * | +1.166 * | +0.133 | -0.305 |
| mixtral / plaba | -0.932 * | -0.297 | +0.635 * | +1.294 * | +1.190 * | -1.452 * |
| mixtral / tsar2025 | -1.873 * | -0.419 | +1.454 * | +1.695 * | +0.337 | +0.129 |

B=baseline; E=ISO+examples; R=few-random; M=few-metric.

- **Llama, Cochrane y PLABA:** ambos prompts ISO superan al baseline en sus promedios. PLABA muestra las mayores ventajas: +2.043 para ISO y +2.657 para ISO+examples. En TSAR no se detectan diferencias de prompt frente al baseline.
- **Mixtral:** ISO queda por debajo del baseline en los tres datasets; ISO+examples queda por debajo en Cochrane, sin diferencia detectable frente a baseline en PLABA/TSAR. La ausencia de ventaja global de ISO no permite borrar estas direcciones opuestas entre modelos.
- **Ejemplos de principios:** ISO+examples supera a ISO en PLABA para ambos modelos y en TSAR para Mixtral, pero queda por debajo de ISO en Cochrane con Mixtral. No es una mejora uniforme.
- **One frente a zero:** diferencia positiva detectable en los tres datasets de Mixtral y en TSAR de Llama; no en Cochrane/PLABA de Llama.
- **Few-random frente a one:** diferencia positiva detectable en PLABA para ambos modelos y en TSAR para Llama; no en Cochrane ni en TSAR con Mixtral.
- **Few-random frente a few-metric:** la ventaja detectable por modelo/dataset se concentra en PLABA, aproximadamente +1.215 para Llama y +1.452 para Mixtral. En Cochrane/TSAR no se detecta una diferencia tras BH. No afirmar que random mejora de forma significativa todos los datasets.

## 4. Sensibilidad a las tres selecciones

Cada SD es la desviación muestral de tres puntuaciones de configuración. La mediana resume nueve condiciones por combinación modelo/setting. No es un error estándar por textos.

| Modelo | Setting | Mediana SD SARI | Máxima SD | Máximo rango entre selecciones |
|---|---|---:|---:|---:|
| llama | few_random | 0.398 | 0.865 | 1.690 |
| llama | one | 0.718 | 2.009 | 3.652 |
| mixtral | few_random | 0.430 | 0.852 | 1.704 |
| mixtral | one | 0.429 | 0.877 | 1.737 |

El caso más sensible es **Llama / PLABA / ISO / one-shot**: SARI 33.712, 37.364 y 36.988; media 36.022, SD 2.009, rango 3.652. El baseline one-shot de la misma combinación varía 3.193 puntos y ISO+examples one-shot 3.033. El fenómeno no se restringe al prompt ISO.

La menor mediana de SD de few-random frente a one con Llama sugiere menor sensibilidad descriptiva en estos conjuntos. Con Mixtral las medianas son casi iguales (0.430 frente a 0.429). No se ha probado estadísticamente que tres ejemplos reduzcan la varianza ni puede generalizarse a selecciones no observadas.

En nueve de las 18 combinaciones modelo/dataset/prompt cambia el signo de la diferencia few-random−one según la selección. Algunas diferencias son muy pequeñas. Esto refuerza la necesidad de informar las tres puntuaciones y su SD en lugar de elegir una semilla favorable o tratar la clasificación de una única ejecución como estable.

## 5. Recuentos de victorias: cómo actualizar el artículo

- El recuento histórico ISO+examples>ISO se reproduce: **16/24**, sin empates. Al sustituir one/few-random por sus medias de tres selecciones, pasa a **15/24**.
- ISO>baseline se reproduce como **10/24** y sigue siendo **10/24** con las medias nuevas.
- Few-random>few-metric era **16/18** con 42; es **14/18** con 44 y **11/18** con 46. Comparar la media de random de tres selecciones con el selector fijo da **14/18**.

Son recuentos descriptivos; las comparaciones comparten fuentes, prompts y selecciones. No tratarlos como ensayos independientes ni añadir una prueba de signos posterior. Se puede conservar 16/18 si se identifica como el resultado histórico de 42; para la síntesis actual es preferible 14/18 y aclarar que compara medias random con un comparador fijo.

## 6. Otras métricas y descriptores: no hay una única noción de mejora

Las seis métricas tienen media/SD; solo SARI tiene los contrastes confirmatorios fijados. No afirmar significación en BLEU, BERTScore, MeaningBERT o legibilidad usando sus cambios descriptivos.

Ejemplo ilustrativo, media de los tres prompts de **Llama/PLABA/one-shot** (cada prompt comparte el mismo conjunto de demostración dentro de la selección; no son réplicas independientes):

| Selección | SARI | MeaningBERT fuente | FKGL | FRE | Palabras salida | Ratio | Copy |
|---|---:|---:|---:|---:|---:|---:|---:|
| 42 | 33.413 | 58.558 | 9.193 | 56.908 | 135.989 | .667 | .485 |
| 44 | 36.706 | 72.401 | 10.763 | 48.914 | 140.741 | .687 | .611 |
| 46 | 36.346 | 66.991 | 11.076 | 48.246 | 160.968 | .795 | .556 |

Las selecciones nuevas tienen SARI y similitud fuente mayores en este ejemplo, pero mayor FKGL y menor FRE: la mejora en SARI no equivale a una mejora uniforme de legibilidad. Cambian también longitud y copia. Esto describe covariación entre conjuntos, no demuestra que copiar cause la subida de MeaningBERT ni que se preserve toda la información.

La SD máxima de MeaningBERT es 8.269 (Llama/PLABA/ISO/one) y 8.231 para ISO+examples en esa combinación. BERTScore se guarda en escala 0–1: tanto media como SD deben multiplicarse por 100 si se presentan en escala porcentual. Las medias y SD completas están en las tablas de evaluación; no seleccionar solo casos favorables.

## 7. Qué podemos afirmar y qué no

**Afirmaciones respaldadas:** la selección concreta importa en algunos contextos; no se detecta ventaja global uniforme de prompts ISO frente a baseline; los patrones varían por modelo/dataset; few-random supera globalmente al selector fijo evaluado con el desglose indicado; el comportamiento de SARI no representa todas las dimensiones de lectura o significado.

**Evitar:** “resultados independientes de la semilla”, “few-shot siempre mejora”, “random es universalmente mejor”, “ISO no sirve”, “Mixtral simplifica mejor en general”, “las métricas validan comprensión/cumplimiento ISO” o “tres semillas prueban robustez poblacional”. Tampoco se demuestra equivalencia con pruebas no significativas.

## 8. Límites estadísticos y siguiente paso editorial

El análisis conjunto usa medias de celda y covarianza agrupada; no debe describirse como un modelo mixto. Se mantienen 148 filas PLABA pero 110 grupos, dentro de 335 grupos totales. El bootstrap por textos es condicional a los conjuntos observados y no un bootstrap de semillas. La agrupación difiere de la auditoría original y debe explicarse brevemente al integrar, sin modificar retrospectivamente sus tablas ni presentar los métodos como idénticos.

El análisis confirma los recuentos históricos indicados, pero sus conclusiones actuales provienen del diseño conjunto fijado, no de seleccionar entre tests. Las comparaciones frente al selector fijo no incluyen el experimento de recuperación de Concern 5; esa tarea sigue separada.

La siguiente fase es preparar la presentación final de medias/SD y contrastes, la respuesta del Concern 2 y completar la del Concern 3. Remi debería revisar la interpretación estadística antes de cerrar tablas y conclusiones. Las ubicaciones se ajustarán sobre el LaTeX actualizado. No son necesarias nuevas generaciones para estos resultados.

Archivos numéricos de apoyo en esta carpeta: `sari_seed_sensitivity.csv`, `sari_sensitivity_by_model_setting.csv`, `random_vs_fixed_metric_descriptive.csv`, `prompt_win_counts_descriptive.csv`. Los p/q e IC originales permanecen en `../statistics_results/joint_sari/` sin alteraciones.
