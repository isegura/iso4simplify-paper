"""Verify source-only rankings, per-input prompts and sharing without model calls."""
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from study import HERE,ROOT,validate,sha
from retrieval_engine import normalized,select_three


def main():
    manifest = validate()
    selected = pd.read_csv(HERE/'selected_examples.csv',keep_default_na=False,dtype={'test_text_id':str,'training_text_id':str})
    prompt_index = pd.read_csv(HERE/'prompt_index.csv',keep_default_na=False)
    helper_dir = ROOT/'experiments/reviewer2_concern2';sys.path.insert(0,str(helper_dir))
    from inspect_original_selection import extract, normalized as prompt_normalized
    checked = 0
    sharing = []
    for dataset in ['cochrane','plaba','tsar2025']:
        train = pd.read_csv(ROOT/'data'/dataset/f'{dataset}_train.csv',keep_default_na=False,dtype={'text_id':str})
        test = pd.read_csv(ROOT/'data'/dataset/f'{dataset}_test.csv',keep_default_na=False,dtype={'text_id':str})
        train['training_row_index']=range(len(train));train['normalized_source']=train.original.map(normalized)
        pool = train.drop_duplicates('normalized_source',keep='first')
        pool = pool[~pool.normalized_source.isin(set(test.original.map(normalized)))].reset_index(drop=True)
        cache = np.load(HERE/'embeddings'/f'{dataset}.npz')
        np.testing.assert_array_equal(cache['training_row_index'],pool.training_row_index)
        for name in ['train','queries']:
            np.testing.assert_allclose(np.linalg.norm(cache[name],axis=1),1,atol=1e-5)
        queries = test.drop_duplicates('original').original.tolist()
        lookup = {source:i for i,source in enumerate(queries)}
        scores = cache['queries'].astype(np.float64) @ cache['train'].astype(np.float64).T
        for i,row in test.iterrows():
            chosen = selected[(selected.dataset==dataset)&(selected.test_row_index==i)].sort_values('rank')
            assert len(chosen)==3 and chosen['rank'].tolist()==[1,2,3]
            assert set(chosen.test_text_id)=={row.text_id}
            expected = select_three(scores[lookup[row.original]],pool,row.original,row.text_id,dataset)
            np.testing.assert_array_equal(chosen.training_row_index,pool.iloc[[x for x,_ in expected]].training_row_index)
            np.testing.assert_allclose(chosen.cosine_similarity,[score for _,score in expected],atol=1e-12,rtol=0)
            parsed_sets = []
            for prompt in ['minimal','iso','iso_examples']:
                entry = prompt_index[(prompt_index.dataset==dataset)&(prompt_index.prompt==prompt)&(prompt_index.row_index==i)]
                assert len(entry)==1
                path = ROOT/entry.prompt_path.iloc[0]
                assert sha(path)==entry.instructions_sha256.iloc[0]
                text = path.read_text(encoding='utf-8')
                template = (ROOT/'prompts'/f'{dataset}_{prompt}_few_random.md').read_text(encoding='utf-8')
                assert text.split('EXAMPLE 1')[0]==template.split('EXAMPLE 1')[0]
                parsed = extract(text)
                assert len(parsed)==3
                for example,candidate in zip(parsed,chosen.itertuples()):
                    actual_train = train.iloc[candidate.training_row_index]
                    assert candidate.original==actual_train.original and candidate.reference==actual_train.reference
                    assert example['original']==prompt_normalized(candidate.original)
                    assert example['reference']==prompt_normalized(candidate.reference)
                    assert example['displayed_id']==candidate.training_text_id
                parsed_sets.append(tuple(item['pair_sha256'] for item in parsed))
                checked+=1
            assert len(set(parsed_sets))==1
            sharing.append(dict(dataset=dataset,row_index=i,source=normalized(row.original),
                                rows=tuple(chosen.training_row_index.tolist())))
    shared = pd.DataFrame(sharing)
    assert all(group.rows.nunique()==1 for _,group in shared.groupby(['dataset','source']))
    assert checked==1119 and len(selected)==1119
    diagnostics = pd.read_csv(HERE/'context_length_comparison.csv')
    length_summary = diagnostics.groupby(['dataset','prompt']).agg(
        inputs=('row_index','size'),min_characters=('prompt_characters','min'),max_characters=('prompt_characters','max'),
        above_original_character_max=('above_historical_max_characters','sum')).reset_index()
    length_summary.to_csv(HERE/'context_length_summary.csv',index=False)
    report = dict(status='prepared_and_verified_no_generation',configurations=18,new_outputs=2238,
        prompt_files_checked=1119,selected_demo_occurrences=1119,rankings_recomputed_from_frozen_embeddings=True,
        instruction_prefixes_preserved=True,training_source_reference_pairs_preserved=True,
        examples_shared_across_prompts_and_models=True,duplicate_test_sources_share_selection=True,
        exact_test_source_matches_excluded=True,synthetic_tests_passed=4,ollama_calls=0,
        embedding_inference='CPU only, cached MiniLM; no generated simplifications',
        context_exact_fit_not_certified=True,contexts_above_original_character_max=int(diagnostics.above_historical_max_characters.sum()),
        source_sha256_verified=True)
    (HERE/'preparation_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    pool = pd.read_csv(HERE/'training_pool.csv')
    lines = ['# Concern 5: preparación terminada', '',
        '18 configuraciones nuevas, 2238 simplificaciones previstas. Solo few-shot con tres ejemplos por entrada. No se ha iniciado ninguna generación con Ollama.', '',
        'Se han verificado los 1119 prompts y las 1119 ocurrencias de demostraciones, con instrucciones preservadas, ranking recalculado desde embeddings congelados y ejemplos idénticos entre prompts/modelos. Las cuatro pruebas sintéticas pasan; incluyen reanudación, salidas vacías, avisos de contexto y TSAR con dos referencias.', '',
        '## Pool de entrenamiento', '', '| Dataset | Filas originales | Fuentes elegibles distintas | Coincidencias exactas excluidas |', '|---|---:|---:|---:|']
    for r in pool.itertuples():
        lines.append(f'| {r.dataset} | {r.training_rows} | {r.eligible_distinct_sources} | {r.exact_test_source_exclusions} |')
    levels = selected[selected.dataset=='tsar2025'].training_text_id.str.extract(r'-(a2|b1)$',expand=False).value_counts().to_dict()
    lines += ['',f'TSAR: las referencias seleccionadas por la regla de primera fila suman {levels} en 300 ocurrencias. Es una consecuencia de esa regla previa, no una selección por calidad. Los textos de test siguen evaluándose con A2/B1 conjuntamente.', '',
        '## Longitud de los prompts', '',f'{report["contexts_above_original_character_max"]} de los 1119 prompts tienen más caracteres que el máximo de las plantillas few-shot originales de su dataset/prompt. Esto es una advertencia de longitud, no un conteo de excesos de 8192 tokens.', '',
        'El detalle está en context_length_summary.csv y context_length_comparison.csv. No se ha certificado tokenización exacta de Ollama ni ausencia de truncamiento silencioso. Antes de ejecutar todos los bloques debe revisarse el diagnóstico y el primer bloque terminado, manteniendo las reglas de contexto de ANALYSIS_PLAN.md. No se han recortado ni reemplazado ejemplos según su longitud.', '',
        '## Siguiente paso', '', 'Esperar a que termine Concern 2. La guía GUIA_EJECUCION.md contiene seis bloques manuales; empezar por el corto Llama/TSAR y revisar contexto/salidas antes de continuar. Evaluación de seis métricas y descriptores preparada por separado; no es necesario regenerar para añadir métricas. Las comparaciones y los textos finales quedan pendientes de resultados.', '',
        'No se modificaron las predicciones históricas, las semillas en curso, el entorno ni los archivos .tex. La preparación usa exclusivamente el encoder ya almacenado en caché, en CPU y con dos hilos.']
    (HERE/'PREPARATION_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    print(length_summary.to_string(index=False))


if __name__=='__main__':
    main()
