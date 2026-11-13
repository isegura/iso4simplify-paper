"""Non-generative screening of all 36 original Mixtral configurations."""
from pathlib import Path
import sys
import hashlib
import json
import html
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from generate_systematic_error_analysis_512 import NUMERIC_END_RE, classify_row, parse_metadata

def main():
    rows=[];hashes={}
    detector=ROOT/'generate_systematic_error_analysis_512.py'
    hashes[str(detector.relative_to(ROOT))]=hashlib.sha256(detector.read_bytes()).hexdigest()
    paths=sorted((ROOT/'outputs/mixtral_512').glob('predictions_*.csv'))
    assert len(paths)==36
    for path in paths:
        hashes[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
        meta=parse_metadata(path)
        for index,row in pd.read_csv(path,keep_default_na=False,dtype={'text_id':str}).iterrows():
            text=str(row.prediction).strip()
            flags=classify_row(meta,row.to_dict())
            baseline=bool(flags['ended_abruptly'])
            # Broad screen only; lists, quotations and notes can lack final punctuation.
            additional=bool(text) and row.done_reason=='stop' and not baseline and not text.rstrip('"\u201d\u2019\x27* ').endswith(('.','!','?'))
            rows.append(dict(dataset=meta['dataset'],prompt=meta['prompt_type'].replace('minimal','baseline'),
                strategy=meta['strategy'] if meta['sampling']=='-' else meta['strategy']+'_'+meta['sampling'],
                row_index=index,text_id=row.text_id,source_file=path.name,
                done_reason=row.done_reason,eval_count=int(row.eval_count),
                existing_detector_candidate=baseline,additional_punctuation_screen_candidate=additional,
                reached_token_limit=row.done_reason=='length',empty_output=not text,
                candidate_reason=('numeric_ending' if NUMERIC_END_RE.search(text) else 'very_short_unpunctuated') if baseline
                    else ('no_terminal_punctuation_needs_review' if additional else ''),
                ending=text[-180:],prediction=row.prediction,original=row.original))
    frame=pd.DataFrame(rows)
    assert len(frame)==4476
    old=pd.read_csv(ROOT/'error_analysis_candidates_512/systematic_error_flags_512.csv')
    assert frame.existing_detector_candidate.sum()==int(old[old.model.str.contains('mixtral')].ended_abruptly.sum())
    frame.to_csv(HERE/'all_outputs_screening.csv',index=False)
    candidates=frame[frame.existing_detector_candidate | frame.additional_punctuation_screen_candidate]
    candidates.to_csv(HERE/'candidate_entries.csv',index=False)
    summary=frame.groupby(['dataset','prompt','strategy'],sort=False).agg(
        n=('row_index','size'),existing_detector_candidates=('existing_detector_candidate','sum'),
        additional_candidates_needing_review=('additional_punctuation_screen_candidate','sum'),
        reached_token_limit=('reached_token_limit','sum'),empty_outputs=('empty_output','sum')).reset_index()
    summary.to_csv(HERE/'by_configuration.csv',index=False)
    table=summary.pivot(index=['dataset','prompt'],columns='strategy',values='existing_detector_candidates').reindex(columns=['zero','one','few_random','few_metric'])
    table.to_csv(HERE/'existing_detector_counts_table.csv')
    body=['<!doctype html><meta charset="utf-8"><title>Mixtral: candidate abrupt endings</title>',
        '<style>body{font:16px sans-serif;max-width:1100px;margin:auto}pre{white-space:pre-wrap}details{border-top:1px solid #bbb;padding:12px}</style>',
        '<h1>Candidate endings — not definitive human labels</h1><p>354 existing-detector candidates plus 92 broader punctuation-screen candidates. Only done_reason=stop. Token-limit outputs are tabulated separately.</p>']
    for r in candidates.itertuples():
        body.append(f'<details><summary>{html.escape(str((r.dataset,r.prompt,r.strategy,r.row_index,r.text_id)))} — {r.candidate_reason}</summary><h3>Source</h3><pre>{html.escape(r.original)}</pre><h3>Full prediction</h3><pre>{html.escape(r.prediction)}</pre></details>')
    (HERE/'candidate_review.html').write_text('\n'.join(body),encoding='utf-8')
    report=f'''# Mixtral: screening de finales abruptos

Ámbito: 36 configuraciones originales, 4476 respuestas. No se incluyen ablaciones ni se generan nuevas salidas.

El detector existente marca **{int(frame.existing_detector_candidate.sum())} candidatos** con done_reason=stop. Se reproduce exactamente su recuento previo. Detecta terminaciones numéricas sospechosas y respuestas de diez palabras o menos sin puntuación final. No es un clasificador validado ni un recuento exhaustivo de fallos confirmados.

Una búsqueda más amplia añade **{int(frame.additional_punctuation_screen_candidate.sum())} candidatos** sin puntuación terminal, excluidos los ya marcados. Incluye falsos positivos esperables: listas completas, citas o notas. No deben sumarse como fallos confirmados. Los 446 candidatos pueden revisarse con fuente y salida completas en candidate_review.html; candidate_entries.csv contiene fila, ID, configuración y texto completo.

Hay además **{int(frame.reached_token_limit.sum())} salidas con done_reason=length**, separadas de estos candidatos stop, y **{int(frame.empty_output.sum())} salidas vacías**. Alcanzar el límite no prueba por sí solo que el final sea lingüísticamente incompleto. Tampoco stop prueba que sea completo.

Las 36 configuraciones tienen al menos un candidato del detector existente. by_configuration.csv contiene denominadores y ambos grupos, límites y vacíos; existing_detector_counts_table.csv ofrece la tabla compacta.

Los IDs repetidos de PLABA se conservan: se cuentan respuestas por fila y configuración, no documentos independientes. No inferir que todos los fallos tengan la misma causa ni que respondan a la penalización de repetición. Estos datos amplían la evidencia más allá de los cuatro ejemplos exactos del revisor y deben tenerse en cuenta antes de fijar el subconjunto diagnóstico.

No se modifica el diseño de generación ni se ejecuta el comando de penalización como parte de este análisis. Una revisión contextual completa y etiquetado independiente siguen pendientes; no se afirma una tasa humana definitiva.
'''
    (HERE/'REPORT.md').write_text(report,encoding='utf-8')
    for relative,sha in hashes.items():
        assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==sha
    (HERE/'provenance.json').write_text(json.dumps(dict(source_sha256=hashes,
        source_files_verified_unchanged=True,scope='36 original Mixtral configurations',
        human_adjudication_complete=False),indent=2),encoding='utf-8')
    print(table.to_string());print(report[:1700])

if __name__=='__main__': main()
