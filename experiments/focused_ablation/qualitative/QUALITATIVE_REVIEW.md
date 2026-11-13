# Revisión cualitativa de la ablación de organización y resumen

Se inspeccionaron 15 textos fuente y 30 pares de salidas (ISO e ISO+examples para cada texto). Esta es una lectura exploratoria asistida por IA, no una evaluación humana con jueces independientes ni una medición validada de adherencia a ISO.

## Selección y procedimiento

La selección se fijó en PREPARATION.md antes de esta inspección: posiciones base cero 0, floor((n−1)/4), floor((n−1)/2), floor(3(n−1)/4), n−1. Se usaron las mismas posiciones para ambas familias de prompts, sin seleccionar por SARI, formato o errores.

- Cochrane: filas 0, 31, 62, 93 y 124 (posiciones 1, 32, 63, 94 y 125).
- PLABA: filas 0, 36, 73, 110 y 147 (posiciones 1, 37, 74, 111 y 148).
- TSAR2025: filas 0, 24, 49, 74 y 99 (posiciones 1, 25, 50, 75 y 100).

Se leyó la fuente y el contenido completo de las dos salidas. Se examinó la apertura, la posición de la conclusión/recomendación explícita en la fuente, la agrupación temática o temporal, la segmentación y la longitud. Se distinguió un resumen inicial añadido de una frase introductoria o una recomendación ya situada al comienzo de la fuente. Los títulos y las notas sobre haber seguido instrucciones no se trataron como resúmenes ni como prueba de cumplimiento. No se estableció una clasificación binaria de importancia ni se calcularon frecuencias subjetivas de adherencia. La longitud usa len(text.split()), incluido metatexto, igual que la evaluación previa.

## Observaciones sustentadas por los casos

En la muestra no aparece una dirección uniforme de deterioro de organización al retirar el bloque. Los ejemplos muestran persistencia del orden de la fuente, conservación de estructuras, expansión o contracción y cambios locales de segmentación. Esto es una observación de esta muestra, no una tasa poblacional ni evidencia de equivalencia.

- **La instrucción original no siempre se traduce en conclusión primero.** En Cochrane CD009601 y CD007497, ambas familias suelen abrir con estudios o búsqueda, dejando la conclusión para después. El original no proporciona aquí un contraste limpio entre presencia y ausencia de un resumen inicial.
- **La estructura puede persistir o aumentar tras la ablación.** En PLABA 34477130 con ISO, la ablación añade cinco secciones numeradas; en Cochrane CD008053 con ISO+examples introduce una lista de resultados. VISUAL FORMAT y sus ejemplos siguen presentes: las listas no son evidencia de aislamiento completo de la organización.
- **Hay pares sin cambios.** PLABA 34477130 y 27630909 con ISO+examples, y TSAR21 con ISO+examples, tienen salidas completas idénticas. Esto es comprobable para esos pares; no permite extrapolar equivalencia al conjunto.
- **La cronología puede conservarse sin el bloque.** TSAR45 mantiene casa → café → coworking en ambas familias. En TSAR70 con ISO+examples cambia la división en párrafos, conservando la secuencia narrativa.
- **Longitud, detalle y estructura no son intercambiables.** Cochrane CD007497 con ISO se expande, mientras otros ejemplos se acortan. En TSAR45 con ISO+examples se añade una recapitulación final redundante. Esos cambios no implican por sí mismos mayor o menor calidad de organización.
- **Metatexto y fidelidad requieren distinguirse del objetivo de la ablación.** Cochrane CD011655 con ISO ablated añade una nota sobre seguir ISO; PLABA 6445384 conserva notas en ambas condiciones. Algunos pares modifican afirmaciones de la fuente. Esta revisión no es una auditoría exhaustiva de errores ni consejo clínico.
- **Un par seleccionado está afectado por truncamiento de la ablación.** Cochrane CD007497, ISO+examples ablated, termina en “trials in ART” con done_reason=length. No se atribuye su cierre ausente a falta de organización.

## Interpretación y límites

