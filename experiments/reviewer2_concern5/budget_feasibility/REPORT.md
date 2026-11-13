# Viabilidad de recuperación con presupuesto — 28/10/2026

**Resultado: sí existen tres demostraciones completas que caben en todas las entradas con contexto 8192 y salida reservada 512.** Esta es una prueba de viabilidad, no el nuevo experimento congelado ni una selección óptima demostrada. No se ha generado ninguna simplificación ni modificado la preparación activa.

## Alcance y resultado

- 373 filas de test, 1119 combinaciones entrada/tipo de prompt y 2238 combinaciones modelo/entrada/prompt, igual que el diseño original.
- Se conservan las mismas tres demostraciones entre ambos modelos y los tres tipos de prompt para cada entrada.
- Los 2238 prompts completos candidatos cumplen entrada+512 <=8192; máximo 8190, mínimo margen 2 tokens.
- 302/373 filas conservan exactamente el top-3 original y sus prompts originales.
- Se cambian las demostraciones de 71 filas: 58 Cochrane y 13 PLABA. En 68 filas se conserva dos de los tres ejemplos originales; en tres, solo uno.
- El ejemplo de mayor similitud se conserva en las 373 filas. Los dos de mayor similitud se conservan en 58 de las 71 filas modificadas.
- TSAR no cambia. La política de elegir la primera referencia de entrenamiento (A2 en la preparación actual) no ha sido resuelta ni alterada.
- No se recortan instrucciones, fuentes, referencias de demostración o texto objetivo. Se reutilizan los embeddings ya calculados, sin volver a ejecutar el encoder ni Ollama.

## Regla explorada, no adoptada como método definitivo

Se intenta mantener el top-3. Si no cabe, se busca una combinación conservando los dos ejemplos más próximos y sustituyendo el tercero. La búsqueda usa ejemplos completos cortos como testigos de viabilidad, y explora hasta los primeros 128 candidatos ordenados por coseno. Si no encuentra un testigo con los dos primeros, intenta conservar el primero y buscar una pareja que complete el presupuesto. Un último recurso de tres textos cortos no fue necesario.

La longitud en caracteres sirve únicamente para ordenar candidatos de búsqueda cortos; **nunca** para certificar que un prompt cabe. Todas las aceptaciones se basan en los tokens nativos de los seis prompts completos, incluyendo instrucciones, demostraciones, texto objetivo, plantilla de conversación y tokens especiales. La biblioteca y el renderizador son los contrastados con 108 conteos históricos en token_preflight.

No es una optimización global de similitud bajo presupuesto ni una prueba de que una combinación rechazada por la búsqueda acotada sea imposible. Las alternativas se han elegido sin observar simplificaciones o métricas de calidad. La primera búsqueda exhaustiva se interrumpió antes de producir evidencia final para sustituirla por esta búsqueda acotada; el código hashado en complete.json es el que produjo estos resultados.

## Coste de imponer la restricción

En las 71 filas cambiadas, la caída media de la similitud coseno media de las tres demostraciones es 0.03665; la máxima es 0.17579. Estas cifras describen el criterio de recuperación, no una pérdida medida de calidad de simplificación.

El caso más extremo selecciona una demostración en el puesto 3548 del ranking. Forzar la conservación de los dos primeros puede producir un tercer ejemplo muy poco relacionado. Por tanto, **no recomendaría congelar directamente estas selecciones como baseline final**: la prueba demuestra que el presupuesto es viable, pero hace falta definir una regla que equilibre la relevancia del conjunto y su longitud, en lugar de conservar siempre los dos primeros a cualquier coste. También conviene decidir si se reserva un pequeño margen adicional; aquí se comprobó exactamente el requisito 8192/512 acordado, sin introducir un nuevo límite.

## Archivos

- `source_selection_changes.csv`: cambios, método, número de ejemplos conservados, rangos y similitudes por fila.
- `candidate_selections.csv`: los tres ejemplos completos provisionales por fila y sus IDs/rangos/cosenos.
- `candidate_token_counts.csv`: las 2238 comprobaciones exactas de presupuesto.
- `summary.csv`: máximos y margen por modelo/dataset/prompt.
- `complete.json`: integridad y alcance de la búsqueda.

No se han escrito nuevos prompts en la carpeta activa ni creado comandos de generación para esta variante. El manifiesto congelado y los hashes de sus entradas siguen válidos. Las diferencias de ranking se conservan para revisar el diseño antes de lanzar.

## Siguiente decisión

Cerrar una política explícita de recuperación limitada por contexto (por ejemplo, buscar un conjunto relevante que quepa en lugar de priorizar rígidamente los dos primeros), decidir el margen y la referencia TSAR, volver a validar todos los prompts y solo entonces congelar el nuevo diseño. Este informe no cambia num_ctx, el número de ejemplos ni las condiciones históricas, y no inicia la siguiente fase automáticamente.
