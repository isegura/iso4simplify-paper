"""Shared Cochrane subset; generate only repeat_penalty=1.0.

Historical predictions with 1.1 are retained as comparison. This script does
not schedule or execute any new 1.1 generation.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import random
from pathlib import Path
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SEED=20261022
STRATEGIES=['zero','few_random']

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def prepare():
    if (HERE/'selection.json').exists(): raise FileExistsError('Selection already frozen')
    review_path=ROOT/'experiments/reviewer2_concern4/abrupt_endings/qualitative_review/reviewed_candidates.csv'
    source_path=ROOT/'data/cochrane/cochrane_test.csv'
    review=pd.read_csv(review_path,keep_default_na=False)
    source=pd.read_csv(source_path,keep_default_na=False,dtype={'text_id':str})
    assert len(source)==125
    fail={}
    for strategy in STRATEGIES:
        subset=review[(review.dataset=='cochrane') & (review.prompt=='ISO') &
            (review.strategy==strategy) & (review.review_label=='clear_apparent_cut')]
        fail[strategy]=sorted(subset.row_index.astype(int).tolist())
    shared=sorted(set(fail['zero']) & set(fail['few_random']))
    union=sorted(set(fail['zero']) | set(fail['few_random']))
    assert len(fail['zero'])==15 and len(fail['few_random'])==8 and shared==[17,82] and len(union)==21
    pool=[i for i in range(len(source)) if i not in union]
    random_rows=sorted(random.Random(SEED).sample(pool,10))
    selected=sorted(union+random_rows)
    assert len(selected)==31
    selection=dict(model='mixtral:latest',dataset='cochrane',prompt='iso',strategies=STRATEGIES,
        sampling_seed=SEED,failure_rows_by_strategy=fail,common_failure_rows=shared,
        union_failure_rows=union,random_pool_n=len(pool),random_rows=random_rows,
        selected_rows=selected,n_texts=31,new_repeat_penalty=1.0,historical_repeat_penalty=1.1,
        new_generations_per_strategy=31,total_new_generations=62)
    tree=ast.parse((ROOT/'model_utils.py').read_text(encoding='utf-8-sig'))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='simplify_one_ollama')
    expr=next(n.value for n in fn.body if isinstance(n,ast.Assign) and
        any(isinstance(t,ast.Name) and t.id=='prompt' for t in n.targets))
    code=compile(ast.Expression(expr),'<shared inference prompt>','eval')
    source_hashes={str(p.relative_to(ROOT)):sha(p) for p in
        [review_path,source_path,ROOT/'model_utils.py',HERE.parent/'study.py',Path(__file__)]}
    selection_rows=[]
    for i in selected:
        selection_rows.append(dict(row_index=i,text_id=source.iloc[i].text_id,
            selection_group='documented_failure_in_either_strategy' if i in union else 'random_from_remaining',
            clear_apparent_cut_historical_zero=i in fail['zero'],
            clear_apparent_cut_historical_few_random=i in fail['few_random']))
    pd.DataFrame(selection_rows).to_csv(HERE/'selected_texts.csv',index=False)
    # Both manifests are built from the same selected source rows, in identical order.
    for strategy in STRATEGIES:
        folder=HERE/strategy;folder.mkdir(exist_ok=True)
        assert not (folder/'manifest.json').exists()
        pred_path=ROOT/'outputs/mixtral_512'/f'predictions_mixtral_latest_cochrane_iso_{strategy}.csv'
        prompt_path=ROOT/'prompts'/('iso_zero.md' if strategy=='zero' else 'cochrane_iso_few_random.md')
        frame=pd.read_csv(pred_path,keep_default_na=False,dtype={'text_id':str})
        assert frame[['text_id','original','reference']].equals(source[['text_id','original','reference']])
        instructions=prompt_path.read_text(encoding='utf-8')
        hashes=dict(source_hashes)
        for path in [pred_path,prompt_path]: hashes[str(path.relative_to(ROOT))]=sha(path)
        cases=[];jobs=[]
        for i,selection_row in zip(selected,selection_rows):
            row=frame.iloc[i]
            if strategy=='few_random' and i==39:
                assert row.prediction.strip()=='Four studies involving over 13,00'
            message=eval(code,{'__builtins__':{}},{'instrucciones':instructions,'texto':row.original})
            case_id=f'cochrane_{i}_iso_{strategy}'
            cases.append(dict(selection_row,case_id=case_id,dataset='cochrane',prompt='iso',strategy=strategy,
                original=row.original,reference=row.reference,instructions=instructions,prompt_file=prompt_path.name,
                historical_prediction=row.prediction,historical_done_reason=row.done_reason,
                historical_eval_count=int(row.eval_count),historical_repeat_penalty=1.1,
                full_user_message=message,full_user_message_sha256=hashlib.sha256(message.encode()).hexdigest()))
            jobs.append(dict(case_id=case_id,repeat_penalty=1.0,job_id=case_id+'_rp1_0'))
        manifest=dict(design_version='cochrane_iso_shared_subset_rp1_0_v1',model='mixtral:latest',
            strategy=strategy,sampling_seed=SEED,selection=selection,
            options=dict(num_predict=512,num_ctx=8192,temperature=0.0,seed=42,top_k=1,top_p=1.0,
                repeat_last_n=64,num_gpu=999),source_sha256=hashes,cases=cases,jobs=jobs)
        (folder/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
        pd.DataFrame([{k:v for k,v in c.items() if k not in ['instructions','full_user_message','original','reference']}
            for c in cases]).to_csv(folder/'selected_cases.csv',index=False)
    (HERE/'selection.json').write_text(json.dumps(selection,indent=2),encoding='utf-8')
    validate()
    print(json.dumps(selection,indent=2))

def validate():
    manifests={s:json.loads((HERE/s/'manifest.json').read_text(encoding='utf-8')) for s in STRATEGIES}
    for s,m in manifests.items():
        assert len(m['cases'])==len(m['jobs'])==31
        assert len({j['job_id'] for j in m['jobs']})==31
        assert all(j['repeat_penalty']==1.0 for j in m['jobs'])
        for c in m['cases']:
            assert c['prompt']=='iso' and c['strategy']==s and c['dataset']=='cochrane'
            assert hashlib.sha256(c['full_user_message'].encode()).hexdigest()==c['full_user_message_sha256']
        for relative,digest in m['source_sha256'].items(): assert sha(ROOT/relative)==digest,relative
    for a,b in zip(manifests['zero']['cases'],manifests['few_random']['cases']):
        assert all(a[k]==b[k] for k in ['row_index','text_id','original','reference','selection_group'])
    return manifests

def run(strategy):
    validate()
    spec=importlib.util.spec_from_file_location('repeat_penalty_shared_runner',HERE.parent/'study.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    assert runner.ROOT==ROOT
    runner.HERE=HERE/strategy
    runner.run()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','validate','run'])
    parser.add_argument('--strategy',choices=STRATEGIES,default='zero')
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='validate':validate();print('31 shared texts; 62 jobs; all repeat_penalty=1.0. No inference executed.')
    else:run(args.strategy)