Los cambios pequeños y no significativos de SARI son compatibles con esta heterogeneidad de ejemplos, pero la revisión cualitativa no demuestra que el bloque carezca de efecto ni que los prompts sean equivalentes. No se evaluó formalmente comprensión, utilidad para lectores ni fidelidad clínica. No hubo cegamiento, jueces humanos independientes, adjudicación ni acuerdo entre evaluadores. La muestra sistemática es pequeña y no aleatoria; no justifica estimaciones de frecuencia ni generalizaciones a otros modelos.

La organización ya presente en la fuente, las instrucciones de formato conservadas, el encuadre ISO y otros requisitos del prompt pueden contribuir a la persistencia de estructura. Son explicaciones plausibles, no mecanismos demostrados por esta inspección. La ablación tampoco controla longitud total, número de instrucciones ni permisos de omisión. Por tanto, informa sobre retirar este bloque en estas condiciones, no sobre el efecto causal completo de ISO 24495-1.

Los identificadores repetidos de PLABA no se han investigado, conforme a la decisión del usuario. Se conserva siempre el índice de fila para identificar cada evidencia.

## Registro de los 30 pares

Los textos completos se pueden consultar en reviewed_pairs.html; reviewed_pairs.csv conserva fuente, referencias, ambas salidas, longitudes, terminaciones y observaciones. Los archivos *_reading.txt son copias para lectura. No se modificó ninguna predicción.


### cochrane · iso · fila 0 · ID CD009601

Palabras: 195 → 189. Terminación: stop → stop. Salidas idénticas: no.

Ambas versiones abren con el número de estudios y participantes, no con una síntesis de la conclusión sobre eficacia. Conservan el recorrido estudios → limitaciones → resultados → necesidad de investigación. La ablación separa más los comparadores y conserva detalles metodológicos; la versión original termina con una recapitulación adicional. No se observa un desplazamiento de la conclusión principal al comienzo.


### cochrane · iso · fila 31 · ID CD008053

Palabras: 165 → 145. Terminación: stop → stop. Salidas idénticas: no.

Ambas aperturas presentan la comparación y la insuficiencia de la muestra; es un encuadre del estudio con cautela, no un resumen separado. La ablación conserva el orden y agrupa los resultados y las implicaciones en menos párrafos. La original habla de partos en casa y añade una afirmación sobre volver a entrar en parto que no se encuentra en la fuente; la ablación afirma ausencia de diferencia en muertes donde la fuente señala evidencia insuficiente. Estos problemas de contenido impiden equiparar una organización legible con fidelidad.


### cochrane · iso · fila 62 · ID CD011655

Palabras: 118 → 130. Terminación: stop → stop. Salidas idénticas: no.

Ambas versiones comienzan por muestra y disponibilidad de resultados, dejando las limitaciones de la comparación para el cierre. La agrupación estudio → resultados → limitaciones se mantiene. La ablación añade glosas de global state y parkinsonism, cambia qué resultados ausentes enumera y añade una nota sobre haber seguido ISO. Esa nota es metatexto, no un resumen del contenido, y contradice RESPONSE FORMAT.


### cochrane · iso · fila 93 · ID CD004510

Palabras: 177 → 179. Terminación: stop → stop. Salidas idénticas: no.

Ambas versiones mantienen un único párrafo largo y una secuencia prácticamente paralela. La conclusión sobre incertidumbre de eficacia sigue al final; In summary/In short son cierres, no resúmenes iniciales. Hay ajustes de redacción, sin reorganización apreciable. TFU permanece sin desarrollar en ambas.


### cochrane · iso · fila 124 · ID CD007497

Palabras: 162 → 257. Terminación: stop → stop. Salidas idénticas: no.

Ambas aperturas siguen la búsqueda y selección de estudios; la limitación de generalización y la necesidad de investigar aparecen después. La ablación desarrolla más detalles y separa diseño, resultados y generalización en más párrafos. No hay un resumen inicial independiente ni traslado claro de la conclusión al principio; el cambio más visible es expansión del contenido.


### cochrane · iso_examples · fila 0 · ID CD009601

