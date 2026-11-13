# Concern 5 — comprobación de contexto completo

Fecha: 28 de octubre de 2026. **No lanzar todavía todos los bloques de recuperación con la preparación actual.** No se ha generado texto ni cambiado ningún prompt, demostración seleccionada, opción de inferencia o manifiesto congelado.

## Resultado

Se contaron los 1119 prompts por entrada con los dos vocabularios de modelo: **2238 combinaciones modelo/entrada**. El presupuesto requerido es prompt completo + 512 tokens de salida <=8192, es decir, hasta 7680 tokens de entrada.

| Modelo | Dataset / prompt | Casos fuera del presupuesto | Máximo tokens de entrada | Máximo entrada+512 |
|---|---|---:|---:|---:|
| Llama | Cochrane / ISO+examples | 2/125 | 7818 | 8330 |
| Mixtral | Cochrane / ISO+examples | 58/125 | 9104 | 9616 |
| Mixtral | PLABA / ISO+examples | 13/148 | 8996 | 9508 |

El resto de grupos cabe: 2165/2238 combinaciones cumplen el presupuesto. Las 73 combinaciones problemáticas corresponden a 71 filas fuente distintas; dos Cochrane fallan para ambos modelos. De las 73, 33 exceden 8192 tokens incluso sin reservar salida. Las otras 40 caben como entrada sola pero no con la reserva de 512. No se interpreta esto como 73 salidas truncadas observadas: todavía no se ha ejecutado la generación.

TSAR cabe con margen: máximos de entrada+512 para ISO+examples de 4583 en Llama y 5301 en Mixtral. Baseline e ISO caben en todos los datasets. PLABA ISO+examples con Llama llega a 8019 de presupuesto total y deja solo 173 tokens de margen.

## Cómo se contó

1. Se comprobó el manifiesto congelado y los hashes de instrucciones y datasets.
2. Se reconstruyó el mensaje de usuario a partir del f-string real de simplify_one_ollama en model_utils.py: instrucciones, tres demostraciones ya incluidas en el archivo, TARGET TEXT completo y bloque ANSWER. No se usaron caracteres como estimación.
3. Se aplicó el caso efectivo de plantilla para un mensaje de usuario, sin sistema ni herramientas, usando la plantilla del modelo instalado. Se verificó que el archivo de plantilla del almacén coincide con los metadatos consultados a Ollama.
4. Se cargó únicamente el vocabulario GGUF mediante la biblioteca llama.cpp incluida con Ollama: vocab_only y no_alloc, cero capas GPU, sin crear un contexto de inferencia. Los registros confirman `vocab only - skipping tensors`. Se incluyen los tokens especiales/BOS según el vocabulario y se tokeniza sin recortar.
5. La ABI se documentó con la cabecera oficial del build 620d2225c y la biblioteca local queda fijada por SHA-256. Si cambia, el contador se detiene para revisión.
6. Antes de contar recuperación, se validó la reconstrucción contra los prompt_eval_count guardados de 108 entradas (primera, central y última de las 18 configuraciones de selección 44 por modelo). **108 coincidencias, cero discrepancias**, sin volver a ejecutar esas generaciones.

Ollama 0.40.6 respondió 404 a /api/tokenize; no se utilizó /api/chat ni /api/generate. Los únicos accesos a la API fueron consultas de metadatos/versiones/modelos cargados y la comprobación de esa ruta de tokenización. La tokenización nativa es CPU y no evalúa los tensores del modelo.

Estos son conteos completos con los vocabularios y las plantillas actuales, contrastados con entradas registradas. No garantizan comportamiento idéntico si cambian modelos, librerías, plantillas, mensajes de sistema/herramientas u opciones, ni demuestran por sí solos ausencia de recorte previo en ejecuciones históricas.

## Archivos

- `summary.csv`: los 18 grupos modelo/dataset/prompt, mínimos/máximos y casos fuera de presupuesto.
- `per_input_token_counts.csv`: las 2238 comprobaciones con ID, fila, hashes, tokens y margen.
- `over_budget_cases.csv`: las 73 combinaciones que requieren resolver el presupuesto.
- `historical_count_validation.csv`: 108 contrastes offline/registro original.
- `complete.json`: evidencia e integridad; `all_fit` es false.
- `llama_vocabulary_load.log` y `mixtral_vocabulary_load.log`: carga solo de vocabulario.
- `llama_620d2225c.h`: cabecera de la ABI oficial utilizada.

Reproducción: `python experiments/reviewer2_concern5/preflight_context.py`. El programa rechaza sobrescribir un complete.json existente y requiere los mismos modelos, metadatos guardados y biblioteca local. No sustituye el estudio congelado ni modifica sus predicciones.

## Qué resolver antes de generar

No recortar silenciosamente instrucciones, demostraciones o texto fuente ni omitir las entradas largas. Hay dos diseños posibles:

1. **Recuperación con presupuesto de contexto:** mantener 8192/512 y buscar tres demostraciones completas que quepan, usando el presupuesto más restrictivo de ambos modelos y los tres prompts para conservar las mismas demostraciones en las comparaciones. Debe definirse la regla de ranking/selección, comprobar que las tres caben para todas las entradas y congelar una nueva preparación antes de generar. Esto cambia el retriever a una variante limitada por contexto y debe describirse así.
2. **Ampliar el contexto para el nuevo estudio:** mantener las demostraciones actuales, usando un contexto suficiente y comprobando compatibilidad/recursos. Cambia una condición frente a los controles históricos y requiere documentarla; no convertir las comparaciones en una atribución causal exclusiva al retriever.

La primera opción mantiene el límite histórico, pero requiere comprobar viabilidad y definir la selección. La segunda conserva el top-3 actual, pero cambia el contexto. Este informe no adopta ni aplica ninguna de las dos. La política de referencias TSAR (A2 en la preparación actual) también sigue pendiente de decisión antes de congelar el experimento final. Se pueden hacer comprobaciones adicionales sin inferencia antes de decidir el diseño.

## Fuentes técnicas

- Cabecera oficial fijada: https://github.com/ggml-org/llama.cpp/blob/620d2225c/include/llama.h (vocab_only y llama_tokenize).
- Implementación oficial de plantillas Ollama: https://github.com/ollama/ollama/blob/main/template/template.go (contexto de cómo se renderizan mensajes; la plantilla efectiva se leyó del modelo local).

La evidencia operativa son el build y la biblioteca hashados, las plantillas locales y las 108 coincidencias; no se afirma que la rama main de una biblioteca sea inmutable.
