# Concern 2: especificación estadística previa al análisis nuevo

Fecha: 23 de octubre de 2026. Se concreta el compromiso de ANALYSIS_PLAN.md mientras la autora ejecuta las nuevas generaciones. No es un registro externo ni se afirma que preceda a la generación de todas las salidas: precede a examinar sus puntuaciones y ajustar este análisis. No se han calculado nuevos contrastes, p-valores ni conclusiones al preparar este documento.

## Pregunta y datos

Evaluar conjuntamente las asociaciones de prompt, condición de prompting, modelo y dataset con SARI, y describir cuánto varían las puntuaciones entre los tres conjuntos de demostraciones seleccionados. El resultado primario es SARI por ítem con el redondeo histórico del pipeline. Las otras cinco métricas se presentan descriptivamente por configuración y semilla; BLEU es de corpus y no entra como respuesta por ítem en la regresión.

Se incluyen 144 configuraciones y 17904 filas de resultados: las 72 históricas y las 72 nuevas. Para cada modelo/dataset/prompt hay zero y few-metric históricos una sola vez, más one y few-random con las selecciones 42/44/46. No existen one-metric o zero-metric; por tanto se utiliza un factor de cuatro condiciones y no un factorial independiente shots × selection con celdas inexistentes. Las ablaciones y el diagnóstico de penalización 1.0 quedan fuera.

Las 36 condiciones aleatorias tienen además tablas individuales 42/44/46 y media, SD muestral, mínimo y máximo. No se tratan esas tres selecciones restringidas como una muestra aleatoria amplia de todas las posibles demostraciones. La semilla de generación siempre es 42.

## Unidad y dependencia de PLABA

Se conserva cada fila de test y toda salida, incluidas vacías y capadas. Para mantener la ponderación del estudio original, la estimación de cada configuración es la media sobre filas, no una media nueva de documentos.

La incertidumbre se agrupa por dataset + text_id, manteniendo juntas todas las filas y todas las configuraciones del mismo identificador. Cochrane tiene 125 filas/125 grupos; PLABA 148 filas/110 grupos; TSAR 100 filas/100 grupos. Total: 373 filas fuente y 335 grupos. PLABA tiene también 110 fuentes textuales distintas: no se consideran 148 documentos independientes. No se eliminan duplicados ni se selecciona una referencia favorable.

Los intervalos y tests serán condicionales a los datasets y a las selecciones observadas. Agrupar textos no estima la incertidumbre de elegir nuevos conjuntos de demostraciones. Esa segunda variación se presenta mediante los tres resultados y su SD; no se oculta dentro de un intervalo por textos.

## Modelo conjunto elegido

Regresión lineal conjunta en parametrización de medias de celda: una columna indicadora por cada combinación observada de dataset, modelo, prompt, condición y selección cuando corresponda, sin intercepto adicional. Es un modelo de efectos fijos con interacciones completas en las combinaciones observadas, de rango 144. No se ajustarán 144 tests independientes ni se interpretarán los coeficientes individuales como descubrimientos.

Esta parametrización permite diferencias de prompt y condición específicas de modelo/dataset/selección sin imponer un efecto común de semilla. Los contrastes se calculan sobre el mismo modelo y promedian explícitamente las celdas relevantes. Se adopta regresión con incertidumbre agrupada en lugar de estimar una distribución de efectos aleatorios de demostraciones con solo tres conjuntos restringidos. El revisor sugiere un modelo mixto como ejemplo de análisis conjunto, no como único procedimiento posible. Esta elección no garantiza por sí sola que el revisor considere completamente resuelta su preocupación.

Los efectos marginales asignan el mismo peso a cada dataset, modelo, prompt y condición sobre los que se promedia. Dentro de one/few-random, cada semilla recibe 1/3 del peso de su celda estructural; zero/few-metric reciben su peso una sola vez. Por tanto tres selecciones no hacen que las condiciones aleatorias pesen tres veces más. Dentro de una configuración se conserva la media original sobre filas.

No se compararán modelos sucesivos para elegir el que produzca significación. El modelo no presupone ausencia de interacciones ni pretende extrapolar a otros modelos, datasets o conjuntos de demostraciones.

## Contrastes fijados y multiplicidad

Familia primaria de **7 contrastes bilaterales sobre SARI**, con medias marginales de igual peso:

1. ISO − baseline, promediando condiciones, modelos y datasets.
2. ISO+examples − baseline, con el mismo promedio.
3. ISO+examples − ISO, con el mismo promedio.
4. One − zero, promediando prompts, modelos y datasets.
5. Few-random − one, con el mismo promedio y selecciones emparejadas.
6. Few-metric − few-random, con el mismo promedio; few-metric es un único comparador fijo.
7. Mixtral − Llama, promediando datasets, prompts y condiciones.

Familia secundaria de **36 contrastes bilaterales sobre SARI**: los seis primeros contrastes anteriores, desglosados por las seis combinaciones modelo/dataset. Los tres contrastes de prompt promedian las cuatro condiciones; los de condición promedian los tres prompts.