Palabras: 351 → 371. Terminación: stop → stop. Salidas idénticas: no.

Las aperturas conservan casi literalmente el número de estudios y las comparaciones. La conclusión sobre evidencia insuficiente continúa hacia el final. La ablación aumenta la segmentación y retiene riesgos relativos e intervalos que la original había omitido. Es un cambio de detalle y agrupación local, no evidencia de pérdida de una jerarquía inicial que la original mostrara claramente.


### cochrane · iso_examples · fila 31 · ID CD008053

Palabras: 162 → 193. Terminación: stop → stop. Salidas idénticas: no.

Ambas versiones abren con el diseño y la insuficiencia de la muestra. La ablación convierte resultados en una lista y separa cautela, satisfacción/costes y futuras investigaciones. La conclusión general sigue al cierre. Las listas aparecen pese a retirar el bloque de organización, coherentemente con VISUAL FORMAT conservado. La original interpreta una dirección de mortalidad pese a la gran incertidumbre; la ablación reduce esa precisión y habla de poca diferencia: son cambios de contenido, no solo de formato.


### cochrane · iso_examples · fila 62 · ID CD011655

Palabras: 128 → 108. Terminación: stop → stop. Salidas idénticas: no.

Ambas versiones son un único párrafo, abren con estudios y participantes y siguen con resultados clínicos y datos ausentes. No aparece un resumen inicial separado. La ablación acaba tras enumerar resultados sin datos y omite el comentario final de la original sobre falta de evidencia comparativa de calidad. Acortar ese cierre afecta al contenido conservado, no demuestra por sí mismo una peor agrupación.


### cochrane · iso_examples · fila 93 · ID CD004510

Palabras: 175 → 169. Terminación: stop → stop. Salidas idénticas: no.

Ambas versiones siguen un párrafo único con estudios, heterogeneidad e incertidumbre. Conservan la conclusión al final y el marcador In summary como cierre. La ablación cambia vocabulario sin un reordenamiento claro. TFU permanece sin explicar.


### cochrane · iso_examples · fila 124 · ID CD007497

Palabras: 290 → 342. Terminación: stop → length. Salidas idénticas: no.

Ambas versiones comienzan con búsqueda y ensayos y conservan la secuencia de la fuente. La ablación retiene más cifras, citas e intervalos y termina abruptamente en trials in ART. El registro confirma terminación length a 512 tokens: no atribuir la falta de cierre a una decisión de organización. El final truncado confunde cualquier valoración de la completitud o agrupación final de este par.


### plaba · iso · fila 0 · ID 30377698

Palabras: 178 → 123. Terminación: stop → stop. Salidas idénticas: no.

La original añade la etiqueta Simplified Text y la ablación un título temático. Las dos abren con enfermedad y tratamiento, mientras la conclusión específica sobre reducción del quiste queda al final. Ambas agrupan contexto, método, resultados y conclusión. La ablación comprime cifras y seguimiento; el título no equivale a un resumen inicial de resultados.


### plaba · iso · fila 36 · ID 6445384

Palabras: 139 → 95. Terminación: stop → stop. Salidas idénticas: no.

Ambas abren con el objetivo del estudio y mantienen el orden de los efectos y su interpretación. La ablación comprime varios párrafos en un párrafo de contenido, omite detalles y mantiene una nota explicativa final, también presente en la original. El resumen compacto no es un bloque inicial añadido: ocupa todo el cuerpo. La fuente dice efecto máximo a seis horas; la ablación dice que duró seis horas, un cambio de significado independiente del formato.


### plaba · iso · fila 73 · ID 34477130

Palabras: 171 → 211. Terminación: stop → stop. Salidas idénticas: no.

La original comienza por comparación y muestra y organiza beneficios en listas. La ablación añade cinco secciones numeradas —Introduction, Methods, Results, Sub-group Analysis y Conclusion— y conserva listas. Ninguna antepone un resumen de resultados; ambas dejan una conclusión final. La ablación resulta más estructurada explícitamente pese a retirar el bloque. Cambia además afirmaciones de resultados: niega diferencia en hemoglobina donde la fuente informa P<.00001 y añade días como unidad de estancia no explicitada en la fuente. No confundir estructura visible con exactitud.


