# TSAR — política de referencia por fuente de entrenamiento

Decisión aplicada el 02/11/2026: hay 40 filas de entrenamiento pero 20 textos originales; cada uno tiene una simplificación A2 y otra B1. Se conserva una referencia por fuente.

Se ordenan los 20 identificadores fuente y se permutan con numpy.PCG64, semilla específica de asignación 42; las primeras diez fuentes reciben A2 y las restantes B1. La asignación concreta completa se guarda en tsar_reference_assignment.csv, por lo que no depende de volver a sortear ni de una versión implícita de una biblioteca. No se eligió semilla ni referencia a partir de resultados de simplificación. Esta semilla de asignación es distinta conceptualmente de la semilla de generación, aunque ambas valen 42.

La referencia asignada permanece fija para esa fuente en todas las consultas, prompts y modelos. Se recuperan fuentes originales por similitud; no se elige un nivel en función del texto de test ni se fuerza una cuota A2/B1 en los tres ejemplos de cada prompt. Los dos modelos y los tres tipos de prompt comparten los ejemplos y referencias de cada entrada.

Los embeddings proceden solo del texto original, idéntico en ambas filas A2/B1. El campo embedding_training_row_index conserva la fila usada en la caché fuente, mientras training_row_index identifica el par fuente/referencia realmente insertado. Se verificó igualdad exacta de la fuente; no se recalcularon embeddings ni se cambió su ranking.

El balance es del pool (10 fuentes A2, 10 B1), no una promesa de 150/150 apariciones entre las 300 demostraciones recuperadas. No se asigna un objetivo CEFR a las salidas. La evaluación prevista mantiene ambas referencias de test A2/B1; no se cambia por esta selección de entrenamiento.

La comparación con controles históricos sigue condicionada a sus conjuntos de demostraciones: no se afirma aislar causalmente la recuperación de toda diferencia de ejemplos, referencias o runtime. La política se documentará brevemente en el suplementario.
