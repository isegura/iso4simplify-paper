# Concern 7: auditoría automática de todas las salidas originales

Completada el 23 de octubre de 2026. Ámbito: **72 configuraciones, 8952 respuestas**, 4476 por modelo. Se han conservado todas las filas originales, sin seleccionar por SARI, incluidas vacías y capadas. No se incluyen ablaciones, penalización 1.0 ni selecciones nuevas 44/46.

## Resultados automáticos

Los porcentajes siguientes usan como denominador las 4476 respuestas de cada modelo, sumando datasets y configuraciones; no son porcentajes de documentos independientes ni promedios balanceados por dataset. El archivo `screening/by_configuration.csv` ofrece los 72 denominadores y recuentos individuales.

| Indicador | Llama, n (%) | Mixtral, n (%) |
|---|---:|---:|
| Salida vacía | 0 (0.00) | 2 (0.04) |
| Límite de generación observado | 17 (0.38) | 107 (2.39) |
| Candidato de final abrupto: detector original | 2 (0.04) | 354 (7.91) |
| Unión de cribados de final: original y puntuación terminal | 55 (1.23) | 446 (9.96) |
| Candidato de preámbulo | 165 (3.69) | 4 (0.09) |
| Una o más líneas con marcador de lista | 464 (10.37) | 399 (8.91) |
| Sigla sin expansión parentética detectada | 1836 (41.02) | 2069 (46.22) |
| Sigla anterior ausente literalmente de la fuente | 205 (4.58) | 151 (3.37) |

**Estas son tasas de indicadores, no tasas de errores confirmados.** Listas y lenguaje técnico no son necesariamente problemas; el uso de listas está pedido en los prompts ISO. No sumar columnas: se solapan. La unión de finales excluye vacíos y se restringe a `done_reason=stop`; los eventos `length` se mantienen separados. Tampoco debe sumarse `length` como si todos esos finales fueran lingüísticamente incompletos.

Se reproducen exactamente, por fila, los 354 candidatos originales de Mixtral y los 92 candidatos adicionales de su auditoría del Concern 4. La revisión contextual previa de sus 446 candidatos permanece allí: no se ha repetido ni se presenta como validación independiente.

## Revisión exploratoria de falsos positivos

Se seleccionó como máximo una salida positiva por combinación modelo/dataset/indicador, para cuatro indicadores y con semilla 20261023. Había 21 combinaciones disponibles: **21 salidas completas revisadas por el asistente**, consultando fuentes para cifras y casos ambiguos. No hubo selección por SARI ni ajuste posterior de las reglas.

Se observaron, entre otros:

- Un final de Llama en «Lower in trisomies 18 and 13» activa el detector numérico, pero es una viñeta completa y la fuente menciona esas trisomías.
- Tres candidatos de la búsqueda por puntuación terminaban en listas completas sin punto. La falta de punto no basta para afirmar truncamiento.
- «Here's some good news about violence» reformula una idea de la fuente: el patrón de preámbulos lo marca, pero no es metatexto sobre la reescritura.
- «osteoarthritis (OA)», FF/VI y TIO están explicados o asociados a sus nombres, aunque las reglas no reconocen expansiones de una palabra o combinaciones de siglas. «Medium-sized space rocks (NEOs)» proporciona una explicación funcional sin coincidir con las iniciales.
- También hay cortes aparentes claros de Mixtral: «Pi and Richard Parker spend 2», «8.8% in 2» y «around 140,00», contrastados con 227 días, 2010 y 140000 en las fuentes.

Los juicios y textos completos están en `spot_check/reviewed_21.csv` y `spot_check/review.html`. Los recuentos de etiquetas de la muestra **no estiman precisión, sensibilidad ni frecuencia poblacional**: es una muestra pequeña de positivos, sin revisión sistemática de negativos, sin cegamiento ni anotación humana independiente. La etiqueta “indicator_supported” confirma únicamente la observación concreta revisada, no un error global ni incumplimiento ISO.

## Uso en la revisión del artículo

Esta auditoría permite sustituir afirmaciones de frecuencia basadas en los peores ejemplos por recuentos sistemáticos de indicadores con denominador por configuración. Los ejemplos cualitativos pueden seguir ilustrando tipos de fallo, sin afirmar que estiman su prevalencia.

En particular, no usar estas cifras para afirmar que todas las estrategias incumplen ISO, que las siglas detectadas son necesariamente incomprensibles o que las listas implican buena/mala simplificación. Para finales incompletos, distinguir el cribado automático de los juicios contextuales previos de Mixtral. Para longitud y copia, usar conjuntamente las definiciones y resúmenes ya preparados en Concern 3, que aquí se han comprobado como idénticos.

No se ha realizado evaluación humana, ni análisis de comprensión o de cumplimiento integral de ISO. La respuesta final debe mantener el alcance limitado de la evaluación automática acordado para Concern 3.

## Integridad y pendientes

Se han verificado los SHA-256 de los originales antes/después, la alineación con los test y la concordancia de longitud/compresión/copia con los 72 resúmenes del Concern 3. Los tests de reglas y los conteos por configuración pasan. No se ha usado Ollama ni modelos semánticos, no se han abierto datos de 44/46 y no se ha modificado ningún `.tex`.

La parte de cribado sistemático del Concern 7 queda preparada. Falta decidir la presentación final de indicadores y revisar las afirmaciones afectadas al integrar el artículo y el suplemento; el material y la respuesta están separados. Estos resultados no convierten el detector en una evaluación humana ni garantizan por sí solos que el concern quede aceptado.

## Actualización editorial — 24 de octubre de 2026

La presentación propuesta queda concretada en `manuscript_proposals/`: una tabla resumen por modelo para el artículo, dos tablas completas de las 72 configuraciones para el suplemento, definiciones, limitaciones, sustituciones de texto y respuesta al revisor. Se usa el suplementario actualizado `(1)`. Los conteos se han vuelto a comprobar contra los 8952 registros de indicadores. No se han vuelto a calcular métricas ni modificado las reglas. Falta aplicar la propuesta y comprobar el PDF final, no decidir desde cero su presentación.