### plaba · iso · fila 110 · ID 27630909

Palabras: 167 → 206. Terminación: stop → stop. Salidas idénticas: no.

La original abre con síntomas y objetivo; la ablación añade título y abre con el papel diagnóstico de Beta hCG y el objetivo. Ambas mantienen Methods/Results/Conclusion y agrupación de resultados y tratamientos. La ablación incluye más porcentajes y sublistas. La recomendación de interpretación conjunta con hallazgos clínicos y sonográficos queda al final en ambas, no en un resumen inicial.


### plaba · iso · fila 147 · ID 35008695

Palabras: 198 → 222. Terminación: stop → stop. Salidas idénticas: no.

Ambas comienzan por el contexto de redistribución del hierro, no por el resultado en ratones. La original separa antecedentes y hallazgos en párrafos y añade una lista recapitulativa; la ablación usa un párrafo largo seguido de una lista numerada que repite los hallazgos. La ablación añade además una nota sobre usar listas. La repetición y el desplazamiento al cierre son observaciones locales: no prueban una tasa global de peor organización.


### plaba · iso_examples · fila 0 · ID 30377698

Palabras: 185 → 210. Terminación: stop → stop. Salidas idénticas: no.

Ambas versiones siguen contexto → hipótesis → métodos/resultados → conclusión. La ablación separa más los bloques y conserva explícitamente los plazos de seguimiento y las cifras. No antepone la conclusión de reducción del quiste a los antecedentes ni añade un resumen inicial independiente. La segmentación aumenta sin que desaparezca la lógica temática.


### plaba · iso_examples · fila 36 · ID 6445384

Palabras: 99 → 168. Terminación: stop → stop. Salidas idénticas: no.

Ambas versiones son un párrafo de contenido seguido de una nota explicativa. La ablación recupera dosis, términos técnicos y detalles de mecanismos, conservando el orden de la fuente. No hay un resumen inicial añadido ni una reorganización global. La mayor longitud y tecnicidad son cambios concomitantes, no una medición de organización. Ambas notas incumplen la instrucción de devolver solo el texto simplificado.


### plaba · iso_examples · fila 73 · ID 34477130

Palabras: 103 → 103. Terminación: stop → stop. Salidas idénticas: sí.

Las dos salidas son exactamente iguales. Ambas presentan estudio y muestra en el primer párrafo, una síntesis del resultado en el segundo, una lista de beneficios y una cautela final. La síntesis temprana se mantiene sin ser un bloque de resumen al comienzo. La igualdad también conserva problemas de fidelidad: ambas presentan menor riesgo de fiebre y fuga urinaria pese a los valores no significativos informados en la fuente.


### plaba · iso_examples · fila 110 · ID 27630909

Palabras: 190 → 190. Terminación: stop → stop. Salidas idénticas: sí.

Las dos salidas son exactamente iguales, con apertura contextual, Aim, Methods, Results y Conclusion, más listas anidadas. La conclusión diagnóstica sigue al final y no hay un resumen inicial separado. La conservación exacta es evidencia de ausencia de cambio en este par, no de equivalencia general entre prompts.


### plaba · iso_examples · fila 147 · ID 35008695

Palabras: 166 → 161. Terminación: stop → stop. Salidas idénticas: no.

Las dos versiones tienen tres párrafos con el mismo contexto, estudio en ratones y mecanismo/conclusión final. Solo cambia de manera menor la frase que introduce el estudio. El hallazgo principal no se traslada al comienzo; la agrupación se conserva y no aparece un resumen añadido.


### tsar2025 · iso · fila 0 · ID 21

Palabras: 73 → 66. Terminación: stop → stop. Salidas idénticas: no.

El cuerpo simplificado es igual en ambas versiones y sigue pistas de los sueños → ejemplos → conexión con la vida diaria. La instrucción interpretativa clave permanece al final. Solo cambia la nota explicativa posterior: una enumera principios de organización y la otra instrucciones lingüísticas. Esas autodescripciones no son evidencia de cumplimiento ni resúmenes del contenido.


