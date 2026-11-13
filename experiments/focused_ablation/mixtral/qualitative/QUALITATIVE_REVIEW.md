# Revisión cualitativa de Mixtral

Se leyeron 15 fuentes y 30 pares de salidas originales/ablated: las mismas posiciones prefijadas que para Llama, sin seleccionar por métricas, formato o fallos. Cochrane: 0,31,62,93,124; PLABA: 0,36,73,110,147; TSAR2025: 0,24,49,74,99 (índices base cero). Se usó 0, floor((n−1)/4), floor((n−1)/2), floor(3(n−1)/4), n−1 para cada tamaño. Esto es inspección exploratoria asistida por IA, no una evaluación humana ciega con jueces independientes, ni un protocolo validado de adherencia ISO.

Se examinó la apertura frente a la conclusión explícita de la fuente, resumen añadido frente a contexto inicial, agrupación, cronología, formato y longitud. Las listas/títulos no se trataron automáticamente como resúmenes ni como prueba de calidad. La importancia de la información no recibió puntuaciones binarias. No se calcularon frecuencias poblacionales de cumplimiento o errores. Las longitudes usan len(split()) e incluyen todo metatexto.

## Observaciones

- **Persistencia o aparición de estructura sin el bloque.** Cochrane CD011655 ISO ablated introduce cinco puntos numerados; PLABA30377698 ISO y TSAR45/95 ISO ablated también añaden listas, manteniendo orden temático/temporal. VISUAL FORMAT sigue presente y puede contribuir; el mecanismo no está demostrado.
- **Un resumen inicial no está asegurado por el prompt original.** En numerosos ejemplos la apertura es contexto o diseño y la conclusión aparece al final. En Cochrane CD009601 ISO, la cautela sobre comparar regímenes aparece ya en el primer párrafo de ambas versiones. No se fuerza una clasificación uniforme entre apertura temática y resumen.
- **Los cambios no son unidireccionales.** PLABA34477130 ISO pasa de una síntesis compacta a resultados detallados en listas con conclusión final; aumenta segmentación pero retrasa la síntesis. TSAR120 ISO+examples fusiona dos elementos de lista y conserva el consejo inicial.
- **Hay fragmentos que impiden comparar organización.** Cochrane CD009601/CD008053 ISO+examples ablated y CD007497 en distintas condiciones, y PLABA27630909 en ambas familias, acaban tras introducciones, números parciales o un título, aun con done_reason=stop. La original PLABA35008695 ISO también acaba antes de los hallazgos. Son observaciones textuales de esta muestra, no una tasa automática ni un diagnóstico de causa.
- **Distinguir cap de final abrupto.** PLABA34477130 ISO+examples original tiene length y queda sin conclusión; la ablación tiene stop y cierre completo. Los otros fragmentos con stop no se etiquetan como truncamientos confirmados por el cap. No se atribuyen a penalización, cuantización, stop sequences o contexto sin pruebas.
- **Fidelidad y formato son dimensiones separadas.** Cochrane CD004510 ISO+examples desarrolla TFU con un término que no aparece en la fuente proporcionada. No se verificó externamente su significado. Otros pares cambian formulaciones de resultados; no se presenta la estructura visible como validación clínica.

## Límites e interpretación

En las salidas que permiten una comparación sustantiva hay cambios heterogéneos y persistencia de organización. Los fragmentos impiden una conclusión general de equivalencia o ausencia de efecto del bloque. SARI no evalúa directamente la organización y los intervalos no significativos no validan cumplimiento ISO. No hubo cegamiento, jueces humanos, adjudicación ni acuerdo entre evaluadores. La muestra es pequeña, sistemática y no aleatoria, y está compartida entre modelos: no son 30 fuentes nuevas e independientes.

No se investigaron los identificadores repetidos de PLABA, conforme a la decisión del usuario. Persisten confusiones por longitud del prompt, cantidad de instrucciones, omisión y formato conservado, además de la identidad histórica del runtime/modelo no certificada. No se afirma efecto causal completo de ISO ni tasas globales de errores.

## Evidencia por caso

