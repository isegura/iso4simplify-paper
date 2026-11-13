"""Materialize fixed assistant review decisions for one frozen candidate file.

This is an annotation export, NOT a general automatic classifier. It refuses
different input content. Labels concern apparent endpoint completeness only.
"""
from pathlib import Path
import hashlib
import html
import json
import re
import pandas as pd

HERE=Path(__file__).resolve().parent
INPUT=HERE.parent/'candidate_entries.csv'
EXPECTED_SHA='7ee4a03343fab9fd351ee62e921713f860938437738976e4899c0bd997e55e51'

# Fixed decisions after inspecting all 446 full outputs, their endings, and
# consulting source texts for ambiguous numeric/technical expressions.
# Unlisted candidates have an apparently clear incomplete ending.
COMPLETE={
 'C107':'El cuerpo termina con una conclusión completa. El bloque Python vacío es una anomalía de formato, no una frase cortada.',
 'C124':'La nota entre paréntesis se cierra y el cuerpo tiene conclusión; no se observa corte del final.',
 'C135':'La última viñeta es completa; la falta de punto final no implica interrupción.',
 'C202':'La respuesta y la nota final están cerradas; el detector se activa por el paréntesis final.',
 'C221':'El último punto de recomendaciones es una unidad completa, sin punto terminal.',
 'C226':'La enumeración final de temas está completa; no queda una frase abierta.',
 'C276':'La conclusión y la nota final están completas.',
 'C279':'La lista y la nota de definiciones están cerradas.',
 'C281':'La lista contiene factores internos/externos y condiciones climáticas; acaba en una viñeta completa. No se juzga aquí cobertura de la fuente.',
 'C284':'El cierre declara que se han omitido detalles; la nota es completa. Omitir información no basta para inferir corte.',
 'C285':'Termina con dos dosis completas en una lista de participantes. Falta cobertura de resultados, pero el final no presenta un corte inequívoco.',
 'C288':'La última viñeta, 5-HT receptors, es una unidad nominal completa.',
 'C289':'El texto acaba con una oración completa y cierre de comillas triples.',
 'C301':'La última viñeta define los marcadores inflamatorios con una cláusula completa.',
 'C335':'La conclusión y la nota explicativa final están cerradas.',
 'C346':'La última viñeta concluye la comparación de trisomías; no tiene punto, pero es completa.',
 'C360':'El cuerpo y la nota final son completos.',
 'C387':'La respuesta y la nota final están cerradas.',
 'C392':'La conclusión y la nota final son completas.',
 'C394':'El cuerpo y la nota final están cerrados.',
 'C401':'La oración final está completa; Confidence: 90% es metatexto añadido, no corte numérico.',
 'C405':'El párrafo termina completo y la lista añadida de instrucciones tiene viñetas completas.',
 'C408':'El cuerpo está completo; el paréntesis final indica un supuesto número de caracteres.',
 'C411':'El párrafo está completo; la atribución final entre paréntesis es metatexto, no un corte.',
 'C412':'El cuerpo termina completo; el paréntesis final indica un supuesto número de palabras.',
 'C414':'El cuerpo termina completo; el paréntesis final indica un supuesto número de palabras.',
 'C415':'El párrafo termina completo; Original text by ChatGPT es una atribución añadida.',
 'C419':'El párrafo está completo y termina con una URL de atribución.',
 'C420':'El cuerpo termina completo; el paréntesis final indica un supuesto número de palabras.',
 'C422':'La nota explicativa final está cerrada y el cuerpo no queda interrumpido.',
 'C426':'La nota final se cierra después de una explicación completa.',
 'C437':'La respuesta y la nota explicativa final están cerradas.',
 'C439':'El cuerpo termina completo; el paréntesis final indica un supuesto número de caracteres.',
 'C444':'El cuerpo y la nota final están completos.',
}
DOUBTFUL={
 'C057':'Solo dice que se revisaron 28 estudios con 9330 participantes y acaba en punto y coma. Hay muy poca cobertura y un cierre anómalo, pero la proposición es completa; no permite distinguir omisión de un corte.',
 'C234':'Solo devuelve un título completo sobre hCG y embarazo ectópico. La tarea queda insuficientemente atendida, pero el título no contiene una frase cortada; no permite diagnosticar interrupción.',
}
ADDITIONAL_CLEAR={
 'C001':'Termina en un paréntesis abierto tras airways; no llega a aportar el contenido del inciso.',
 'C002':'Termina en un paréntesis abierto tras one year.',
 'C005':'El resultado principal termina en pain response seguido de paréntesis abierto.',
 'C007':'El resultado termina en months seguido de un paréntesis abierto.',
 'C016':'El efecto de antibióticos termina en 8% seguido de paréntesis abierto.',
 'C020':'El rango de edad acaba en five and, sin segundo extremo.',
 'C021':'La comparación de complicaciones acaba en un paréntesis abierto.',
 'C030':'La frase de supervivencia acaba con un paréntesis abierto.',
 'C044':'La frase de efectos protectores acaba en un paréntesis abierto.',
 'C046':'La frase de supervivencia acaba en un paréntesis abierto.',
 'C049':'La frase sobre mortalidad termina en death seguido de paréntesis abierto.',
 'C052':'La primera viñeta de resultados acaba en Delivery method seguido de paréntesis abierto.',
 'C056':'La comparación a favor de clavos acaba en un paréntesis abierto.',
 'C062':'Anuncia tres temas y termina en dos puntos sin enumerarlos.',
 'C063':'Termina en P value = sin dar el valor.',
 'C071':'Termina en accuracy data for, dejando el complemento sin completar.',
 'C077':'La comparación estadística termina en un paréntesis abierto.',
 'C083':'El intervalo de confianza acaba en 3.3 - sin extremo superior.',
 'C088':'La frase sobre embarazo termina en un paréntesis abierto.',
 'C095':'El intervalo de especificidad acaba en from 48% to, sin extremo superior.',
 'C099':'La frase sobre calidad de evidencia acaba en un paréntesis abierto.',
 'C115':'El rango de edad acaba en from 41 to, sin segundo extremo.',
 'C119':'Anuncia resultados de supervivencia con dos puntos sin desarrollarlos.',
 'C121':'Anuncia lo que encontraron los estudios con found: y no lo desarrolla.',
 'C134':'Enumera dos de cuatro intervenciones anunciadas y termina en coma.',
 'C147':'El inciso estadístico queda abierto tras 149 participants:.',
 'C148':'Termina en survival after, dejando la frase incompleta.',
 'C156':'Termina en P < sin valor ni cierre del inciso.',
 'C168':'Acaba en actin-related protein sin identificar Arp4 ni continuar la explicación presente en la fuente.',
 'C169':'La lista de histonas se corta en H, frente a H3/H4 en la fuente.',
 'C174':'Termina en p < sin valor ni cierre del inciso.',
 'C175':'Termina en Zn( sin completar el término químico.',
 'C176':'Termina en Zn( sin completar el término químico.',
 'C182':'El nombre mechanistic target of rapamycin complex queda sin el 1 de la fuente y sin continuación.',
 'C189':'Se corta el nombre del dímero en H4-H, frente a H4-H3 en la fuente.',
 'C192':'Se corta el identificador del segundo ensayo en TULIP-.',
 'C207':'Anuncia ocho modificaciones pero enumera dos y termina en coma.',
 'C208':'Termina en HMG1/ sin completar el nombre HMG1/2.',
 'C211':'Termina en P < sin valor ni cierre del inciso.',
 'C212':'Termina en P < sin valor ni cierre del inciso; fila distinta con el mismo ID que C211.',
 'C242':'Termina con un paréntesis abierto al iniciar el siguiente elemento de una enumeración.',
 'C245':'La construcción looked at how ... coronavirus queda sin predicado; además falta completar el nombre del virus.',
 'C249':'Acaba en actin-related protein sin identificar Arp4 ni continuar la explicación presente en la fuente.',
 'C254':'Termina en two phase, sin completar la descripción de ensayos de fase 3.',
 'C260':'La enumeración de variantes de histonas se corta en H.',
 'C269':'El identificador del dímero acaba en H4-H, sin completar H4-H3.',
 'C282':'Anuncia factores con made worse by: pero no los enumera.',
 'C290':'La última viñeta termina en actin-related protein sin identificar Arp4 ni continuar.',
 'C297':'Se corta el identificador PC12 en PC1.',
 'C307':'Termina en actin-related protein sin identificar Arp4 ni continuar la explicación.',
 'C309':'La construcción The activity of caspase queda sin predicado y sin completar caspase 3/7.',
 'C332':'El identificador anti-CD20 queda cortado en anti-CD2.',
 'C337':'Termina en Zn( sin completar el término químico.',
 'C341':'La enumeración de citoquinas queda cortada en IL-.',
 'C344':'La fecha queda sin valor después de increased ... to 8.8% in.',
 'C350':'Anuncia resultados comparativos con dos puntos y no los desarrolla.',
 'C370':'La comparación de porcentajes queda en from 3 percent to sin segundo valor.',
}