Aplicar Benjamini–Hochberg (BH, FDR 0.05) por separado a las 7 pruebas primarias y las 36 secundarias. Publicar p sin ajustar, p ajustada, efecto en puntos SARI y CI. Las familias responden a preguntas distintas y se declararán explícitamente; no añadir familias posteriores ni sustituir BH por otro método según los resultados. No hay tests confirmatorios adicionales sobre las cinco métricas secundarias. Los contrastes específicos de prompt × condición × semilla se mostrarán descriptivamente si ayudan a entender la heterogeneidad.

Para los tests del modelo usar la matriz sandwich agrupada CR1: G/(G−1) × (N−1)/(N−p), con G=335, N=17904 y p=144 en el análisis completo. Los scores de cada grupo suman todas sus filas/configuraciones; no se usa una covarianza de errores independientes. Calcular el test t bilateral sobre cada contraste; grados de libertad 334 en contrastes globales y G_dataset−1 en los desglosados por dataset (124,109,99). Se explicará que es una aproximación de grandes muestras condicional a las selecciones.

## Intervalos y sensibilidad

El CI principal del efecto será el percentil 2.5/97.5 de **10000 remuestreos por grupos**, semilla computacional **20261023**. Dentro de cada dataset se remuestrean sus identificadores con reemplazo y se incluyen todas las filas/configuraciones de cada identificador escogido, con su multiplicidad. Se mantienen emparejadas las configuraciones y semillas. Se recalculan las medias por celda y los contrastes de pesos fijos. La distribución se basa en textos y no se presenta como un bootstrap de semillas.

Los CI del bootstrap son puntuales, no simultáneos ni corregidos por BH; no se equiparará excluir cero con superar BH. El test agrupado y el CI bootstrap son aproximaciones distintas: se presentarán ambos, con posibles discrepancias, sin escoger el favorable. Como sensibilidad se pueden mostrar los CI t de CR1 ya especificados, claramente identificados. Si hay varianza cero, score no finito, ausencia de una celda o fallo de alineación, detener y documentar: no sustituir por un test distinto tras ver el resultado.

La estimación por celda y sus contrastes equivalen algebraicamente a la regresión conjunta indicada. `statistics_core.py` implementa el ajuste, la matriz CR1, los tests, BH por familias y el bootstrap mediante sumas por grupo/celda, sin construir una matriz gigante. `test_statistics_plan.py` valida con datos sintéticos recuperación de efectos conocidos, coincidencia con mínimos cuadrados y la matriz sandwich expandida, pesos balanceados, un grupo con filas repetidas, reproducibilidad del remuestreo y separación de familias BH. Se han superado tres pruebas. No se ha aplicado el código a las nuevas puntuaciones reales.

## Recuentos y redacción

Revisar los recuentos originales de victorias ISO+examples/ISO y ISO/baseline sobre las 24 parejas históricas, documentando empates y precisión. Mantenerlos descriptivos: esas parejas comparten textos y factores, por lo que no se tratarán automáticamente como 24 ensayos independientes de signo. Una p no significativa no demuestra equivalencia; no se han fijado márgenes ni una prueba de equivalencia.

La comparación de selección es histórica, no un experimento contemporáneo que aísle causalmente la semilla. Conservar las limitaciones de entorno y de las etiquetas del tercer ejemplo corregidas en Cochrane/PLABA. No excluir resultados por mala calidad ni cambiar las semillas según los resultados. No hacer afirmaciones sobre comprensión humana o cumplimiento ISO a partir de SARI.

## Archivos y siguiente ejecución

`prepare_statistics.py` lee únicamente metadatos de los tres test, construye y valida el diseño y los pesos. No abre predicciones nuevas ni columnas de puntuaciones. Escribe en `statistics_plan/`: celdas, grupos fuente, conteos, pesos de los 43 contrastes y validación con hashes. No modifica el manifiesto ni los scripts congelados de generación.

Próximos pasos: esperar a las métricas completas; ensamblar la tabla de análisis y las sumas por grupo/celda, comprobando integridad y correspondencia con las 144 celdas previstas; aplicar el núcleo ya probado, ejecutar este plan y guardar los resultados aparte; preparar explicación y respuesta al revisor fuera de los `.tex` originales. El ensamblado y el comando final de ejecución todavía deben prepararse. Si una modificación metodológica resultara necesaria, conservar este plan y registrar antes de la nueva ejecución el cambio y su motivo.

Fuentes técnicas para la covarianza y la alternativa mixta: [cov_cluster, documentación oficial](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster.html), [implementación oficial de sandwich_covariance](https://github.com/statsmodels/statsmodels/blob/main/statsmodels/stats/sandwich_covariance.py), [modelos mixtos, documentación oficial](https://www.statsmodels.org/stable/mixed_linear.html). La elección concreta y los límites anteriores son decisiones de este estudio.
