"""Prepare/validate the demonstration-selection study; run only with --execute."""
import argparse
import csv
import difflib
import hashlib
import json
import re
import sys
import time
from pathlib import Path
import pandas as pd
from inspect_original_selection import extract, normalized

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DATASETS={'cochrane':125,'plaba':148,'tsar2025':100}
PROMPTS=['minimal','iso','iso_examples']
STRATEGIES=['one','few_random']
SEEDS=[44,46]
MODELS={'llama':('llama3.1:8b','llama3_1_8b'),'mixtral':('mixtral:latest','mixtral_latest')}
OPTIONS=dict(max_new_tokens=512,num_ctx=8192,temperature=0.0,seed=42,
    top_k=1,top_p=1.0,repeat_penalty=1.1,repeat_last_n=64,num_gpu=999,require_gpu=True,timeout=900)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def relative(path):return path.relative_to(ROOT).as_posix()

def generation_record(job,row,prediction,metadata):
    """Save raw output and execution metadata; derive indicators afterwards."""
    return dict(row.to_dict(),prediction=prediction,**metadata,
        model=job['ollama_model'],dataset=job['dataset'],prompt_type=job['prompt'],
        strategy=job['strategy'],selection_seed=job['selection_seed'],generation_seed=42,
        repeat_penalty=1.1,repeat_last_n=64)

def slot(original,value):
    if '"""' in original:
        start=original.index('"""')+3;end=original.rindex('"""')
        assert end>=start
        return original[:start]+slot(original[start:end],value)+original[end:]
    match=re.fullmatch(r'(\s*)(.*?)(\s*)',original,re.S)
    assert match
    return match[1]+str(value).strip()+match[3]

def substitute(template,selection):
    matches=list(re.finditer(r'^EXAMPLE\s+(\d+)\s*\(([^)]+)\)\s*$',template,re.M))
    assert len(matches)==len(selection)
    result=template[:matches[0].start()]
    for i,(match,(_,row)) in enumerate(zip(matches,selection.iterrows())):
        block=template[match.start():matches[i+1].start() if i+1<len(matches) else len(template)]
        head,remainder=block.split('ORIGINAL:',1)
        original,reference=remainder.split('SIMPLIFIED TEXT:',1)
        head=re.sub(r'^(EXAMPLE\s+\d+\s*\()[^)]+(\))',lambda m:m[1]+str(row.text_id)+m[2],head,count=1)
        result+=head+'ORIGINAL:'+slot(original,row.original)+'SIMPLIFIED TEXT:'+slot(reference,row.reference)
    assert result[:matches[0].start()]==template[:matches[0].start()]
    return result

