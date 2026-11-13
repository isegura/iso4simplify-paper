"""Export fixed contextual assistant notes for the frozen sample; not a classifier."""
from pathlib import Path
import hashlib
import html
import json
import pandas as pd

HERE = Path(__file__).resolve().parent
SOURCE = HERE/'screening/spot_check_sample.csv'
EXPECTED = 'c75c2bea493384841ed99fe4339f3a6ff022de6065fd407cf13b298f66135ffd'
# Labels refer only to the sampled indicator, not overall simplification quality.
DECISIONS = [
 ('indicator_supported', 'Encabezado añadido Simplified Text; además hay una nota sobre las instrucciones. No es un juicio sobre el cuerpo simplificado.'),
 ('false_positive_for_incomplete_ending', 'La última viñeta sobre percepciones de los padres es una unidad completa. La falta de punto no demuestra corte.'),
 ('false_positive_for_unexplained_acronym', 'FF/VI se asocia explícitamente a fluticasone furoate and vilanterol; TIO a tiotropium. La heurística no reconoce esa asociación ni expansiones de una sola palabra.'),
 ('indicator_supported', 'Here is the simplified text es un preámbulo de la respuesta, separado del contenido.'),
 ('false_positive_for_incomplete_ending', 'Termina en una viñeta completa: Lower in trisomies 18 and 13. La fuente también menciona esas trisomías. El 13 terminal activa la regla numérica.'),
 ('false_positive_for_incomplete_ending', 'La última viñeta propone analizar a familiares para detectar BHD. Es una acción completa sin punto final.'),
 ('false_positive_for_unexplained_acronym', 'OA está explicado como osteoarthritis (OA); el detector exige al menos dos palabras en la expansión. RA también está definido.'),
 ('indicator_supported', 'Here is the simplified text y una nota final sobre el seguimiento de instrucciones constituyen metatexto añadido.'),
 ('false_positive_for_incomplete_ending', 'La última viñeta sobre una habitación usada como almacén es completa. No se observa final interrumpido.'),
 ('indicator_supported', 'NEOs y PHAs se mantienen sin desarrollar o explicar en la salida; NASA también se conserva sin expansión. La familiaridad de NASA no se evalúa.'),
 ('apparent_incomplete_ending', 'We looked at 1 deja una cantidad y la construcción sin completar. La fuente comienza con 13 ensayos y 16112 participantes.'),
 ('apparent_incomplete_ending', 'Termina en over 1,600,00 frente a 1601515 participantes en la fuente; la cantidad queda aparentemente cortada.'),
 ('indicator_supported', 'ICU aparece en ICU patients sin desarrollo en la salida. COPD sí se desarrolla; la observación no implica por sí sola falta de comprensión.'),
 ('indicator_supported', 'Simplified Text es un encabezado de respuesta añadido. El cierre de Markdown también es anómalo, pero no se etiqueta como corte.'),
 ('apparent_incomplete_ending', 'La fecha termina en July 2; la fuente dice July 2007 to July 2009. El intervalo queda sin completar.'),
 ('apparent_incomplete_ending', 'La fecha termina en 8.8% in 2 frente a 2010 en la fuente; hay una terminación claramente incompleta.'),
 ('mixed_indicator', 'BHD sí está explicado como Birt-Hogg-Dubé syndrome, aunque la heurística no lo reconoce. COPD y CT quedan sin expansión; FLCN tiene una explicación funcional parcial como gen supresor de tumores.'),
 ('false_positive_for_preamble', 'Here is some good news about violence reformula la primera idea de la fuente, que expresa optimismo. Es contenido, no una presentación del proceso de reescritura.'),
 ('apparent_incomplete_ending', 'Pi and Richard Parker spend 2 queda sin duración/unidad; la fuente indica 227 días en el bote.'),
 ('apparent_incomplete_ending', 'Acaba en around 140,00 frente a 140000 sueños en la fuente; la cifra parece cortada.'),
 ('mixed_indicator', 'NASA no se desarrolla, pero NEOs se explica funcionalmente como medium-sized space rocks aunque las iniciales no coincidan. PHAs sí se desarrolla. El contador no distingue familiaridad de siglas ni explicación funcional.'),
]


def main():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError('Sample changed; fixed review notes do not apply')
    frame = pd.read_csv(SOURCE, keep_default_na=False)
    if len(frame) != len(DECISIONS):
        raise ValueError('Unexpected sample')
    frame['review_label'] = [r[0] for r in DECISIONS]
    frame['review_note'] = [r[1] for r in DECISIONS]
    frame['reviewer'] = 'Codex assistant; exploratory, unblinded, not independent human evaluation'
    destination = HERE/'spot_check'
    if destination.exists():
        raise FileExistsError('Review output exists; preserve rather than overwrite')
    destination.mkdir()
    frame.to_csv(destination/'reviewed_21.csv', index=False)
    counts = frame.groupby(['sampled_flag','review_label']).size().reset_index(name='n')
    counts.to_csv(destination/'sample_labels.csv', index=False)
    body = ['<!doctype html><meta charset="utf-8"><title>Concern 7: exploratory spot check</title>',
        '<style>body{font:16px sans-serif;max-width:1100px;margin:auto}pre{white-space:pre-wrap}details{border-top:1px solid #bbb;padding:12px}</style>',
        '<h1>21 sampled outputs: assistant inspection</h1><p>Not a human evaluation, not a detector validation or population error-rate estimate.</p>']
    for i,r in frame.iterrows():
        body.append(f'<details><summary>{i+1}: {html.escape(r.instance_id)} — {html.escape(r.sampled_flag)}</summary><p><strong>{html.escape(r.review_label)}</strong>: {html.escape(r.review_note)}</p><h3>Full output</h3><pre>{html.escape(r.prediction)}</pre><h3>Source</h3><pre>{html.escape(r.original)}</pre></details>')
    (destination/'review.html').write_text('\n'.join(body), encoding='utf-8')
    (destination/'provenance.json').write_text(json.dumps(dict(sample_sha256=EXPECTED, outputs=21,
        assistant_inspection_only=True, blinded=False, human_evaluation=False, detector_thresholds_changed=False,
        population_precision_or_recall_estimated=False, review_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2),encoding='utf-8')
    print(counts.to_string(index=False))


if __name__ == '__main__':
    main()
