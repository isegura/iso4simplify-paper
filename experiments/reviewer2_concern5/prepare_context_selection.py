"""Prepare best-first context-constrained triples separately; never generate text."""
import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from native_tokenizer_20261102 import Vocabulary,LIBDIR
from budgeted_search import best_feasible_triple
from retrieval_engine import normalized,document_id
import study

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'context_selection_20261102'
LIMIT=8192-512-64


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if (OUT/'complete.json').exists() or (OUT/'prompts').exists():
        raise FileExistsError('A completed or partial search exists; inspect before replacing.')
    frozen=study.validate();frozen_sha=sha(HERE/'experiment_manifest.json')
    old_proof=json.loads((HERE/'token_preflight/complete.json').read_text())
    helper=ROOT/'experiments/reviewer2_concern2';sys.path.insert(0,str(helper))
    spec=importlib.util.spec_from_file_location('fixed_slots',helper/'study.py')
    slots=importlib.util.module_from_spec(spec);spec.loader.exec_module(slots)
    from inspect_original_selection import extract
    tree=ast.parse((ROOT/'model_utils.py').read_text(encoding='utf-8'))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='simplify_one_ollama')
    expr=next(n.value for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prompt' for t in n.targets))
    assert isinstance(expr,ast.JoinedStr) and not any(isinstance(n,ast.Call) for n in ast.walk(expr))
    code=compile(ast.Expression(expr),'actual_prompt','eval')
    build=lambda text,instructions:eval(code,{'__builtins__':{}},{'texto':text,'instrucciones':instructions})
    def render(model,text):
        return ('<|start_header_id|>user<|end_header_id|>\n\n'+text+'<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n') if model=='llama' else '[INST] '+text+' [/INST] '
    models=Path.home()/'.ollama/models';vocabs={};calibration=[];input_hashes={};model_proofs={}
    old_study=json.loads((helper/'experiment_manifest.json').read_text())
    try:
        for model,name,size in [('llama','llama3.1/8b',128256),('mixtral','mixtral/latest',32000)]:
            mp=models/'manifests/registry.ollama.ai/library'/name
            assert sha(mp)==old_proof['model_proofs'][model]['manifest_digest']
            mf=json.loads(mp.read_text());metadata=json.loads((OUT/(model+'_metadata.json')).read_text())
            assert not metadata.get('system')
            template_digest=next(x['digest'] for x in mf['layers'] if x['mediaType']=='application/vnd.ollama.image.template')
            tp=models/'blobs'/template_digest.replace(':','-')
            assert tp.read_text(encoding='utf-8')==metadata['template']
            assert sha(tp)==old_proof['model_proofs'][model]['template_sha256']
            digest=next(x['digest'] for x in mf['layers'] if x['mediaType']=='application/vnd.ollama.image.model')
            assert digest==old_proof['model_proofs'][model]['gguf_layer_digest']
            vocabs[model]=Vocabulary(models/'blobs'/digest.replace(':','-'),size)
            model_proofs[model]=dict(manifest_digest=sha(mp),template_sha256=sha(tp),gguf_layer_digest=digest)
            for job in [j for j in old_study['jobs'] if j['model']==model and j['selection_seed']==44]:
                path=ROOT/job['prediction_path'];pp=ROOT/job['prompt_path']
                cert=ROOT/f"experiments/reviewer2_concern2/logs/{model}/seed_44/{job['job_id']}.complete.json"
                assert json.loads(cert.read_text())['prediction_sha256']==sha(path)
                saved=pd.read_csv(path,keep_default_na=False,dtype={'text_id':str})
                instructions=pp.read_text(encoding='utf-8')
                for i in [0,len(saved)//2,len(saved)-1]:
                    row=saved.iloc[i];count=len(vocabs[model].encode(render(model,build(row.original,instructions))))
                    calibration.append(dict(model=model,job_id=job['job_id'],row_index=i,count=count,recorded=int(row.prompt_eval_count),matches=count==int(row.prompt_eval_count)))
                for p in [path,pp,cert]:input_hashes[p.relative_to(ROOT).as_posix()]=sha(p)
        assert len(calibration)==108 and all(x['matches'] for x in calibration)
        pd.DataFrame(calibration).to_csv(OUT/'tokenizer_revalidation.csv',index=False)
        print('Current native tokenizer: 108/108 recorded counts matched.',flush=True)
        original_selections=pd.read_csv(HERE/'selected_examples.csv',keep_default_na=False)
        sources=[];selected=[];counts=[];prompt_index=[]
        for dataset in ['cochrane','plaba','tsar2025']:
            train_path=ROOT/f'data/{dataset}/{dataset}_train.csv';test_path=ROOT/f'data/{dataset}/{dataset}_test.csv'
            train=pd.read_csv(train_path,keep_default_na=False,dtype={'text_id':str});test=pd.read_csv(test_path,keep_default_na=False,dtype={'text_id':str})
            train['training_row_index']=range(len(train));train['normalized_source']=train.original.map(normalized)
            pool=train.drop_duplicates('normalized_source',keep='first')
            pool=pool[~pool.normalized_source.isin(set(test.original.map(normalized)))].reset_index(drop=True)
            docs=[document_id(x,dataset) for x in pool.text_id];keys=pool.normalized_source.tolist();training_rows=pool.training_row_index.to_numpy()
            npz=HERE/'embeddings'/f'{dataset}.npz';pf=HERE/'embeddings'/f'{dataset}.json'
            assert json.loads(pf.read_text())['cache_sha256']==sha(npz)
            with np.load(npz) as cached:
                assert list(cached['training_row_index'])==list(training_rows)
                similarities=cached['queries'].astype(np.float64)@cached['train'].astype(np.float64).T
            query_lookup={text:i for i,text in enumerate(test.drop_duplicates('original').original.tolist())}
            templates={p:(ROOT/f'prompts/{dataset}_{p}_few_random.md').read_text(encoding='utf-8') for p in ['minimal','iso','iso_examples']}
            for p in [train_path,test_path,npz,pf]+[ROOT/f'prompts/{dataset}_{p}_few_random.md' for p in templates]:input_hashes[p.relative_to(ROOT).as_posix()]=sha(p)
            cache={}
            for row_index,row in test.iterrows():
                score=similarities[query_lookup[row.original]]
                source_key=normalized(row.original);source_id=document_id(row.text_id,dataset)
                eligible=[i for i in range(len(pool)) if keys[i]!=source_key and docs[i]!=source_id]
                def evaluate(ids,full=False):
                    chosen=pool.iloc[ids];texts={p:slots.substitute(templates[p],chosen) for p in templates};tokens={}
                    for model,prompt in [('mixtral','iso_examples'),('llama','iso_examples')]+[(m,p) for m in ['llama','mixtral'] for p in ['minimal','iso']]:
                        n=len(vocabs[model].encode(render(model,build(row.original,texts[prompt]))));tokens[model,prompt]=n
                        if n>LIMIT and not full:return False,None
                    return all(n<=LIMIT for n in tokens.values()),(texts,tokens)
                # Identical source/id rows reuse source-only selection, preserving PLABA dependence.
                query_key=(row.original,source_id)
                if query_key in cache:
                    ids,certificate=cache[query_key]
                else:
                    ids,certificate=best_feasible_triple(score,training_rows,docs,keys,lambda ids:evaluate(ids)[0],eligible,max_checks=5000)
                    cache[query_key]=(ids,certificate)
                okay,(texts,tokens)=evaluate(ids,full=True);assert okay and len(tokens)==6
                prior=original_selections[(original_selections.dataset==dataset)&(original_selections.test_row_index==row_index)].sort_values('rank')
                changed=list(prior.training_row_index)!=list(pool.iloc[ids].training_row_index)
                sources.append(dict(dataset=dataset,row_index=row_index,text_id=row.text_id,changed=changed,
                    original_mean_cosine=float(prior.cosine_similarity.mean()),selected_mean_cosine=certificate['mean_cosine'],
                    selected_ranks=json.dumps(certificate['ranks']),candidate_checks=certificate['checked'],optimal_stored_score=True,
                    retained_original_examples=len(set(prior.training_row_index)&set(pool.iloc[ids].training_row_index))))
                for rank,i in enumerate(ids,1):
                    ex=pool.iloc[i]
                    selected.append(dict(dataset=dataset,test_row_index=row_index,test_text_id=row.text_id,rank=rank,retrieval_rank=certificate['ranks'][rank-1],training_row_index=int(ex.training_row_index),training_text_id=ex.text_id,cosine_similarity=float(score[i]),original=ex.original,reference=ex.reference))
                for prompt,text in texts.items():
                    parsed=extract(text);assert len(parsed)==3 and text.split('EXAMPLE 1')[0]==templates[prompt].split('EXAMPLE 1')[0]
                    for part,i in zip(parsed,ids):
                        ex=pool.iloc[i]
                        assert (part['original'],part['reference'],part['displayed_id'])==(slots.normalized(ex.original),slots.normalized(ex.reference),ex.text_id)
                    dest=OUT/'prompts'/dataset/prompt/f'row_{row_index:03d}.md';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text,encoding='utf-8')
                    prompt_index.append(dict(dataset=dataset,prompt=prompt,row_index=row_index,text_id=row.text_id,prompt_path=dest.relative_to(ROOT).as_posix(),instructions_sha256=sha(dest)))
                    for model in ['llama','mixtral']:
                        n=tokens[model,prompt];counts.append(dict(model=model,dataset=dataset,prompt=prompt,row_index=row_index,text_id=row.text_id,prompt_tokens=n,output_reserve=512,safety_margin=64,total_reserved=n+512+64,spare_after_output=8192-n-512,fits=n<=LIMIT))
                if row_index%10==0 or changed:print(f'{dataset} {row_index+1}/{len(test)}: ranks {certificate["ranks"]}, checks {certificate["checked"]}',flush=True)
        frame=pd.DataFrame(counts);source_frame=pd.DataFrame(sources)
        assert len(frame)==2238 and frame.fits.all() and len(selected)==1119 and len(prompt_index)==1119
        for name,digest in input_hashes.items():assert sha(ROOT/name)==digest,name
        assert sha(HERE/'experiment_manifest.json')==frozen_sha;study.validate()
        frame.to_csv(OUT/'token_counts.csv',index=False);source_frame.to_csv(OUT/'selection_changes.csv',index=False)
        pd.DataFrame(selected).to_csv(OUT/'selected_examples.csv',index=False);pd.DataFrame(prompt_index).to_csv(OUT/'prompt_index.csv',index=False)
        frame.groupby(['model','dataset','prompt']).agg(inputs=('fits','size'),max_prompt_tokens=('prompt_tokens','max'),max_reserved=('total_reserved','max'),minimum_spare_after_output=('spare_after_output','min')).reset_index().to_csv(OUT/'summary.csv',index=False)
        proof=dict(status='complete_context_selection_provisional_tsar_policy',date='2026-11-02',all_fit=True,
            context=8192,output_reserve=512,safety_margin=64,source_rows=373,prompt_files=1119,model_input_combinations=2238,
            tokenizer_checks=108,tokenizer_mismatches=0,model_proofs=model_proofs,native_sha256=sha(LIBDIR/'libllama.dll'),
            native_build='39febd2ad',ollama_version_observed='0.40.13',fixed_original_manifest_sha256=frozen_sha,
            original_inputs_unchanged=True,old_study_still_active=True,tsar_reference_policy_unchanged=True,
            inference_calls=0,new_embeddings=0,search_complete_for_all_rows=True,
            max_checks_observed=int(source_frame.candidate_checks.max()),changed_rows=int(source_frame.changed.sum()),
            input_sha256=input_hashes,code_sha256={f.name:sha(f) for f in [Path(__file__),HERE/'budgeted_search.py',HERE/'native_tokenizer_20261102.py',OUT/'METHOD.md']})
        (OUT/'complete.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
        print('Complete: all 2238 combinations fit, 64-token safety margin retained.',flush=True)
    finally:
        for v in vocabs.values():v.close()


if __name__=='__main__':main()