Los textos completos enfrentados y la fuente están en reviewed_pairs.html; reviewed_pairs.csv conserva texto, observaciones, referencias, longitud y motivo de terminación. Ninguna predicción se modificó.


### cochrane · iso · fila 0 · ID CD009601

Palabras: 261 → 195. Terminación: stop → stop.

Ambas aperturas presentan estudios y participantes e incluyen ya en el primer párrafo la insuficiencia de evidencia entre regímenes. No es un resumen separado, pero sí una cautela temprana que se conserva tras la ablación. La ablación comprime cinco párrafos en tres, agrupa comparaciones y conserva una conclusión final. La reducción de detalle no equivale por sí misma a pérdida de jerarquía.


### cochrane · iso · fila 31 · ID CD008053

Palabras: 198 → 203. Terminación: stop → stop.

Ambas salidas son un único párrafo largo con estudios, limitaciones, resultados y futuras investigaciones en orden parecido a la fuente. No anteponen un resumen de los hallazgos. La ablación cambia 2 días por 2–3 días, más próximo a 48–72 horas de la fuente, y simplifica vocabulario. La agrupación visual sigue siendo escasa en ambas.


### cochrane · iso · fila 62 · ID CD011655

Palabras: 162 → 181. Terminación: stop → stop.

La original agrupa estudio, comparación clínica y limitaciones en párrafos. La ablación convierte la secuencia en cinco puntos numerados sin mover la conclusión clínica al principio. La numeración añade estructura visible pese a retirar el bloque; VISUAL FORMAT permanece. Cambia también available por applicable en los resultados, por lo que las diferencias no son solo de organización.


### cochrane · iso · fila 93 · ID CD004510

Palabras: 106 → 137. Terminación: stop → stop.

Ambas son párrafos únicos que siguen estudios → heterogeneidad → cautela/conclusión. La ablación amplía detalles metodológicos y mantiene el resultado inconcluso después de los antecedentes. No hay un resumen inicial independiente ni una pérdida clara del orden lógico; TFU sigue sin desarrollarse.


### cochrane · iso · fila 124 · ID CD007497

Palabras: 206 → 19. Terminación: stop → stop.

La original ofrece una síntesis relativamente temprana de ausencia de diferencias de dosis y después una lista que repite puntos. La ablación solo devuelve una introducción numerada de 19 palabras, terminada en Milinkovic 2. Aunque done_reason=stop, el fragmento carece de resultados y cierre. No puede valorarse como una versión completa con peor organización ni atribuirse al límite de 512 tokens.


### cochrane · iso_examples · fila 0 · ID CD009601

Palabras: 222 → 10. Terminación: stop → stop.

La original distribuye antecedentes, comparaciones, seguridad y conclusión en cuatro párrafos, sin conclusión primero. La ablación solo devuelve 10 palabras y acaba en Some studies compared:. El registro dice stop. No hay contenido suficiente para comparar jerarquía, agrupación o resumen; la ausencia de conclusión queda confundida con un final abrupto no diagnosticado.


### cochrane · iso_examples · fila 31 · ID CD008053

Palabras: 214 → 7. Terminación: stop → stop.

La original agrupa métodos, resultados, limitaciones y necesidad de investigación en párrafos. La ablación acaba tras Two studies with a total of 1, con siete palabras y done_reason=stop. Ese fragmento no permite evaluar el efecto estructural de retirar el bloque y no debe clasificarse como truncamiento confirmado por límite.


### cochrane · iso_examples · fila 62 · ID CD011655

Palabras: 159 → 172. Terminación: stop → stop.

Ambas versiones mantienen dos párrafos, primero estudio/resultados disponibles y después resultados ausentes e interpretación. La conclusión permanece al final. La ablación amplía algunas formulaciones sin un resumen inicial separado ni reordenamiento global.


### cochrane · iso_examples · fila 93 · ID CD004510

Palabras: 161 → 146. Terminación: stop → stop.

La original separa antecedentes/heterogeneidad y conclusión en dos párrafos; la ablación los integra en uno y conserva la secuencia. La original repite al final ausencia de daños y la ablación no. Ambas expanden TFU como Transcutaneous Fetal Monitoring, desarrollo no sustentado por el fragmento fuente proporcionado. No se ha verificado externamente el acrónimo; no usar esa expansión como evidencia de fidelidad.


