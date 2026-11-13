# Longitud de entradas: Reviewer 2, Concern 4

Se analizaron las 72 configuraciones originales (8952 entradas). Los CSV originales contienen el contador de tokens procesados por Ollama. No se generaron nuevas simplificaciones ni se modificaron resultados ni archivos LaTeX.

## Cochrane, ISO+examples, few-shot (tres demostraciones)

| Model | Selection | Min | Median | Max | Headroom after 512 |
|---|---|---:|---:|---:|---:|
| llama | few_random | 4783 | 5097 | 5650 | 2030 |
| llama | few_metric | 4851 | 5165 | 5718 | 1962 |
| mixtral | few_random | 5689 | 6053 | 6724 | 956 |
| mixtral | few_metric | 5769 | 6133 | 6804 | 876 |

Los valores son `prompt_eval_count` de las ejecuciones originales. La columna final resta entrada observada y 512 tokens de salida al contexto de 8192.

En las 8952 entradas hay **0** casos cuyo contador observado más 512 supera 8192. El máximo global observado es **7219** tokens.

## Alcance e interpretación

Estos registros no muestran un exceso del presupuesto si el número de casos anterior es cero. Sin embargo, no permiten certificar que ninguna entrada original fuera recortada antes de procesarse. No confundir ausencia de evidencia de exceso con prueba de ausencia de truncamiento de entrada.

Se reconstruyó el mensaje de usuario completo con la misma expresión de `model_utils.py`: instrucciones (incluidas las demostraciones del archivo), TARGET TEXT y ANSWER. Se guardan caracteres, palabras por espacios y hash por entrada; estas medidas NO se presentan como tokens. La plantilla de chat del modelo no está incluida en esos caracteres. Los hashes actuales no certifican por sí solos que los prompts históricos no cambiaran.

Para cerrar una verificación independiente haría falta tokenizar las entradas completas con el tokenizador y plantilla de chat exactos de cada modelo. No se ha sustituido esa comprobación por un tokenizador de otro modelo ni por estimaciones de caracteres.

## Ubicación propuesta en los documentos

Paper: V.A, Models and Inference Environment, después del párrafo que fija 512 tokens y contexto 8192. Suplemento: S2, nuevo apartado sobre longitud de entrada y presupuesto de contexto, con `summary.csv` como tabla completa. Los .tex originales permanecen sin editar. La redacción final debe conservar la distinción entre tokens procesados y longitud independiente de la entrada completa.
