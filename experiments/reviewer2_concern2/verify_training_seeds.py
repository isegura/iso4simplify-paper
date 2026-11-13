"""Copy author-supplied training CSVs and replay original demonstration sampling.

No prompt rewriting or model inference. Seeds 42--46 are inspected for input
overlap only, never using generated-output quality to choose seeds.
"""
from pathlib import Path
import hashlib
import itertools
import json
import shutil
import pandas as pd
import numpy as np
from inspect_original_selection import extract, normalized

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DATASETS=['cochrane','plaba','tsar2025']
SEEDS=[42,43,44,45,46]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    provenance={};checks=[];samples=[];overlaps=[];partitions=[]
    for dataset in DATASETS:
        provided=Path('C:/Users/isegu/Downloads')/f'{dataset}_train.csv'
        target=ROOT/'data'/dataset/provided.name
        if target.exists():assert sha(target)==sha(provided),'Existing training file differs; refusing overwrite'
        else:shutil.copy2(provided,target)
        assert sha(target)==sha(provided)
        provenance[dataset]=dict(supplied_file=str(provided),project_file=str(target.relative_to(ROOT)),sha256=sha(target))
        train=pd.read_csv(target,keep_default_na=False,dtype={'text_id':str})
        assert {'text_id','original','reference'}<=set(train)
        test=pd.read_csv(ROOT/'data'/dataset/f'{dataset}_test.csv',keep_default_na=False,dtype={'text_id':str})
        test_sources={normalized(x) for x in test.original.astype(str)}
        partitions.append(dict(dataset=dataset,training_rows=len(train),test_rows=len(test),
            training_rows_with_normalized_exact_source_in_test=sum(normalized(x) in test_sources for x in train.original.astype(str)),
            shared_text_ids=len(set(train.text_id)&set(test.text_id))))
        selected={seed:train.sample(n=3,random_state=seed) for seed in SEEDS}
        for seed,selection in selected.items():
            for position,(index,row) in enumerate(selection.iterrows(),1):
                original=normalized(row.original);reference=normalized(row.reference)
                samples.append(dict(dataset=dataset,seed=seed,position=position,training_row_index=int(index),
                    text_id=row.text_id,original=original,reference=reference,
                    source_sha256=hashlib.sha256(original.encode()).hexdigest(),
                    pair_sha256=hashlib.sha256((original+'\n'+reference).encode()).hexdigest(),
                    normalized_exact_source_overlap_with_test=original in test_sources))
        for prompt in ['minimal','iso','iso_examples']:
            for strategy in ['one','few_random']:
                path=ROOT/'prompts'/f'{dataset}_{prompt}_{strategy}.md'
                before=sha(path)
                examples=extract(path.read_text(encoding='utf-8'))
                for e,(_,row) in zip(examples,selected[42].iterrows()):
                    checks.append(dict(dataset=dataset,prompt=prompt,strategy=strategy,position=e['position'],
                        prompt_displayed_id=e['displayed_id'],training_actual_id=row.text_id,
                        source_matches=e['original']==normalized(row.original),
                        reference_matches=e['reference']==normalized(row.reference),
                        displayed_id_matches=e['displayed_id']==row.text_id))
                assert sha(path)==before
        for first,second in itertools.combinations(SEEDS,2):
            a,b=selected[first],selected[second]
            source_a={normalized(x) for x in a.original};source_b={normalized(x) for x in b.original}
            pairs_a={(normalized(r.original),normalized(r.reference)) for r in a.itertuples()}
            pairs_b={(normalized(r.original),normalized(r.reference)) for r in b.itertuples()}
            overlaps.append(dict(dataset=dataset,seed_a=first,seed_b=second,
                shared_training_rows=len(set(a.index)&set(b.index)),shared_source_texts=len(source_a&source_b),
                shared_demonstration_pairs=len(pairs_a&pairs_b),
                one_shot_pair_identical=(normalized(a.iloc[0].original),normalized(a.iloc[0].reference))==
                    (normalized(b.iloc[0].original),normalized(b.iloc[0].reference))))
    check=pd.DataFrame(checks);sample=pd.DataFrame(samples)
    assert len(check)==36 and check.source_matches.all() and check.reference_matches.all()
    assert not sample.normalized_exact_source_overlap_with_test.any()
    check.to_csv(HERE/'seed42_prompt_comparison.csv',index=False)
    sample.to_csv(HERE/'candidate_seed_demonstrations.csv',index=False)
    pd.DataFrame(overlaps).to_csv(HERE/'candidate_seed_overlaps.csv',index=False)
    pd.DataFrame(partitions).to_csv(HERE/'training_test_overlap.csv',index=False)
    info=dict(training_files=provenance,pandas_version=pd.__version__,numpy_version=np.__version__,
        algorithm='DataFrame.sample(n=3, random_state=seed), without replacement; retain returned order',
        inspected_seeds=SEEDS,selection_replay_seed=42,
        all_36_prompt_occurrences_match_content_and_order=True,
        original_prompt_files_modified=False,models_run=False,
        new_experimental_seeds_finalized=False,
        note='Inspected additional seed inputs before outcome generation. 43 repeats TSAR one-shot from 42; 45 repeats TSAR one-shot from 44. 44 and 46 are an available alternative if distinct one-shot inputs are required.')
    (HERE/'training_seed_verification.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    (HERE/'SEED42_VERIFICATION.md').write_text('''# Comprobación de los training y semilla 42

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
''',encoding='utf-8')
    print(check.groupby('dataset')[['source_matches','reference_matches','displayed_id_matches']].sum().to_string())
    print(pd.DataFrame(partitions).to_string(index=False))

if __name__=='__main__':main()
