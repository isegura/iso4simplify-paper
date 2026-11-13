# Recuperación por similitud con restricción de contexto

Preparación: 2 de noviembre de 2026. **Primer paso completado, sin generar simplificaciones.** Las selecciones están separadas de la preparación antigua y aún no son el experimento final: falta decidir la política de referencias TSAR y preparar el manifiesto/comandos definitivos.

## Resultado

- Se han construido **1119 archivos de instrucciones por entrada**, compartidos entre ambos modelos.
- Se han comprobado **2238 prompts completos** (373 filas × tres tipos de prompt × dos modelos).
- Todos cumplen: **entrada + 512 de salida + 64 de margen <=8192**.
- El margen real mínimo después de reservar salida es **65 tokens**.
- Los ejemplos de **298/373 filas** son los mismos del top-3 original. Cambian 75 filas: **61 Cochrane y 14 PLABA**; TSAR no cambia con su política de referencia actual.
- En las filas modificadas se mantienen dos ejemplos originales en 66 casos y uno en nueve. No se obliga a conservar el ejemplo de mayor similitud: prescindir de él en un caso puede permitir un conjunto más relevante que quepa.
- El ejemplo seleccionado más lejano está en el **puesto 23**, frente al puesto 3548 de la prueba de viabilidad anterior.

## Regla de selección y justificación

Se maximiza la suma (o media) de los tres cosenos fuente-fuente almacenados, entre documentos elegibles distintos, sujeto a que los seis prompts completos quepan. El orden de presentación de las demostraciones se fija por similitud decreciente, con desempate por fila de entrenamiento. La optimalidad se refiere a esa puntuación almacenada, pool/referencia y orden fijados; no al rendimiento de simplificación ni a otros encoders, órdenes o políticas de referencia.

La búsqueda enumera ternas en orden decreciente de puntuación conjunta. Las ternas vecinas incrementan un rango, por lo que su puntuación no puede aumentar, y todas las ternas son alcanzables. La primera que satisface la restricción tiene la mejor puntuación factible, a la precisión numérica de los cosenos almacenados. El predicado de presupuesto no se aproxima por caracteres ni por sumas de longitudes: se tokeniza cada prompt completo antes de aceptar. No se usa ningún resultado SARI ni simplificación generada para elegir ejemplos.

Se fijó una parada computacional de 5000 evaluaciones de ternas por entrada. Ningún caso alcanzó el límite; el máximo fue 427. No hubo fallback hacia un ejemplo corto alejado del ranking ni se aseguró que los dos primeros fueran intocables. Las tres pruebas sintéticas del buscador verifican coincidencia con enumeración exhaustiva, casos de factibilidad no aditiva, documentos repetidos, empates y rechazo explícito al alcanzar el límite.

## Comparación con el intento anterior

El intento anterior priorizaba mantener los dos primeros y podía completar con un tercer texto poco relacionado. La nueva regla maximiza la relevancia del conjunto y añade un margen de 64 tokens.

De las 373 soluciones anteriores, 348 también cumplen el margen nuevo de 64. En esos casos comparables, la puntuación conjunta nueva es mayor en 13 y coincide en 335; **no es menor en ninguno**. Los otros 25 casos anteriores no cumplían la reserva nueva y no se presentan como un empeoramiento de similitud bajo iguales condiciones.

Respecto al top-3 sin restricción, la pérdida media del coseno medio en las 75 filas cambiadas es 0.01373. Es una descripción de la función de recuperación, no una pérdida de calidad humana o de SARI medida. El incremento de 71 a 75 filas cambiadas frente al estudio previo se debe al criterio más conservador y se documenta, sin descartar entradas.

## Integridad y tokenización

Se reutilizaron el encoder y los embeddings fuente completos ya congelados; no hubo nuevas llamadas al encoder, GPU ni generación. Las instrucciones originales, textos fuente y pares de demostración se mantienen completos. La selección por entrada se comparte entre ambos modelos y los tres prompts. La política de exclusiones de self-match, fuentes de test y documentos repetidos se conserva.

Ollama se actualizó desde la preparación anterior: la versión local observada es 0.40.13 y el build nativo 39febd2ad. Se creó un wrapper de vocabulario separado, con su DLL fijada por hash y ABI contrastada con la cabecera oficial, sin cambiar el contador antiguo. Las plantillas y manifiestos de modelo siguen coincidiendo con los anteriores. Los conteos se revalidaron contra las mismas **108 entradas históricas, con 108 coincidencias**. No se llamó a chat/generate ni se cargaron tensores de inferencia. Estos datos no certifican identidad de todos los detalles de los runtimes históricos.

La selección fija de referencia por fuente de entrenamiento sigue siendo la anterior: TSAR usa la primera fila (A2). **No se ha resuelto aún esa decisión**, ni se presenta esta preparación como evidencia a favor de A2 o B1. Cambiarla requerirá recalcular los prompts afectados y su comprobación antes de lanzar.

## Archivos y uso

- METHOD.md: regla fijada antes de esta búsqueda.
- selected_examples.csv: ejemplos completos, cosenos, IDs y rangos.
- prompt_index.csv y prompts/: instrucciones por entrada y sus hashes.
- token_counts.csv y summary.csv: comprobación de todas las combinaciones y máximos por grupo.
- selection_changes.csv: cambios respecto al top-3 sin presupuesto.
- comparison_to_previous_attempt.csv: comparación con el intento que preservaba prefijos.
- tokenizer_revalidation.csv: las 108 comprobaciones históricas.
- complete.json e integrity_verification.json: procedencia, parámetros y controles.

No ejecutar los comandos antiguos pensando que usan estas selecciones: el manifiesto activo antiguo sigue intacto. Primero cerrar TSAR y congelar la nueva configuración. El repositorio GitHub y las propuestas editoriales sin recuperación no se han actualizado automáticamente por esta preparación.

Fuente técnica de la ABI: https://github.com/ggml-org/llama.cpp/blob/39febd2ad/include/llama.h . La evidencia principal es la biblioteca local hashada y los conteos reproducidos, no una suposición de que la rama de una biblioteca no cambie.