### tsar2025 · iso · fila 24 · ID 45

Palabras: 100 → 108. Terminación: stop → stop. Salidas idénticas: no.

Ambas versiones mantienen cuatro párrafos y el orden cronológico casa → café → coworking, tras el encuadre como freelancer. No añaden un resumen independiente de la solución al principio. La ablación conserva conectores y modifica formulación local; la progresión temporal permanece clara sin el bloque retirado.


### tsar2025 · iso · fila 49 · ID 70

Palabras: 47 → 50. Terminación: stop → stop. Salidas idénticas: no.

Ambas versiones conservan dos párrafos: llegada/café/espera y disfrute con las ratas. No añaden resumen ni invierten el orden narrativo. Cambian detalles sobre el lugar del café, la intención de subir y las distracciones; estas reformulaciones no se deben interpretar solo como organización. El núcleo temporal es parecido.


### tsar2025 · iso · fila 74 · ID 95

Palabras: 53 → 56. Terminación: stop → stop. Salidas idénticas: no.

Ambas abren con una generalización sobre los lugares vacíos en el cine de terror. La original agrupa silencio, soledad y preguntas en el primer párrafo y reserva la cobertura telefónica para el segundo. La ablación lleva las preguntas al segundo párrafo junto al teléfono. El tema se conserva con una frontera de agrupación diferente; la apertura temática no es un resumen añadido de todo el pasaje.


### tsar2025 · iso · fila 99 · ID 120

Palabras: 56 → 20. Terminación: stop → stop. Salidas idénticas: no.

Ambas abren con la recomendación sobre comentarios positivos/negativos, siguiendo la posición de la fuente; por ello no puede atribuirse esa prioridad al bloque ISO. La ablación acorta el contenido y elimina la nota explicativa original. Su Don't mix es más categórico que el Don't always follow de la fuente. El cambio de alcance debe separarse del de longitud.


### tsar2025 · iso_examples · fila 0 · ID 21

Palabras: 49 → 49. Terminación: stop → stop. Salidas idénticas: sí.

Las dos salidas son exactamente iguales y mantienen generalización sobre sueños, ejemplos y recomendación interpretativa al final. No hay un resumen inicial independiente. La coincidencia es específica de este par.


### tsar2025 · iso_examples · fila 24 · ID 45

Palabras: 106 → 116. Terminación: stop → stop. Salidas idénticas: no.

Ambas conservan la cronología casa → café → coworking. La ablación añade al final I use this space because it helps me stay focused and avoid distractions at home, que repite la motivación ya expuesta. No adelanta la solución como resumen inicial; el cambio visible es una recapitulación final adicional.


### tsar2025 · iso_examples · fila 49 · ID 70

Palabras: 51 → 45. Terminación: stop → stop. Salidas idénticas: no.

La original divide llegada/espera y ratas en dos párrafos; la ablación los integra en uno con frases más cortas. Ambas mantienen el orden de acontecimientos, sin resumen añadido. La fusión de párrafos no elimina la secuencia temporal, aunque reduce la separación visual de temas.


### tsar2025 · iso_examples · fila 74 · ID 95

Palabras: 77 → 82. Terminación: stop → stop. Salidas idénticas: no.

Ambas versiones usan un párrafo temático sobre lugares vacíos y una nota explicativa. La secuencia lugares → sensación/inquietud → utilidad de la falta de cobertura se conserva con reformulaciones. Las notas cambian, pero no son resúmenes ni evidencia de cumplimiento. No se observa una reorganización global.


### tsar2025 · iso_examples · fila 99 · ID 120

Palabras: 28 → 33. Terminación: stop → stop. Salidas idénticas: no.

Ambas abren con la recomendación sobre feedback y siguen consecuencia → consejo. No añaden un resumen inicial independiente; la prioridad ya procede de la fuente. La ablación reformula devaluación y crítica con una estructura casi idéntica. La agrupación se mantiene.