def prepare():
    if (HERE/'experiment_manifest.json').exists():raise FileExistsError('Frozen plan exists; refusing overwrite')
    hashes={relative(ROOT/'model_utils.py'):sha(ROOT/'model_utils.py'),relative(Path(__file__)):sha(Path(__file__))}
    hashes[relative(HERE/'inspect_original_selection.py')]=sha(HERE/'inspect_original_selection.py')
    for path in [ROOT/'generate_systematic_error_analysis_512.py',ROOT/'data/tsar2025/tsar2025_test_200.csv']:
        hashes[relative(path)]=sha(path)
    selections=[];jobs=[];diffs=[]
    for dataset,n in DATASETS.items():
        train_path=ROOT/'data'/dataset/f'{dataset}_train.csv';test_path=train_path.with_name(f'{dataset}_test.csv')
        train=pd.read_csv(train_path,keep_default_na=False,dtype={'text_id':str})
        test=pd.read_csv(test_path,keep_default_na=False,dtype={'text_id':str})
        assert len(test)==n
        test_sources={normalized(t) for t in test.original}
        for path in [train_path,test_path]:hashes[relative(path)]=sha(path)
        draws={s:train.sample(n=3,random_state=s) for s in [42]+SEEDS}
        all_sources=[normalized(r.original) for s in draws.values() for r in s.itertuples()]
        assert len(set(all_sources))==9 and not set(all_sources)&test_sources
        for seed,draw in draws.items():
            for position,(index,row) in enumerate(draw.iterrows(),1):
                selections.append(dict(dataset=dataset,selection_seed=seed,position=position,
                    training_row_index=int(index),text_id=row.text_id,original=row.original,reference=row.reference))
        for prompt in PROMPTS:
            for strategy in STRATEGIES:
                template_path=ROOT/'prompts'/f'{dataset}_{prompt}_{strategy}.md'
                hashes[relative(template_path)]=sha(template_path)
                template=template_path.read_text(encoding='utf-8')
                expected_n=1 if strategy=='one' else 3
                baseline=extract(template)
                for e,(_,r) in zip(baseline,draws[42].iloc[:expected_n].iterrows()):
                    assert e['original']==normalized(r.original) and e['reference']==normalized(r.reference)
                for seed in SEEDS:
                    selection=draws[seed].iloc[:expected_n]
                    text=substitute(template,selection)
                    parsed=extract(text)
                    assert len(parsed)==expected_n
                    for e,(_,r) in zip(parsed,selection.iterrows()):
                        assert (e['original'],e['reference'],e['displayed_id'])==(normalized(r.original),normalized(r.reference),r.text_id)
                    output=HERE/'prompts'/f'seed_{seed}'/template_path.name
                    output.parent.mkdir(parents=True,exist_ok=True)
                    assert not output.exists()
                    output.write_text(text,encoding='utf-8')
                    hashes[relative(output)]=sha(output)
                    diffs.extend(difflib.unified_diff(template.splitlines(True),text.splitlines(True),
                        fromfile=relative(template_path),tofile=relative(output)))
                    for model,(ollama,short) in MODELS.items():
                        old=ROOT/'outputs'/(model+'_512')/f'predictions_{short}_{dataset}_{prompt}_{strategy}.csv'
                        original=pd.read_csv(old,keep_default_na=False,dtype={'text_id':str})
                        assert original[['text_id','original','reference']].equals(test[['text_id','original','reference']])
                        hashes[relative(old)]=sha(old)
                        key=f'{model}_seed{seed}_{dataset}_{prompt}_{strategy}'
                        prediction=HERE/'predictions'/model/f'seed_{seed}'/old.name
                        jobs.append(dict(job_id=key,model=model,ollama_model=ollama,dataset=dataset,prompt=prompt,
                            strategy=strategy,selection_seed=seed,n=n,prompt_path=relative(output),
                            test_path=relative(test_path),prediction_path=relative(prediction),
                            historical_prediction_path=relative(old)))
    assert len(jobs)==72 and sum(j['n'] for j in jobs)==8952
    manifest=dict(study='Reviewer 2 Concern 2: demonstration-selection variability',
        original_selection_seed=42,new_selection_seeds=SEEDS,ollama_generation_seed=42,
        new_seeds_selected_before_outputs=True,input_diversity_constraint='Distinct one-shot pairs and no shared source texts among the three sets; seeds 42--46 were inspected without generation scores',
        pandas_version=pd.__version__,options=OPTIONS,source_sha256=hashes,jobs=jobs)
    pd.DataFrame(selections).to_csv(HERE/'frozen_demonstrations.csv',index=False)
    pd.DataFrame(jobs).to_csv(HERE/'planned_runs.csv',index=False)
    (HERE/'prompt_changes.diff').write_text(''.join(diffs),encoding='utf-8')
    (HERE/'experiment_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    validate()
    print('Prepared 36 prompt files; 72 configurations; 8952 new outputs. No inference executed.')

def validate():
    m=json.loads((HERE/'experiment_manifest.json').read_text(encoding='utf-8'))
    assert len(m['jobs'])==72 and sum(j['n'] for j in m['jobs'])==8952
    assert len({j['job_id'] for j in m['jobs']})==72 and m['options']==OPTIONS
    for name,digest in m['source_sha256'].items():assert sha(ROOT/name)==digest,name
    for dataset in DATASETS:
        for seed in SEEDS:
            for strategy in STRATEGIES:
                examples=[extract((ROOT/next(j['prompt_path'] for j in m['jobs'] if j['dataset']==dataset and j['selection_seed']==seed and j['strategy']==strategy and j['prompt']==p)).read_text(encoding='utf-8')) for p in PROMPTS]
                assert len({tuple(e['pair_sha256'] for e in group) for group in examples})==1
            one=extract((HERE/'prompts'/f'seed_{seed}'/f'{dataset}_iso_one.md').read_text(encoding='utf-8'))
            few=extract((HERE/'prompts'/f'seed_{seed}'/f'{dataset}_iso_few_random.md').read_text(encoding='utf-8'))
            assert one[0]['pair_sha256']==few[0]['pair_sha256']
    return m

def runtime(model):
    import requests
    name=MODELS[model][0]
    def get(url):
        r=requests.get('http://localhost:11434'+url,timeout=30);r.raise_for_status();return r.json()
    tags=get('/api/tags');matching=[x for x in tags['models'] if x.get('name')==name or x.get('model')==name]
    assert len(matching)==1,'Model not installed; no automatic pull is performed'
    expected_path=ROOT/'experiments/focused_ablation'/('model_provenance.json' if model=='llama' else 'mixtral/model_provenance.json')
    expected=json.loads(expected_path.read_text())['digest']
    assert matching[0]['digest']==expected,'Model digest differs from the documented experiment model'
    r=requests.post('http://localhost:11434/api/show',json={'model':name},timeout=30);r.raise_for_status();show=r.json()
    info=dict(model=name,digest=matching[0]['digest'],version=get('/api/version'),
        details=show.get('details'),template=show.get('template'),parameters=show.get('parameters'),system=show.get('system'))
    folder=HERE/'runtime';folder.mkdir(exist_ok=True);path=folder/(model+'.json')
    if path.exists():assert json.loads(path.read_text())==info,'Runtime changed; do not mix execution environments silently'
    else:path.write_text(json.dumps(info,indent=2),encoding='utf-8')

def run(args):
    m=validate()
    jobs=[j for j in m['jobs'] if j['model']==args.model and j['selection_seed']==args.seed and
        (args.dataset is None or j['dataset']==args.dataset)]
    print(f"{len(jobs)} configurations / {sum(j['n'] for j in jobs)} outputs; selection seed {args.seed}; Ollama seed 42; repeat penalty 1.1",flush=True)
    if not args.execute:print('DRY RUN; use --execute to generate.');return
    sys.path.insert(0,str(ROOT))
    from model_utils import simplify_one_ollama
    runtime(args.model)
    for job in jobs:
        out=ROOT/job['prediction_path'];out.parent.mkdir(parents=True,exist_ok=True)
        log=HERE/'logs'/job['model']/f"seed_{job['selection_seed']}"/(job['job_id']+'.json')
        log.parent.mkdir(parents=True,exist_ok=True)
        current=dict(schema_version=3,job=job,options=OPTIONS,prompt_sha256=sha(ROOT/job['prompt_path']),
            test_sha256=sha(ROOT/job['test_path']),inference_code_sha256=sha(ROOT/'model_utils.py'))
        if log.exists():assert json.loads(log.read_text())==current,'Run metadata differs'
        else:
            assert not out.exists(),'Output exists without matching execution metadata'
            log.write_text(json.dumps(current,indent=2),encoding='utf-8')
        frame=pd.read_csv(ROOT/job['test_path'],keep_default_na=False,dtype={'text_id':str})
        done=pd.read_csv(out,keep_default_na=False,dtype={'text_id':str}) if out.exists() else frame.iloc[:0]
        assert len(done)<=len(frame)
        assert done[['text_id','original','reference']].equals(frame.iloc[:len(done)][['text_id','original','reference']])
        instructions=(ROOT/job['prompt_path']).read_text(encoding='utf-8')
        print(f"{job['job_id']}: {len(done)}/{len(frame)} already saved",flush=True)
        for i in range(len(done),len(frame)):
            row=frame.iloc[i]
            prediction,_,_,_,metadata=simplify_one_ollama(texto=row.original,instrucciones=instructions,
                model_name=job['ollama_model'],marker='SIMPLIFIED TEXT:',**OPTIONS)
            record=generation_record(job,row,prediction,metadata)
            pd.DataFrame([record]).to_csv(out,mode='a',header=not out.exists(),index=False,encoding='utf-8')
            print(f"  [{i+1}/{len(frame)}] {row.text_id}: {metadata.get('done_reason')}",flush=True)
        complete=log.with_suffix('.complete.json')
        complete.write_text(json.dumps(dict(rows=len(frame),prediction_sha256=sha(out),status='complete'),indent=2),encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','validate','run'])
    parser.add_argument('--model',choices=MODELS)
    parser.add_argument('--seed',type=int,choices=SEEDS)
    parser.add_argument('--dataset',choices=DATASETS)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='validate':validate();print('Validated all inputs and 72 planned configurations; no inference.')
    else:
        if args.model is None or args.seed is None:parser.error('run requires --model and --seed')
        run(args)
