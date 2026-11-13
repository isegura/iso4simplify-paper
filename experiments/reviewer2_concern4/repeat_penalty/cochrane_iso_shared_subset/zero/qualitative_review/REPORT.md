# Revisión inicial zero-shot — penalización 1.0 frente a originales 1.1

Mixtral, ISO original, Cochrane: las 31 respuestas previstas están completas como archivos, no están vacías y corresponden a sus entradas congeladas. Se verificaron los hashes del manifiesto y de todas las fuentes. Es una revisión exploratoria del asistente sobre el cierre de las respuestas, sin cegamiento ni evaluadores humanos independientes; no es una evaluación exhaustiva de fidelidad o calidad.

## Resultado principal del diagnóstico

De los 15 textos con final aparentemente cortado en el zero-shot original, 10 presentan ahora un cierre completo y cinco siguen aparentemente cortados. Los cinco persistentes son CD010876, CD011627, CD009953, CD001499 y CD005015. Cuatro repiten literalmente la salida histórica: CD010876, CD011627, CD009953 y CD005015. CD001499 desarrolla más texto pero se corta después.

En las 31 entradas, los cortes con done_reason=stop pasan de 15 a 7. Las terminaciones por límite pasan de 2 a 1. La lectura de las salidas indica 17 finales incompletos en total antes y ocho después (sumando los cortes stop y los casos length aquí comprobados como incompletos). Estas son observaciones sobre el subconjunto seleccionado, no tasas representativas del dataset.

## Casos que impiden afirmar una solución uniforme

- CD009919 (fila 110): antes tenía una conclusión completa; ahora termina en RR 0.56, con done_reason=stop. Fue seleccionado por su fallo en few-random, no por un fallo previo en zero-shot.
- CD010683 (fila 94): antes terminaba con una conclusión completa; ahora alcanza 512 tokens y queda en lower with fibrin. También fue seleccionado por fallo en few-random.
- CD007074 (fila 53, grupo aleatorio): antes alcanzaba el límite y terminaba incompleto; ahora acaba prematuramente en MD −3.18, 9 con done_reason=stop. No es un fallo de completitud nuevo, sino un cambio de mecanismo de terminación observado.
- CD009611 (fila 36, grupo aleatorio): antes alcanzaba el límite en una palabra incompleta; ahora tiene cierre completo con done_reason=stop.

## Separación de los grupos seleccionados

stratum,n,historical_stop_cut,new_stop_cut,historical_limit,new_limit,historical_any_apparent_cut,new_any_apparent_cut,resolved_historical_zero_cut
historical_zero_shot_failure,15,15,5,0,0,15,5,10
random_from_remaining,10,0,1,2,0,2,1,0
selected_for_few_random_failure_only,6,0,1,0,1,0,2,0

Los 15 fallos zero-shot se analizan separadamente de seis textos seleccionados solo por fallos en few-random y de los diez sorteados del resto. En esos diez, hay nueve cierres completos y uno aparentemente cortado con stop en la nueva ejecución; los originales incluían dos cortes por límite y ocho cierres completos. No interpretar este pequeño grupo condicionado como una estimación aleatoria incondicional para Cochrane.

## Cierre completo no equivale a conservación de significado

En CD011790 (fila 49), el nuevo texto termina completo, pero afirma que los participantes EERW tuvieron alivio similar al continuar pregabalina o pasar a placebo. La fuente informa respuesta mantenida del 40% frente al 20%. En CD007104 (fila 12), used blindfolds interpreta literalmente el cegamiento del ensayo. Estas observaciones son ejemplos de errores de contenido; no se ha puntuado ni contado exhaustivamente la fidelidad de todas las salidas. No se recomienda describir todos los cierres resueltos como mejoras globales de calidad.

## Interpretación provisional

En estas entradas seleccionadas, la nueva ejecución con penalización 1.0 presenta menos finales aparentemente incompletos que las salidas históricas con 1.1. Persisten fallos y también aparecen regresiones. Es compatible con sensibilidad de algunas salidas a la configuración, pero sin una nueva condición contemporánea 1.1 no se puede atribuir causalidad exclusiva a la penalización.

No se han calculado métricas nuevas, pruebas estadísticas ni generalizaciones a otras configuraciones. La etapa few-random no forma parte de este informe y no se lee ni modifica. Las predicciones originales y los .tex se conservan intactos. paired_review.csv y reviewed_evidence.html contienen las comparaciones y decisiones de cada texto. La distinción de cortes vs límite se mantiene en todos los recuentos.
