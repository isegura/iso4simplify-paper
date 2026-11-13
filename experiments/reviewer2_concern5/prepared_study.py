"""Run the validated budget-aware/balanced-reference revision; dry-run by default."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PLAN=HERE/'prepared_retrieval_20261102'
OPTIONS=dict(max_new_tokens=512,num_ctx=8192,temperature=0.0,seed=42,top_k=1,top_p=1.0,
             repeat_penalty=1.1,repeat_last_n=64,num_gpu=999,require_gpu=True,timeout=900)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def validate():
    manifest=json.loads((PLAN/'experiment_manifest.json').read_text(encoding='utf-8'))
    if manifest['options']!=OPTIONS or len(manifest['jobs'])!=18 or sum(j['n'] for j in manifest['jobs'])!=2238:
        raise ValueError('Prepared study design changed')
    for name,digest in manifest['source_sha256'].items():
        if sha(ROOT/name)!=digest:raise ValueError(f'Frozen prepared input changed: {name}')
    counts=pd.read_csv(PLAN/'token_counts.csv')
    if len(counts)!=2238 or not (counts.prompt_tokens+512+64<=8192).all():
        raise ValueError('Incomplete or over-budget context certificate')
    assignment=pd.read_csv(PLAN/'tsar_reference_assignment.csv',dtype={'source_id':str})
    if len(assignment)!=20 or assignment.source_id.nunique()!=20 or assignment.reference_cefr.value_counts().to_dict()!={'b1':10,'a2':10}:
        raise ValueError('TSAR reference assignment changed')
    return manifest


def check_runtime(model,manifest):
    import requests
    from native_tokenizer_20261102 import LIBDIR
    if sha(LIBDIR/'libllama.dll')!=manifest['native_sha256']:
        raise ValueError('Tokenizer runtime changed: revalidate complete prompt counts before generating.')
    response=requests.get('http://localhost:11434/api/version',timeout=30);response.raise_for_status()
    version=response.json()
    if version.get('version')!=manifest['ollama_version']:
        raise ValueError('Ollama changed since preflight: revalidate the runtime before generating.')
    name='llama3.1:8b' if model=='llama' else 'mixtral:latest'
    response=requests.get('http://localhost:11434/api/tags',timeout=30);response.raise_for_status()
    matches=[x for x in response.json()['models'] if x.get('name')==name or x.get('model')==name]
    if len(matches)!=1 or matches[0]['digest']!=manifest['model_proofs'][model]['manifest_digest']:
        raise ValueError('Model changed; no automatic model download or substitution.')
    response=requests.post('http://localhost:11434/api/show',json={'model':name},timeout=30);response.raise_for_status()
    shown=response.json();expected=json.loads((HERE/'context_selection_20261102'/f'{model}_metadata.json').read_text())
    for field in ['template','system','parameters','details']:
        if shown.get(field)!=expected.get(field):raise ValueError(f'Model {field} changed since preflight')
    record=dict(model=name,digest=matches[0]['digest'],version=version,**{k:shown.get(k) for k in ['template','system','parameters','details']})
    path=PLAN/'runtime'/f'{model}.json';path.parent.mkdir(exist_ok=True)
    if path.exists() and json.loads(path.read_text())!=record:raise ValueError('Runtime changed within the prepared study')
    if not path.exists():path.write_text(json.dumps(record,indent=2),encoding='utf-8')


def run(model,dataset=None,execute=False,limit=None,generator=None):
    manifest=validate()
    jobs=[j for j in manifest['jobs'] if j['model']==model and (dataset is None or j['dataset']==dataset)]
    if limit is not None and (limit<1 or dataset is None):raise ValueError('Pilot requires a dataset and a positive per-configuration limit')
    print(f'{len(jobs)} configurations; '+(f'pilot up to {limit} rows each.' if limit else 'full datasets.'),flush=True)
    if not execute:
        print('DRY RUN: validated new inputs; no Ollama calls.');return
    if generator is None:
        check_runtime(model,manifest)
        sys.path.insert(0,str(ROOT))
        from model_utils import simplify_one_ollama
        generator=simplify_one_ollama
    selections=pd.read_csv(PLAN/'selected_examples.csv',keep_default_na=False,dtype={'training_text_id':str})
    index=pd.read_csv(PLAN/'prompt_index.csv',keep_default_na=False)
    token_counts=pd.read_csv(PLAN/'token_counts.csv')
    for job in jobs:
        output=ROOT/job['prediction_path'];log=PLAN/'logs'/model/(job['job_id']+'.json')
        log.parent.mkdir(parents=True,exist_ok=True)
        metadata=dict(job=job,options=OPTIONS,study_manifest_sha256=sha(PLAN/'experiment_manifest.json'),inference_sha256=sha(ROOT/'model_utils.py'),generation_schema=2)
        if log.exists():
            if json.loads(log.read_text())!=metadata:raise ValueError('Run provenance changed')
        else:
            if output.exists():raise ValueError('Prediction exists without run metadata')
            log.write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        test=pd.read_csv(ROOT/job['test_path'],keep_default_na=False,dtype={'text_id':str})
        completed=pd.read_csv(output,keep_default_na=False,dtype={'text_id':str}) if output.exists() else test.iloc[:0]
        if len(completed)>len(test) or not completed[['text_id','original','reference']].equals(test.iloc[:len(completed)][['text_id','original','reference']]):
            raise ValueError('Resume alignment failed')
        if len(completed) and completed.context_budget_observed_warning.astype(str).str.lower().isin(['true','1']).any():
            raise ValueError('Saved context discrepancy requires inspection; do not resume silently')
        progress=log.with_suffix('.progress.json')
        if len(completed):
            if not progress.exists() or json.loads(progress.read_text())!=dict(rows=len(completed),prediction_sha256=sha(output)):
                raise ValueError('Partial prediction changed or missing progress checkpoint; inspect before resuming')
        marker=log.with_suffix('.complete.json')
        if marker.exists():
            if json.loads(marker.read_text())!=dict(status='complete',rows=len(test),prediction_sha256=sha(output)) or len(completed)!=len(test):
                raise ValueError('Completed prediction changed')
            print(f'{job["job_id"]}: complete, verified, skipped.',flush=True);continue
        stop=min(len(test),limit) if limit is not None else len(test)
        for i in range(len(completed),stop):
            row=test.iloc[i]
            entry=index[(index.dataset==job['dataset'])&(index.prompt==job['prompt'])&(index.row_index==i)]
            expected=token_counts[(token_counts.model==model)&(token_counts.dataset==job['dataset'])&(token_counts.prompt==job['prompt'])&(token_counts.row_index==i)]
            chosen=selections[(selections.dataset==job['dataset'])&(selections.test_row_index==i)].sort_values('rank')
            if len(entry)!=1 or len(expected)!=1 or len(chosen)!=3:raise ValueError('Missing or ambiguous prepared input')
            path=ROOT/entry.prompt_path.iloc[0]
            if sha(path)!=entry.instructions_sha256.iloc[0]:raise ValueError('Instruction changed before request')
            predicted=int(expected.prompt_tokens.iloc[0])
            prediction,_,_,_,execution=generator(texto=row.original,instrucciones=path.read_text(encoding='utf-8'),model_name=job['ollama_model'],marker='SIMPLIFIED TEXT:',**OPTIONS)
            observed=int(execution['prompt_eval_count']);warning=observed!=predicted or observed+512+64>8192
            record=dict(row.to_dict(),prediction=prediction,**execution,model=job['ollama_model'],dataset=job['dataset'],
                prompt_type=job['prompt'],strategy='few_retrieval',generation_seed=42,repeat_penalty=1.1,repeat_last_n=64,
                retrieval_training_rows_json=json.dumps(chosen.training_row_index.tolist()),retrieval_training_ids_json=json.dumps(chosen.training_text_id.tolist()),
                retrieval_cosine_scores_json=json.dumps(chosen.cosine_similarity.tolist()),retrieval_reference_cefr_json=json.dumps(chosen.reference_cefr.tolist()),
                instructions_sha256=sha(path),preflight_prompt_tokens=predicted,context_safety_margin=64,context_budget_observed_warning=warning)
            output.parent.mkdir(parents=True,exist_ok=True)
            pd.DataFrame([record]).to_csv(output,mode='a',index=False,header=not output.exists(),encoding='utf-8')
            progress.write_text(json.dumps(dict(rows=i+1,prediction_sha256=sha(output)),indent=2),encoding='utf-8')
            print(f'{job["job_id"]}: {i+1}/{len(test)}, {execution.get("done_reason")}, input tokens {observed}/{predicted}',flush=True)
            if warning:raise RuntimeError('Prompt token discrepancy or context overflow. Output preserved; inspect before continuing.')
        if stop==len(test):
            marker.write_text(json.dumps(dict(status='complete',rows=len(test),prediction_sha256=sha(output)),indent=2),encoding='utf-8')
        else:print(f'PILOT STOP: {job["job_id"]}; no full-generation certificate. Full run resumes these rows.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['validate','run'])
    parser.add_argument('--model',choices=['llama','mixtral'])
    parser.add_argument('--dataset',choices=['cochrane','plaba','tsar2025'])
    parser.add_argument('--limit',type=int)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if args.action=='validate':validate();print('New balanced/context-limited revision validated; no inference.')
    else:
        if not args.model:parser.error('run requires --model')
        run(args.model,args.dataset,args.execute,args.limit)
