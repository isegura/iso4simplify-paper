# Concern 4 — revisión de cierre, 24/10/2026

**Diagnóstico acordado completado; integración pendiente.** No se proponen nuevas generaciones por este cierre.

- 31 fuentes compartidas de Cochrane, Mixtral ISO, zero y few-random; 62 pares de respuestas, no 62 fuentes independientes.
- Finales aparentemente incompletos: zero 17→8 y few-random 9→5; separar cortes stop y terminaciones length. La revisión es exploratoria del asistente, no validación humana independiente.
- Subconjunto seleccionado para diagnóstico, no muestra representativa ni estimación de prevalencia. Comparación histórica: no atribuir el cambio exclusivamente a la penalización ni asegurar una mejora global de calidad.
- Tabla 3: conservar la propuesta de señalar 29/125 (23.2%) salidas capadas en ISO+examples zero-shot de Cochrane. No afirmar análisis excluyendo esas filas. El diagnóstico ISO no resuelve esa celda ISO+examples ni el ejemplo PLABA.
- Tokens de entrada: son los procesados registrados, no una tokenización independiente del prompt completo; no descartan por sí solos recorte previo.
- Hardware/formatos confirmados por la autora; la copia actual de main.tex ya contiene RTX 5080 y ambas cuantizaciones. No duplicar paper_quantization.tex.

## Pendiente editorial

Integrar nota de tabla, resumen y materiales de S2; coordinar lenguaje sobre finales con Concern 7 sin sumar tasas o confundir detección con juicio contextual; revisar PDF y referencias finales. No se han recalculado métricas ni pruebas estadísticas del diagnóstico.