def main():
    assert hashlib.sha256(INPUT.read_bytes()).hexdigest()==EXPECTED_SHA
    frame=pd.read_csv(INPUT,keep_default_na=False,dtype={'text_id':str})
    assert len(frame)==446
    frame.insert(0,'review_id',[f'C{i+1:03}' for i in range(len(frame))])
    assert len(COMPLETE)==34 and len(DOUBTFUL)==2 and len(ADDITIONAL_CLEAR)==57
    assert not (set(COMPLETE)&set(DOUBTFUL))
    records=[]
    for row in frame.to_dict('records'):
        key=row['review_id']
        label='clear_apparent_cut'
        note=ADDITIONAL_CLEAR.get(key)
        if key in COMPLETE:
            label='no_clear_cut'; note=COMPLETE[key]
        elif key in DOUBTFUL:
            label='uncertain'; note=DOUBTFUL[key]
        elif note is None:
            assert row['existing_detector_candidate'],key
            end=' '.join(row['prediction'].split())[-140:]
            note=f'La salida termina en «{end}». El cierre deja una cantidad, fecha, intervalo, término técnico o construcción sintáctica aparentemente sin completar; no se basa solo en la falta de punto.'
        # Context checks that distinguish genuine terms from apparent prefixes.
        if key=='C138': note='El cierre interleukin-1 corresponde a interleukin-10 en la fuente: el término queda aparentemente cortado, no es solo ausencia de punto.'
        if key in ['C191','C253']: note='La fuente habla de interleukin-17; el cierre interleukin-1 deja aparentemente incompleto el identificador.'
        if key in ['C230','C334']: note='La fuente habla de T helper 17. El cierre T helper 1 no completa ese identificador; además la frase queda sintácticamente abierta.'
        if row['dataset']=='cochrane' and row['row_index']==109:
            note='El efecto termina en day 2; la fuente especifica day 28. Es un aparente corte del número, no solo una oración sin punto.'
        if row['dataset']=='cochrane' and row['row_index']==17 and row['prediction'].endswith('zero-1'):
            note='La escala zero-10 de la fuente queda aparentemente cortada en zero-1.'
        records.append(dict(row,review_label=label,review_note=note,
            reviewer='AI assistant; exploratory single review, not independent human annotation',
            causal_explanation_assigned=False))
    reviewed=pd.DataFrame(records)
    reviewed.to_csv(HERE/'reviewed_candidates.csv',index=False)
    reviewed[reviewed.review_label=='clear_apparent_cut'].to_csv(HERE/'clear_apparent_cuts.csv',index=False)
    (HERE/'decisions.json').write_text(json.dumps([dict(review_id=r['review_id'],label=r['review_label'],note=r['review_note'])
        for r in records],ensure_ascii=False,indent=2),encoding='utf-8')
    grouped=reviewed.groupby(['dataset','prompt','strategy','review_label']).size().unstack(fill_value=0).reset_index()
    grouped.to_csv(HERE/'by_configuration.csv',index=False)
    datasets=[]
    for dataset,group in reviewed.groupby('dataset'):
        clear=group[group.review_label=='clear_apparent_cut']
        datasets.append(dict(dataset=dataset,candidates_reviewed=len(group),clear_apparent_cuts=len(clear),
            no_clear_cut=int((group.review_label=='no_clear_cut').sum()),
            uncertain=int((group.review_label=='uncertain').sum()),
            affected_test_rows=clear.row_index.nunique(),affected_unique_ids=clear.text_id.nunique()))
    summary=pd.DataFrame(datasets)
    summary.to_csv(HERE/'by_dataset.csv',index=False)
    all_rows=pd.read_csv(HERE.parent/'all_outputs_screening.csv',dtype={'text_id':str})
    denominator=all_rows.groupby(['dataset','prompt','strategy']).size().rename('total_original_outputs')
    grouped.merge(denominator.reset_index(),on=['dataset','prompt','strategy'],validate='one_to_one').to_csv(HERE/'by_configuration_with_denominators.csv',index=False)
    # Reviewable full evidence with source/output and explicit decisions.
    body=['<!doctype html><meta charset="utf-8"><title>Mixtral: reviewed candidate endings</title>',
        '<style>body{font:16px sans-serif;max-width:1100px;margin:auto}pre{white-space:pre-wrap}details{border-top:1px solid #aaa;padding:12px}</style>',
        '<h1>AI-assisted exploratory review — 446 candidates</h1><p>Clear apparent cuts are observations about text endings, not verified runtime causes. Completeness of meaning and overall quality are separate questions.</p>']
    for r in records:
        title=f"{r['review_id']} | {r['dataset']} | {r['prompt']} | {r['strategy']} | row {r['row_index']} | ID {r['text_id']} | {r['review_label']}"
        body.append(f'<details><summary>{html.escape(title)}</summary><p>{html.escape(r["review_note"])}</p><h3>Source</h3><pre>{html.escape(r["original"])}</pre><h3>Output</h3><pre>{html.escape(r["prediction"])}</pre></details>')
    (HERE/'reviewed_evidence.html').write_text('\n'.join(body),encoding='utf-8')
    methods=dict(input_sha256=EXPECTED_SHA,candidates=446,scope='Only screened stop outputs from original Mixtral runs; not ablations',
        annotation='AI-assisted exploratory single review; not a human study; not blinded; no interrater agreement',
        procedure='All candidate outputs inspected; full sources consulted for ambiguous numeric and technical expressions. This is a fixed review export, not a newly validated detector.',
        labels=dict(clear_apparent_cut='Unfinished syntax, enumeration, numerical expression or technical identifier apparent from output/context',
            uncertain='Insufficient coverage or anomalous closure without unambiguous cutoff',
            no_clear_cut='No clear abrupt endpoint; may contain other quality/format/coverage problems'),
        limitations=['Not all 4476 outputs were qualitatively reviewed; false negatives outside the screening remain possible.',
            '107 length outputs and two empty outputs are outside this candidate review.',
            'Apparent cuts do not establish that repeat penalty caused them.',
            'Source rows, repeated PLABA IDs and repeated configurations are not independent observations.',
            'Numbers here are provisional assistant annotations, not a validated human failure rate.'])
    (HERE/'methodology.json').write_text(json.dumps(methods,indent=2,ensure_ascii=False),encoding='utf-8')
    report='''# Revisión cualitativa de finales — Mixtral

Se revisaron las 446 salidas candidatas: las 354 del detector existente y las 92 del cribado amplio. Es una revisión exploratoria realizada por el asistente, sin evaluadores humanos independientes ni cegamiento. Se inspeccionaron las salidas completas y se consultaron fuentes completas para resolver dudas sobre cifras y términos técnicos. No se afirma haber evaluado fidelidad o cobertura completa de todas las salidas.

## Decisiones

'''+summary.to_csv(index=False)+'''
clear_apparent_cut significa final aparentemente cortado, no mecanismo de terminación demostrado. no_clear_cut significa que no hay corte claro del cierre, no que la simplificación sea buena o conserve todo el significado. uncertain conserva los casos ambiguos en lugar de forzar una decisión.

En total: 410 finales aparentemente cortados, 34 sin corte claro y dos dudosos. De los 354 candidatos iniciales, 353 se consideran cortes aparentes y uno es dudoso. De los 92 adicionales, 57 se consideran cortes aparentes, 34 no presentan corte claro y uno es dudoso.

Los dos dudosos son C057 (una sola oración con número de estudios/participantes, terminada en punto y coma) y C234 (solo un título). La falta de cobertura de la fuente no basta para afirmar un corte de generación. Las listas y notas completas sin punto son falsos positivos del cribado de puntuación.

## Alcance

Las 36 configuraciones contienen cortes aparentes. by_configuration_with_denominators.csv incluye las decisiones y los denominadores originales. Los recuentos por texto se basan en la posición de fila del test; PLABA contiene IDs repetidos, también desglosados. No se mezclan las 107 salidas con done_reason=length ni las dos vacías.

La revisión solo cubre candidatos: no certifica ausencia de fallos en las demás respuestas. No es una evaluación humana validada ni permite estimar sensibilidad/especificidad. Los resultados no identifican la causa del corte: repeat penalty, condiciones de parada y otros mecanismos siguen por comprobar.

## Siguiente decisión experimental

No se ha cambiado ni ejecutado el comando de generación. Dado que los cortes aparecen en todos los prompts y estrategias, es razonable seleccionar después un diagnóstico pequeño que cubra esos grupos y conserve los ejemplos exactos del revisor, manteniendo separados los fallos seleccionados deliberadamente y los controles aleatorios. Los archivos de generación todavía contienen el diseño anterior de 496 respuestas; no constituyen una selección nueva basada en esta revisión.

Las decisiones individuales, su motivo y la evidencia completa se encuentran en reviewed_candidates.csv, decisions.json y reviewed_evidence.html. Las predicciones originales, los informes previos y los archivos LaTeX permanecen sin modificar.
'''
    (HERE/'REPORT.md').write_text(report,encoding='utf-8')
    assert reviewed.review_label.value_counts().to_dict()=={'clear_apparent_cut':410,'no_clear_cut':34,'uncertain':2}
    assert hashlib.sha256(INPUT.read_bytes()).hexdigest()==EXPECTED_SHA
    print(summary.to_string(index=False))
    print(reviewed.review_label.value_counts().to_string())

if __name__=='__main__': main()