### cochrane · iso_examples · fila 124 · ID CD007497

Palabras: 15 → 17. Terminación: stop → stop.

Ambas salidas son fragmentos de búsqueda/citas: la original acaba en McComsey 2 y la ablación en Sanchez-Conde 2. Ambas registran stop. Ninguna permite examinar la organización de los resultados o la conclusión. Su incompletitud aparente no se debe equiparar a llegar al límite de generación.


### plaba · iso · fila 0 · ID 30377698

Palabras: 214 → 197. Terminación: stop → stop.

Ambas siguen contexto, método, resultados y conclusión; la conclusión sobre el quiste queda al final. La ablación convierte el contenido en cinco puntos numerados y elimina la nota final de la original sobre conocimientos médicos. La numeración conserva la secuencia sin añadir resumen inicial independiente.


### plaba · iso · fila 36 · ID 6445384

Palabras: 136 → 137. Terminación: stop → stop.

Ambas utilizan listas numeradas, con objetivo primero y relevancia clínica al final. La ablación añade un punto sobre células estimuladoras y aumenta de seis a siete elementos, manteniendo la temporalidad de los efectos. La estructura de lista persiste sin el bloque retirado.


### plaba · iso · fila 73 · ID 34477130

Palabras: 88 → 221. Terminación: stop → stop.

La original es un párrafo compacto que presenta ya pronto el resultado de la comparación. La ablación amplía mucho la salida, presenta primero diseño/muestra y distribuye cifras en listas de resultados y subgrupos, con conclusión final. Hay más detalle y organización explícita, pero se retrasa la síntesis. No es una mejora o empeoramiento unidireccional y no se adjudica aquí la dirección clínica de cada cifra.


### plaba · iso · fila 110 · ID 27630909

Palabras: 34 → 29. Terminación: stop → stop.

La original incluye título y Study Details, pero se corta en Dec 2; la ablación termina en from 2 tras contexto y objetivo. Ambas registran stop. Los encabezados de la original no compensan la ausencia de resultados; no puede compararse la completitud estructural con estos fragmentos.


### plaba · iso · fila 147 · ID 35008695

Palabras: 47 → 152. Terminación: stop → stop.

La original solo llega a antecedentes sobre ferritina y termina después de H-ferritin (FTH), sin cerrar la comilla ni presentar el estudio en ratones; registra stop. La ablación desarrolla el contenido en siete puntos numerados, con sublistas y hallazgos/conclusión. La diferencia es de cobertura y estructura a la vez; no demuestra que retirar el bloque causara mayor calidad.


### plaba · iso_examples · fila 0 · ID 30377698

Palabras: 190 → 236. Terminación: stop → stop.

Ambas mantienen antecedentes, método, resultados y conclusión. La ablación explica más términos y convierte resultados en una lista introducida por Here's what we found. La conclusión no se adelanta al comienzo. La longitud aumenta, con más segmentación visible y sin pérdida uniforme del orden temático.


### plaba · iso_examples · fila 36 · ID 6445384

Palabras: 117 → 141. Terminación: stop → stop.

Ambas usan un párrafo entre comillas, que sigue objetivo → efectos/dosis → temporalidad → relevancia clínica. La ablación conserva más términos y detalles celulares. No añade resumen inicial ni reorganiza globalmente; la expansión es principalmente de contenido.


### plaba · iso_examples · fila 73 · ID 34477130

Palabras: 245 → 202. Terminación: length → stop.

Ambas abren con diseño y muestra y agrupan resultados en listas. La original alcanza el límite y se corta en The study concluded that MPCNL (length); la ablación es más corta y llega a una conclusión completa (stop). La diferencia del cierre está confundida por el cap. También cambia la dirección expresada para el descenso de hemoglobina; no tratar la mejor completitud aparente como una validación de exactitud clínica.


### plaba · iso_examples · fila 110 · ID 27630909

Palabras: 13 → 69. Terminación: stop → stop.

