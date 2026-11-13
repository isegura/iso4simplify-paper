# Diagnóstico completado: penalización 1.0, Mixtral, ISO, Cochrane

Se verificaron las 31 respuestas de cada etapa (62 en total), con los mismos 31 textos fuente. No hay respuestas vacías. Cada archivo coincide con el trabajo y hash del manifiesto; solo se generó penalización 1.0. La comparación usa las predicciones históricas de 1.1, sin nuevo control contemporáneo 1.1. Los parámetros restantes y las demostraciones few-random se conservaron. Se revisaron las salidas y sus cierres; las dudas de contenido se contrastaron con el fragmento fuente. Revisión exploratoria del asistente, sin cegamiento ni evaluadores humanos independientes.

## Recuento por estrategia

| Estrategia | Cortes stop históricos → nuevos | Límite histórico → nuevo | Finales incompletos de cualquier tipo, históricos → nuevos |
|---|---:|---:|---:|
| Zero-shot | 15 → 7 | 2 → 1 | 17 → 8 |
| Few-random | 8 → 4 | 1 → 1 | 9 → 5 |

En este subconjunto, las salidas con length se comprobaron también textualmente como incompletas. No se aplica esa equivalencia como regla universal. Las 62 comparaciones corresponden a 31 fuentes comunes, no a 62 textos independientes. No se deben usar sus sumas como tasas representativas del corpus ni realizar un test que asuma independencia entre todas las filas.

## Fallos seleccionados y casos concretos

Zero-shot: diez de los 15 cortes stop históricos ahora tienen cierre completo; cinco persisten. Dos respuestas antes completas pasan a cortes nuevos (CD009919 con stop y CD010683 por límite); CD007074 ya estaba incompleta por límite y ahora se corta con stop.

Few-random: cuatro de los ocho cortes stop históricos se resuelven (CD005122, CD003122, CD003583, CD009919); tres persisten con stop (CD011424, CD007514, CD008720) y uno cambia a corte por límite (CD010683). La salida de CD007514 es literalmente idéntica a la original. CD006250, antes completa, ahora termina en un paréntesis abierto con stop. CD005015 pasa de corte por límite a cierre completo.

El ejemplo del revisor CD005122, “Four studies involving over 13,00”, se desarrolla ahora en few-random hasta resultados y conclusión. No se afirma que este ejemplo arregle todos los demás ni el caso “from 2006 to 2”, que pertenece a PLABA y queda fuera de este diagnóstico.

## Diez entradas aleatorias, separadas

En zero-shot, esas diez entradas tenían dos cortes por límite y ocho cierres completos; ahora tienen un corte stop y nueve cierres completos. En few-random, las diez tenían cierre completo y siguen teniendo cierre completo. Se sortearon entre las 104 filas que no pertenecían a la unión de fallos revisados: no constituyen una muestra incondicional del test completo. Las restantes entradas seleccionadas solo por fallo en la otra estrategia se informan separadamente en summary_by_selection_stratum.csv.

## Calidad del contenido

El cierre completo no acredita fidelidad ni calidad global. En zero-shot CD011790 aparece una comparación EERW de pregabalina y placebo incompatible con el 40% frente al 20% de la fuente. En few-random CD009919 se añade “esophageal cancer”, diagnóstico no sustentado por el fragmento fuente proporcionado. En few-random CD005122 se pierde la distinción entre ausencia declarada de conflictos y ausencia de información. Estas son observaciones ilustrativas, no una evaluación exhaustiva ni un recuento humano de errores semánticos.

## Conclusión que permite esta prueba

Las nuevas ejecuciones con penalización desactivada presentan menos finales aparentemente incompletos que las salidas históricas en ambas estrategias de este subconjunto. Persisten fallos y aparecen regresiones. El resultado es compatible con sensibilidad a la configuración, pero no establece que la penalización sea la causa exclusiva de los fallos históricos. No generalizar a otros modelos, prompts, datasets ni selecciones de demostraciones.

No se calculan métricas automáticas ni pruebas estadísticas en este informe. Las respuestas originales, resultados de ablación y .tex permanecen sin modificar. Tampoco se ha resuelto aquí la petición independiente de marcar en Tabla 3 o analizar la celda de ISO+examples zero-shot con 29/125 salidas por límite.

## Paso siguiente

La generación diagnóstica está terminada. Con estos resultados se puede preparar la tabla descriptiva del suplemento y una respuesta acotada al revisor, junto con la cuantización y longitudes ya auditadas. No hay motivo para lanzar automáticamente más configuraciones. Si se calculan métricas sobre estas 31 entradas, comparar exclusivamente el mismo subconjunto histórico y separar los grupos seleccionados; no compararlas con promedios del test completo.
