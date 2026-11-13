"""Export fixed exploratory endpoint review of the completed zero-shot stage.

No inference or semantic-metric model calls. Does not access few-shot results.
"""
from pathlib import Path
import hashlib
import html
import json
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
STAGE=HERE/'zero'
OUT=STAGE/'qualitative_review'
NEW_CUT_NOTES={
 27:'Persiste exactamente Two studies from 1987 and 2; la fuente fecha el segundo ensayo en 2004.',
 53:'La respuesta nueva termina en MD −3.18, 9, con el intervalo estadístico sin completar. La original también era incompleta, pero acababa por límite.',
 55:'Persiste exactamente 13 trials with 1, sin completar 1316 participantes ni desarrollar los resultados.',
 58:'Persiste exactamente 984 participants from 1, sin completar los 12 estudios de la fuente.',
 94:'Alcanza 512 tokens y termina en red blood cells ... lower with fibrin. El cierre queda incompleto; la original tenía una conclusión completa.',
 95:'Cambia la redacción y desarrolla más vías, pero termina Four studies, with 1, sin completar el grupo de 1456 participantes.',
 110:'La original tenía conclusión completa. La nueva se corta en RR 0.56, con el inciso estadístico abierto.',
 114:'Persiste exactamente In a 2, sin completar la actualización de 2019 ni desarrollar el estudio.',
}
QUALITY_NOTES={
 12:'Cierre completo, pero traduce blinding como used blindfolds: lectura literal incorrecta del cegamiento del ensayo; no es un problema de final abrupto.',
 49:'Cierre completo, pero afirma alivio similar al continuar pregabalina o pasar a placebo en EERW. La fuente informa respuesta mantenida del 40% frente al 20%; no confundir mejora del cierre con fidelidad.',
 53:'Además del cierre incompleto, afirma menor AHI con corticosteroides sin conservar claramente la incertidumbre que expresa la fuente.',
}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=True)
    manifest_path=STAGE/'manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    assert len(manifest['jobs'])==31
    assert all(j['repeat_penalty']==1.0 for j in manifest['jobs'])
    hashes={str(manifest_path.relative_to(ROOT)):sha(manifest_path)}
    for relative,digest in manifest['source_sha256'].items():assert sha(ROOT/relative)==digest,relative
    records=[]
    for case,job in zip(manifest['cases'],manifest['jobs']):
        assert job['case_id']==case['case_id']
        path=STAGE/'results'/(job['job_id']+'.json')
        hashes[str(path.relative_to(ROOT))]=sha(path)
        result=json.loads(path.read_text(encoding='utf-8'))
        assert result['job']==job and result['manifest_sha256']==sha(manifest_path)
        metadata=result['metadata'];text=result['prediction'];index=case['row_index']
        assert text.strip()
        old=case['historical_prediction']
        old_reason=case['historical_done_reason'];new_reason=metadata['done_reason']
        old_label=('apparent_cut_stop' if case['clear_apparent_cut_historical_zero'] else
            'apparent_cut_length' if old_reason=='length' else 'no_clear_endpoint_cut')
        new_label=('apparent_cut_length' if index==94 else
            'apparent_cut_stop' if index in NEW_CUT_NOTES else 'no_clear_endpoint_cut')
        if case['clear_apparent_cut_historical_zero']:stratum='historical_zero_shot_failure'
        elif case['selection_group']=='random_from_remaining':stratum='random_from_remaining'
        else:stratum='selected_for_few_random_failure_only'
        note=NEW_CUT_NOTES.get(index,
            'La respuesta nueva termina con una oración, conclusión o elemento de lista completo. Esto no certifica fidelidad ni cobertura total.')
        records.append(dict(row_index=index,text_id=case['text_id'],stratum=stratum,
            selection_group=case['selection_group'],historical_done_reason=old_reason,new_done_reason=new_reason,
            historical_endpoint_label=old_label,new_endpoint_label=new_label,
            historical_stop_cut=old_label=='apparent_cut_stop',new_stop_cut=new_label=='apparent_cut_stop',
            historical_limit=old_reason=='length',new_limit=new_reason=='length',
            historical_any_apparent_cut=old_label!='no_clear_endpoint_cut',
            new_any_apparent_cut=new_label!='no_clear_endpoint_cut',
            resolved_historical_zero_cut=case['clear_apparent_cut_historical_zero'] and new_label=='no_clear_endpoint_cut',
            exactly_same_text=old==text,historical_words=len(old.split()),new_words=len(text.split()),
            historical_eval_count=case['historical_eval_count'],new_eval_count=metadata['eval_count'],
            new_prompt_eval_count=metadata['prompt_eval_count'],wall_time_s=metadata['wall_time_s'],
            endpoint_review_note=note,additional_quality_observation=QUALITY_NOTES.get(index,''),
            historical_prediction=old,new_prediction=text,original=case['original'],reference=case['reference']))
    frame=pd.DataFrame(records)
    assert len(frame)==31
    assert frame.historical_stop_cut.sum()==15 and frame.new_stop_cut.sum()==7
    assert frame.historical_limit.sum()==2 and frame.new_limit.sum()==1
    assert frame.resolved_historical_zero_cut.sum()==10
    assert frame.historical_any_apparent_cut.sum()==17 and frame.new_any_apparent_cut.sum()==8
    frame.to_csv(OUT/'paired_review.csv',index=False)
    fields=['historical_stop_cut','new_stop_cut','historical_limit','new_limit',
        'historical_any_apparent_cut','new_any_apparent_cut','resolved_historical_zero_cut']
    grouped=frame.groupby('stratum').agg(n=('row_index','size'),**{c:(c,'sum') for c in fields}).reset_index()
    grouped.to_csv(OUT/'by_selection_stratum.csv',index=False)
    summary=dict(n=31,historical_stop_cuts=15,new_stop_cuts=7,
        original_zero_failures_resolved=10,original_zero_failures_persisting=5,
        historical_limit_count=2,new_limit_count=1,
        historical_any_apparent_cut=17,new_any_apparent_cut=8,
        old_complete_to_new_stop_cut_ids=['CD009919'],
        old_complete_to_new_length_cut_ids=['CD010683'],
        old_length_to_new_stop_cut_ids=['CD007074'],
        exactly_unchanged_cut_ids=frame[(frame.exactly_same_text)&frame.new_any_apparent_cut].text_id.tolist(),
        generation_minutes=float(frame.wall_time_s.sum()/60))
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    report='''# Revisión inicial zero-shot — penalización 1.0 frente a originales 1.1

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

'''+grouped.to_csv(index=False)+'''
Los 15 fallos zero-shot se analizan separadamente de seis textos seleccionados solo por fallos en few-random y de los diez sorteados del resto. En esos diez, hay nueve cierres completos y uno aparentemente cortado con stop en la nueva ejecución; los originales incluían dos cortes por límite y ocho cierres completos. No interpretar este pequeño grupo condicionado como una estimación aleatoria incondicional para Cochrane.

## Cierre completo no equivale a conservación de significado

En CD011790 (fila 49), el nuevo texto termina completo, pero afirma que los participantes EERW tuvieron alivio similar al continuar pregabalina o pasar a placebo. La fuente informa respuesta mantenida del 40% frente al 20%. En CD007104 (fila 12), used blindfolds interpreta literalmente el cegamiento del ensayo. Estas observaciones son ejemplos de errores de contenido; no se ha puntuado ni contado exhaustivamente la fidelidad de todas las salidas. No se recomienda describir todos los cierres resueltos como mejoras globales de calidad.

## Interpretación provisional

En estas entradas seleccionadas, la nueva ejecución con penalización 1.0 presenta menos finales aparentemente incompletos que las salidas históricas con 1.1. Persisten fallos y también aparecen regresiones. Es compatible con sensibilidad de algunas salidas a la configuración, pero sin una nueva condición contemporánea 1.1 no se puede atribuir causalidad exclusiva a la penalización.

No se han calculado métricas nuevas, pruebas estadísticas ni generalizaciones a otras configuraciones. La etapa few-random no forma parte de este informe y no se lee ni modifica. Las predicciones originales y los .tex se conservan intactos. paired_review.csv y reviewed_evidence.html contienen las comparaciones y decisiones de cada texto. La distinción de cortes vs límite se mantiene en todos los recuentos.
'''
    (OUT/'REPORT.md').write_text(report,encoding='utf-8')
    body=['<!doctype html><meta charset="utf-8"><title>Zero-shot: paired endpoint review</title>',
        '<style>body{font:16px sans-serif;max-width:1150px;margin:auto}pre{white-space:pre-wrap}details{padding:12px;border-top:1px solid #aaa}</style>',
        '<h1>31 paired outputs: historical 1.1 and new 1.0</h1><p>Exploratory AI-assisted review. Full endpoint closure does not establish meaning preservation. Historical comparisons do not isolate the causal effect of the penalty.</p>']
    for r in records:
        title=f"row {r['row_index']} | {r['text_id']} | {r['historical_endpoint_label']} → {r['new_endpoint_label']} | {r['stratum']}"
        body.append(f'<details><summary>{html.escape(title)}</summary><p>{html.escape(r["endpoint_review_note"])}</p><p>{html.escape(r["additional_quality_observation"])}</p><h3>Source</h3><pre>{html.escape(r["original"])}</pre><h3>Historical 1.1</h3><pre>{html.escape(r["historical_prediction"])}</pre><h3>New 1.0</h3><pre>{html.escape(r["new_prediction"])}</pre></details>')
    (OUT/'reviewed_evidence.html').write_text('\n'.join(body),encoding='utf-8')
    for relative,digest in hashes.items():assert sha(ROOT/relative)==digest,relative
    (OUT/'provenance.json').write_text(json.dumps(dict(input_sha256=hashes,
        input_files_verified_unchanged=True,reviewer='AI assistant, exploratory, unblinded',
        metrics_computed=False,few_random_results_accessed=False),indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