La original devuelve únicamente un título de 13 palabras, registrado como stop. La ablación añade Introduction, Goal y comienzo de métodos, pero se corta en from 2006 to 2, también con stop. No hay resultados ni conclusión en ninguna; no son versiones completas para valorar resumen inicial o jerarquía final.


### plaba · iso_examples · fila 147 · ID 35008695

Palabras: 195 → 218. Terminación: stop → stop.

Ambas tienen tres párrafos de contexto, estudio en ratones y mecanismo/conclusión. La ablación amplía explicaciones y conserva el mismo orden. No se añade un resumen inicial separado y la información principal sobre ratones sigue después del contexto.


### tsar2025 · iso · fila 0 · ID 21

Palabras: 44 → 39. Terminación: stop → stop.

Ambas son párrafos breves que siguen generalización → ejemplos → vínculo con experiencias y emociones. La ablación quita las comillas externas y reformula. La recomendación interpretativa sigue al final y no aparece un resumen independiente.


### tsar2025 · iso · fila 24 · ID 45

Palabras: 74 → 84. Terminación: stop → stop.

La original es un párrafo narrativo; la ablación convierte la misma cronología casa → café → coworking en cinco puntos numerados. La solución sigue al final. La lista preserva el orden de acontecimientos pese a retirar la instrucción cronológica explícita.


### tsar2025 · iso · fila 49 · ID 70

Palabras: 66 → 67. Terminación: stop → stop.

Ambas son narraciones continuas con orden llegada → café → espera → ratas. La ablación antepone 1. al único párrafo, sin crear una lista temática real ni un resumen. La cobertura y longitud son parecidas.


### tsar2025 · iso · fila 74 · ID 95

Palabras: 62 → 79. Terminación: stop → stop.

La original mantiene un párrafo; la ablación distribuye lugares, inquietud, silencio y cobertura telefónica en cuatro puntos numerados. No adelanta una síntesis distinta; conserva el recorrido de la fuente y aumenta la separación visual.


### tsar2025 · iso · fila 99 · ID 120

Palabras: 28 → 41. Terminación: stop → stop.

Ambas empiezan con el consejo y usan listas, viñetas en la original y cinco puntos numerados en la ablación. La recomendación ya aparece al principio de la fuente. La ablación cambia el orden de explicación/consejos y añade formulaciones sobre sinceridad y crítica escasa; no todo el contenido adicional está explícito en la fuente.


### tsar2025 · iso_examples · fila 0 · ID 21

Palabras: 47 → 48. Terminación: stop → stop.

Ambas son párrafos entre comillas con la misma secuencia de interpretación de sueños. La ablación divide más claramente las frases pero mantiene el consejo al final. No hay un resumen inicial separado ni cambio global de agrupación.


### tsar2025 · iso_examples · fila 24 · ID 45

Palabras: 91 → 96. Terminación: stop → stop.

Ambas mantienen en un párrafo la cronología casa → café → coworking y la satisfacción final. La ablación simplifica vocabulario y divide algunas oraciones sin cambiar la posición de la solución ni añadir resumen inicial.


### tsar2025 · iso_examples · fila 49 · ID 70

Palabras: 68 → 63. Terminación: stop → stop.

Ambas mantienen una narración de un párrafo, con llegada, café, demora del trabajo, ruido futuro y ratas. Las diferencias son locales, como relax frente a enjoy the quiet time. No se observa un reordenamiento global ni un resumen inicial independiente.


### tsar2025 · iso_examples · fila 74 · ID 95

Palabras: 70 → 65. Terminación: stop → stop.

Ambas conservan lugares → inquietud/preguntas → silencio → cobertura telefónica en un párrafo. La ablación recupera las preguntas directas de la fuente; la original las expresa indirectamente. No cambia la ubicación del cierre ni añade una síntesis inicial.


### tsar2025 · iso_examples · fila 99 · ID 120

Palabras: 45 → 50. Terminación: stop → stop.

Ambas abren con el mismo consejo y mantienen una lista numerada. La ablación fusiona los elementos tercero y cuarto de la original en un tercer punto más largo. La prioridad inicial ya está en la fuente; cambia la granularidad de agrupación, no la organización general.
