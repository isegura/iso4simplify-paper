"""Fixed exploratory few-random review and combined endpoint summaries.

No generation, metric-model calls, or manuscript edits.
"""
from pathlib import Path
import hashlib
import html
import json
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=HERE/'combined_review'
NOTES={
 17:'Persiste un corte stop: ahora llega hasta la escala zero-1, que en la fuente es zero-10. El texto anterior se cortaba antes, en un paréntesis abierto.',
 23:'Nuevo corte stop frente a la original con cierre completo: termina en between the two groups ( sin completar el inciso.',
 54:'Se repite literalmente We looked at four studies with 1154 participants, aged 50 to 9; el intervalo de la fuente es 50 a 90 años.',
 82:'El texto se extiende más que antes, pero acaba en giving 20,00 sin completar la dosis de 20,000 unidades.',
 94:'El corte stop original se sustituye por un corte al alcanzar 512 tokens: la nueva salida termina en considerable benefit or. No se considera resuelto.',
 39:'El ejemplo del revisor Four studies involving over 13,00 pasa a una respuesta con resultados y conclusión completos.',
 74:'Se completa la cantidad de 10,114 mujeres y la respuesta alcanza una conclusión.',
 100:'Se completan los 2125 participantes y la respuesta alcanza una conclusión.',
 110:'Se completan los 123 participantes y la respuesta alcanza una conclusión, pero añade esophageal cancer, diagnóstico no sustentado por el fragmento fuente proporcionado.',
 114:'La original se cortaba por límite al final de una frase; la nueva acaba con una conclusión completa.',
}
QUALITY={
 39:'Afirma No conflicts of interest were reported sin conservar la distinción de la fuente: dos estudios declararon ausencia de conflictos y los otros dos no aportaron información. Cierre completo no equivale a fidelidad total.',
 110:'Añade people with esophageal cancer, expresión ausente del texto fuente. No se determina aquí el diagnóstico verdadero mediante conocimiento externo; se marca como adición no sustentada por el fragmento.',
}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=True)
    stage=HERE/'few_random';review_dir=stage/'qualitative_review';review_dir.mkdir(exist_ok=True)
    manifest_path=stage/'manifest.json'
    m=json.loads(manifest_path.read_text(encoding='utf-8'))
    digest=sha(manifest_path)
    assert len(m['cases'])==len(m['jobs'])==31
    hashes={str(manifest_path.relative_to(ROOT)):digest}
    for path,expected in m['source_sha256'].items():assert sha(ROOT/path)==expected,path
    rows=[]
    for c,j in zip(m['cases'],m['jobs']):
        assert c['case_id']==j['case_id'] and j['repeat_penalty']==1.0
        p=stage/'results'/(j['job_id']+'.json')
        hashes[str(p.relative_to(ROOT))]=sha(p)
        r=json.loads(p.read_text(encoding='utf-8'))
        assert r['manifest_sha256']==digest and r['job']==j and r['prediction'].strip()
        index=c['row_index'];meta=r['metadata']
        old_label=('apparent_cut_stop' if c['clear_apparent_cut_historical_few_random'] else
            'apparent_cut_length' if c['historical_done_reason']=='length' else 'no_clear_endpoint_cut')
        new_label=('apparent_cut_stop' if index in [17,23,54,82] else
            'apparent_cut_length' if index==94 else 'no_clear_endpoint_cut')
        assert (meta['done_reason']=='length')==(index==94)
        stratum=('historical_few_random_failure' if c['clear_apparent_cut_historical_few_random'] else
            'random_from_remaining' if c['selection_group']=='random_from_remaining' else 'selected_for_zero_shot_failure_only')
        rows.append(dict(strategy='few_random',row_index=index,text_id=c['text_id'],stratum=stratum,
            selection_group=c['selection_group'],historical_done_reason=c['historical_done_reason'],
            new_done_reason=meta['done_reason'],historical_endpoint_label=old_label,new_endpoint_label=new_label,
            historical_stop_cut=old_label=='apparent_cut_stop',new_stop_cut=new_label=='apparent_cut_stop',
            historical_limit=c['historical_done_reason']=='length',new_limit=meta['done_reason']=='length',
            historical_any_apparent_cut=old_label!='no_clear_endpoint_cut',new_any_apparent_cut=new_label!='no_clear_endpoint_cut',
            resolved_historical_strategy_cut=c['clear_apparent_cut_historical_few_random'] and new_label=='no_clear_endpoint_cut',
            exactly_same_text=c['historical_prediction']==r['prediction'],historical_words=len(c['historical_prediction'].split()),
            new_words=len(r['prediction'].split()),new_eval_count=meta['eval_count'],wall_time_s=meta['wall_time_s'],
            endpoint_review_note=NOTES.get(index,'La nueva respuesta acaba con una oración, conclusión o elemento completo; no se certifica cobertura ni fidelidad total.'),
            additional_quality_observation=QUALITY.get(index,''),historical_prediction=c['historical_prediction'],
            new_prediction=r['prediction'],original=c['original'],reference=c['reference']))
    few=pd.DataFrame(rows)
    assert few.historical_stop_cut.sum()==8 and few.new_stop_cut.sum()==4
    assert few.historical_limit.sum()==few.new_limit.sum()==1
    assert few.resolved_historical_strategy_cut.sum()==4
    assert few.historical_any_apparent_cut.sum()==9 and few.new_any_apparent_cut.sum()==5
    few.to_csv(review_dir/'paired_review.csv',index=False)
    zero_path=HERE/'zero/qualitative_review/paired_review.csv'
    hashes[str(zero_path.relative_to(ROOT))]=sha(zero_path)
    zero=pd.read_csv(zero_path,keep_default_na=False,dtype={'text_id':str})
    zero['strategy']='zero'
    zero=zero.rename(columns={'resolved_historical_zero_cut':'resolved_historical_strategy_cut'})
    assert zero.row_index.tolist()==few.row_index.tolist()
    assert zero.text_id.tolist()==few.text_id.tolist()
    combined=pd.concat([zero,few],ignore_index=True)
    combined.to_csv(OUT/'all_62_paired_comparisons.csv',index=False)
    summary=combined.groupby('strategy',sort=False).agg(n=('row_index','size'),
        historical_stop_cuts=('historical_stop_cut','sum'),new_stop_cuts=('new_stop_cut','sum'),
        historical_limit=('historical_limit','sum'),new_limit=('new_limit','sum'),
        historical_any_cut=('historical_any_apparent_cut','sum'),new_any_cut=('new_any_apparent_cut','sum'),
        resolved_historical_strategy_cuts=('resolved_historical_strategy_cut','sum'),
        new_generation_seconds=('wall_time_s','sum')).reset_index()
    summary.to_csv(OUT/'summary_by_strategy.csv',index=False)
    strata=combined.groupby(['strategy','stratum']).agg(n=('row_index','size'),
        old_stop_cut=('historical_stop_cut','sum'),new_stop_cut=('new_stop_cut','sum'),
        old_length=('historical_limit','sum'),new_length=('new_limit','sum'),
        old_any_cut=('historical_any_apparent_cut','sum'),new_any_cut=('new_any_apparent_cut','sum')).reset_index()
    strata.to_csv(OUT/'summary_by_selection_stratum.csv',index=False)
    for destination,records,title in [(review_dir,few.to_dict('records'),'Few-random: 31 paired outputs'),
                                    (OUT,combined.to_dict('records'),'Both settings: 62 paired outputs, 31 sources')]:
        body=['<!doctype html><meta charset="utf-8"><title>'+title+'</title>',
            '<style>body{font:16px sans-serif;max-width:1100px;margin:auto}pre{white-space:pre-wrap}details{padding:12px;border-top:1px solid #aaa}</style>',
            '<h1>'+title+'</h1><p>Exploratory AI-assisted endpoint review; not independent human annotation. Historical 1.1 versus new 1.0.</p>']
        for r in records:
            heading=f"{r['strategy']} | row {r['row_index']} | {r['text_id']} | {r['historical_endpoint_label']} → {r['new_endpoint_label']}"
            body.append(f'<details><summary>{html.escape(heading)}</summary><p>{html.escape(r["endpoint_review_note"])}</p><p>{html.escape(r["additional_quality_observation"])}</p><h3>Source</h3><pre>{html.escape(r["original"])}</pre><h3>Historical 1.1</h3><pre>{html.escape(r["historical_prediction"])}</pre><h3>New 1.0</h3><pre>{html.escape(r["new_prediction"])}</pre></details>')
        (destination/'reviewed_evidence.html').write_text('\n'.join(body),encoding='utf-8')
    report='''# Diagnóstico completado: penalización 1.0, Mixtral, ISO, Cochrane

Se verificaron las 31 respuestas de cada etapa (62 en total), con los mismos 31 textos fuente. No hay respuestas vacías. Cada archivo coincide con el trabajo y hash del manifiesto; solo se generó penalización 1.0. La comparación usa las predicciones históricas de 1.1, sin nuevo control contemporáneo 1.1. Los parámetros restantes y las demostraciones few-random se conservaron. Se revisaron las salidas y sus cierres; las dudas de contenido se contrastaron con el fragmento fuente. Revisión exploratoria del asistente, sin cegamiento ni evaluadores humanos independientes.

## Recuento por estrategia

| Estrategia | Cortes stop históricos → nuevos | Límite histórico → nuevo | Finales incompletos de cualquier tipo, históricos → nuevos |
|---|---:|---:|---:|
| Zero-shot | 15 → 7 | 2 → 1 | 17 → 8 |
| Few-random | 8 → 4 | 1 → 1 | 9 → 5 |

En este subconjunto, las salidas con length se comprobaron también textualmente como incompletas. No se aplica esa equivalencia como regla universal. Las 62 comparaciones corresponden a 31 fuentes comunes, no a 62 textos independientes. No se deben usar sus sumas como tasas representativas del corpus ni realizar un test que asuma independencia entre todas las filas.

## Fallos seleccionados y casos concretos

Zero-shot: diez de los 15 cortes stop históricos ahora tienen cierre completo; cinco persisten. Dos respuestas antes completas pasan a cortes nuevos (CD009919 con stop y CD010683 por límite); CD007074 ya estaba incompleta por límite y ahora se corta con stop.

Few-random: cuatro de los ocho cortes stop históricos se resuelven (CD005122, CD003122, CD003583, CD009919); tres persisten con stop (CD011424, CD007514, CD008720) y uno cambia a corte por límite (CD010683). La salida de CD007514 es literalmente idéntica a la original. CD006250, antes completa, ahora termina en un paréntesis abierto con stop. CD005015 pasa de corte por límite a cierre completo.

El ejemplo del revisor CD005122, “Four studies involving over 13,00”, se desarrolla ahora en few-random hasta resultados y conclusión. No se afirma que este ejemplo arregle todos los demás ni el caso “from 2006 to 2”, que pertenece a PLABA y queda fuera de este diagnóstico.

## Diez entradas aleatorias, separadas

En zero-shot, esas diez entradas tenían dos cortes por límite y ocho cierres completos; ahora tienen un corte stop y nueve cierres completos. En few-random, las diez tenían cierre completo y siguen teniendo cierre completo. Se sortearon entre las 104 filas que no pertenecían a la unión de fallos revisados: no constituyen una muestra incondicional del test completo. Las restantes entradas seleccionadas solo por fallo en la otra estrategia se informan separadamente en summary_by_selection_stratum.csv.

## Calidad del contenido

El cierre completo no acredita fidelidad ni calidad global. En zero-shot CD011790 aparece una comparación EERW de pregabalina y placebo incompatible con el 40% frente al 20% de la fuente. En few-random CD009919 se añade “esophageal cancer”, diagnóstico no sustentado por el fragmento fuente proporcionado. En few-random CD005122 se pierde la distinción entre ausencia declarada de conflictos y ausencia de información. Estas son observaciones ilustrativas, no una evaluación exhaustiva ni un recuento humano de errores semánticos.

## Conclusión que permite esta prueba

Las nuevas ejecuciones con penalización desactivada presentan menos finales aparentemente incompletos que las salidas históricas en ambas estrategias de este subconjunto. Persisten fallos y aparecen regresiones. El resultado es compatible con sensibilidad a la configuración, pero no establece que la penalización sea la causa exclusiva de los fallos históricos. No generalizar a otros modelos, prompts, datasets ni selecciones de demostraciones.

No se calculan métricas automáticas ni pruebas estadísticas en este informe. Las respuestas originales, resultados de ablación y .tex permanecen sin modificar. Tampoco se ha resuelto aquí la petición independiente de marcar en Tabla 3 o analizar la celda de ISO+examples zero-shot con 29/125 salidas por límite.

## Paso siguiente

La generación diagnóstica está terminada. Con estos resultados se puede preparar la tabla descriptiva del suplemento y una respuesta acotada al revisor, junto con la cuantización y longitudes ya auditadas. No hay motivo para lanzar automáticamente más configuraciones. Si se calculan métricas sobre estas 31 entradas, comparar exclusivamente el mismo subconjunto histórico y separar los grupos seleccionados; no compararlas con promedios del test completo.
'''
    (OUT/'REPORT.md').write_text(report,encoding='utf-8')
    (review_dir/'REPORT.md').write_text('''# Few-random completado

31/31 respuestas nuevas con penalización 1.0, ninguna vacía. Ocho cortes stop históricos: cuatro se resuelven, tres persisten con stop y uno pasa a corte por límite. Aparece un nuevo corte stop en CD006250. Las diez entradas aleatorias mantienen cierre completo. Consulte ../../combined_review/REPORT.md para la revisión conjunta y los límites de interpretación.

paired_review.csv y reviewed_evidence.html contienen las decisiones, comparación histórica y fuente de los 31 casos. Revisión exploratoria del asistente; no es anotación humana independiente ni evaluación exhaustiva de fidelidad.
'''.replace('../../combined_review/','../../combined_review/'),encoding='utf-8')
    for relative,digest in hashes.items():assert sha(ROOT/relative)==digest,relative
    (OUT/'provenance.json').write_text(json.dumps(dict(input_sha256=hashes,inputs_verified_unchanged=True,
        generation_completed=True,new_penalty=1.0,rows=62,unique_source_rows=31,
        reviewer='AI assistant; exploratory; unblinded; no human interrater study',
        metrics_computed=False),indent=2),encoding='utf-8')
    print(summary.to_string(index=False))

if __name__=='__main__':main()
