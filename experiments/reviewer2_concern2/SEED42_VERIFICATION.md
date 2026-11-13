# Comprobación de los training y semilla 42

Actualización posterior a la verificación: el 23 de octubre de 2026 se corrigieron por petición de la autora las seis etiquetas erróneas en los prompts few-random. Las afirmaciones de abajo sobre prompts sin modificar corresponden a la comprobación histórica previa. Véanse prompt_label_correction/changes.json y las copias históricas; el contenido y orden de las demostraciones no cambiaron.

Se copiaron los tres CSV aportados por la autora a data/cochrane/cochrane_train.csv, data/plaba/plaba_train.csv y data/tsar2025/tsar2025_train.csv. Se conservaron exactamente sus bytes y orden de filas, comprobados con SHA-256. No se sobrescribieron archivos diferentes.

## Reproducción de la selección original

Pandas sample(n=3, random_state=42) reproduce las tres parejas original/simplificado de cada dataset y su orden. Se cotejaron las 36 apariciones en los 18 prompts originales (tres datasets, tres tipos de prompt, one y few-random), normalizando solo espacios y delimitadores de formato. One-shot contiene la primera de las tres demostraciones.

| Dataset | Filas de training | Posiciones seleccionadas, base cero | IDs reales en orden |
|---|---:|---|---|
| Cochrane | 3568 | 976, 2751, 351 | CD008514, CD006611, CD004329 |
| PLABA | 635 | 523, 250, 428 | 15507061, 32784601, 23939641 |
| TSAR2025 | 40 | 19, 16, 15 | 10-b1, 09-a2, 08-b1 |

El tercer ejemplo de Cochrane aparece etiquetado como CD008514 en los prompts, pero su contenido corresponde a CD004329. En PLABA, el tercero aparece etiquetado como 15507061 pero corresponde a 23939641. Los textos coinciden con las filas sorteadas: el error es de etiqueta, no una repetición de contenido. No se corrigieron los prompts usados históricamente ni se repitieron sus generaciones. Documentar la errata; no confundir la verificación de selección con una afirmación de que los identificadores escritos no puedan influir en un modelo.

## Semillas nuevas

43 y 44 son semillas válidas; no existe una ventaja estadística intrínseca por elegir números consecutivos. Sin embargo, en TSAR, la primera demostración de 43 es 10-b1, idéntica a la primera de 42: el one-shot resultaría repetido con los demás parámetros iguales. No se obtendrían tres entradas one-shot distintas para TSAR usando 42, 43 y 44.

Se inspeccionaron también 45 y 46 antes de generar resultados. La primera de 45 repite 03-b1 de 44. Si se exige tener tres entradas one-shot distintas, una alternativa disponible es conservar 42 y utilizar 44 y 46: en TSAR las primeras serían 10-b1, 19-a2 y 02-b1. Ese criterio debe declararse antes de ejecutar y no presentarse como muestreo sin restricciones. No se escogieron semillas por sus puntuaciones: todavía no hay salidas ni métricas nuevas. La decisión final de semillas queda pendiente.

candidate_seed_demonstrations.csv y candidate_seed_overlaps.csv conservan TODAS las selecciones inspeccionadas (42 a 46), no solo las alternativas favorables al criterio de diversidad. training_test_overlap.csv distingue coincidencias exactas de texto normalizado de IDs compartidos; no prueba ausencia de solapamiento semántico o documental. Ninguna de las demostraciones inspeccionadas coincide exactamente con los textos test tras normalizar espacios.

Los training, versiones de paquetes y hashes están en training_seed_verification.json. La comprobación se limita a selección y contenido: no se ejecutó el notebook ni ningún modelo y no se generaron prompts nuevos. No se subió nada a GitHub.
