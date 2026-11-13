"""Feasibility only: preserve the nearest examples when repairing a context overflow.

Does not change frozen prompts, manifests, inference options, or model weights.
Candidate selections are provisional and have no generation command.
"""
import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from native_tokenizer import Vocabulary
from retrieval_engine import normalized,document_id
import study

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'budget_feasibility'
PROMPTS=['minimal','iso','iso_examples']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUT.exists() and any(OUT.iterdir()):raise FileExistsError('Keep the existing feasibility evidence; no automatic replacement.')
    manifest=study.validate()
    frozen_before=sha(HERE/'experiment_manifest.json')
    OUT.mkdir(exist_ok=True)
    helper=ROOT/'experiments/reviewer2_concern2'
    sys.path.insert(0,str(helper))
    spec=importlib.util.spec_from_file_location('existing_slots',helper/'study.py')
    slots=importlib.util.module_from_spec(spec);spec.loader.exec_module(slots)
    from inspect_original_selection import extract
    tree=ast.parse((ROOT/'model_utils.py').read_text(encoding='utf-8'))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='simplify_one_ollama')
    expr=next(n.value for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prompt' for t in n.targets))
    assert isinstance(expr,ast.JoinedStr) and not any(isinstance(n,ast.Call) for n in ast.walk(expr))
    expression=compile(ast.Expression(expr),'original_generation_prompt','eval')
    full=lambda text,instructions:eval(expression,{'__builtins__':{}},{'texto':text,'instrucciones':instructions})
    models=Path.home()/'.ollama/models'
    vocabs={}
    for model,name,size in [('llama','llama3.1/8b',128256),('mixtral','mixtral/latest',32000)]:
        mf=json.loads((models/'manifests/registry.ollama.ai/library'/name).read_text())
        digest=next(x['digest'] for x in mf['layers'] if x['mediaType']=='application/vnd.ollama.image.model')
        vocabs[model]=Vocabulary(models/'blobs'/digest.replace(':','-'),size)
    render=lambda model,text:('<|start_header_id|>user<|end_header_id|>\n\n'+text+'<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n') if model=='llama' else '[INST] '+text+' [/INST] '
    original_selections=pd.read_csv(HERE/'selected_examples.csv',keep_default_na=False,dtype={'test_text_id':str,'training_text_id':str})
    old_counts=pd.read_csv(HERE/'token_preflight/per_input_token_counts.csv')
    source_results=[];selected_records=[];token_records=[];input_hashes={}
    try:
        for dataset in ['cochrane','plaba','tsar2025']:
            train_path=ROOT/f'data/{dataset}/{dataset}_train.csv';test_path=ROOT/f'data/{dataset}/{dataset}_test.csv'
            train=pd.read_csv(train_path,keep_default_na=False,dtype={'text_id':str});test=pd.read_csv(test_path,keep_default_na=False,dtype={'text_id':str})
            train['training_row_index']=range(len(train));train['normalized_source']=train.original.map(normalized)
            pool=train.drop_duplicates('normalized_source',keep='first')
            pool=pool[~pool.normalized_source.isin(set(test.original.map(normalized)))].reset_index(drop=True)
            pool_keys=pool.normalized_source.tolist()
            pool_ids=[document_id(value,dataset) for value in pool.text_id]
            character_costs=[len(str(o))+len(str(r)) for o,r in zip(pool.original,pool.reference)]
            npz=HERE/'embeddings'/f'{dataset}.npz';proof=HERE/'embeddings'/f'{dataset}.json'
            assert json.loads(proof.read_text())['cache_sha256']==sha(npz)
            with np.load(npz) as cached:
                assert pool.training_row_index.tolist()==cached['training_row_index'].tolist()
                scores=cached['queries'].astype(np.float64)@cached['train'].astype(np.float64).T
            unique=test.drop_duplicates('original',keep='first').original.tolist();query_lookup={s:i for i,s in enumerate(unique)}
            templates={p:(ROOT/f'prompts/{dataset}_{p}_few_random.md').read_text(encoding='utf-8') for p in PROMPTS}
            input_hashes.update({p.relative_to(ROOT).as_posix():sha(p) for p in [train_path,test_path,npz,proof]})
            for row_index,row in test.iterrows():
                cosine=scores[query_lookup[row.original]]
                order=np.lexsort((pool.training_row_index.to_numpy(),-cosine))
                source_key=normalized(row.original);source_id=document_id(row.text_id,dataset)
                eligible=[int(i) for i in order if pool_keys[int(i)]!=source_key and pool_ids[int(i)]!=source_id]
                short_order=sorted(eligible,key=lambda i:(character_costs[i],int(pool.iloc[i].training_row_index)))
                rank={idx:i+1 for i,idx in enumerate(eligible)}
                previous=original_selections[(original_selections.dataset==dataset)&(original_selections.test_row_index==row_index)].sort_values('rank')
                original=[int(pool.index[pool.training_row_index==v][0]) for v in previous.training_row_index]
                assert len(original)==3
                def ordered(ids):return sorted(ids,key=lambda i:rank[i])
                def distinct(ids):
                    return len(ids)==3 and len({document_id(pool.iloc[i].text_id,dataset) for i in ids})==3 and len({normalized(pool.iloc[i].original) for i in ids})==3
                memo={}
                def evaluate(ids,all_counts=False):
                    ids=tuple(ordered(ids))
                    if ids not in memo:
                        if not distinct(ids):return False,None
                        chosen=pool.iloc[list(ids)]
                        texts={p:slots.substitute(templates[p],chosen) for p in PROMPTS}
                        counts={}
                        # Reject using the historically most restrictive combination first.
                        sequence=[('mixtral','iso_examples'),('llama','iso_examples')]+[(m,p) for m in ['llama','mixtral'] for p in ['minimal','iso']]
                        fits=True
                        for model,prompt in sequence:
                            count=len(vocabs[model].encode(render(model,full(row.original,texts[prompt]))))
                            counts[model,prompt]=count
                            if count+512>8192:
                                fits=False
                                if not all_counts:break
                        memo[ids]=(fits,counts,texts)
                    fits,counts,texts=memo[ids]
                    if all_counts and len(counts)!=6:
                        del memo[ids];return evaluate(ids,all_counts=True)
                    return fits,(counts,texts)
                fits,_=evaluate(original)
                choice=list(original);method='unchanged_top3';candidates_tried=0
                if not fits:
                    choice=None
                    # Keep the two nearest originals and take the highest ranked remaining
                    # eligible third document whose full six prompts meet the budget.
                    # A short-example witness prevents an expensive exhaustive search
                    # when the fixed top-two prefix itself leaves almost no room.
                    # Character length is a search heuristic only: acceptance always
                    # requires native counts of all six complete prompts.
                    witness=None
                    for third in short_order[:30]:
                        if third in original[:2]:continue
                        candidates_tried+=1
                        trial=ordered(original[:2]+[third])
                        if evaluate(trial)[0]:witness=trial;break
                    if witness is not None:
                        choice=witness;method='keep_top2_short_witness'
                        for third in eligible[:128]:
                            if third in original[:2]:continue
                            candidates_tried+=1;trial=ordered(original[:2]+[third])
                            if evaluate(trial)[0]:choice=trial;method='keep_top2_ranked_scan';break
                    if choice is None:
                        # A deterministic completion witness proves feasibility, not global
                        # optimality: preserve the top document and try short full examples.
                        shorts=short_order[:30]
                        for second in eligible[:128]:
                            if second==original[0]:continue
                            found=False
                            for third in shorts:
                                if third in [original[0],second]:continue
                                candidates_tried+=1;trial=ordered([original[0],second,third])
                                if evaluate(trial)[0]:choice=trial;method='keep_top1_short_completion_witness';found=True;break
                            if found:break
                    if choice is None:
                        # Final viability witness: three shortest distinct eligible documents.
                        shorts=short_order
                        for start in range(min(20,len(shorts)-2)):
                            trial=ordered(shorts[start:start+3]);candidates_tried+=1
                            if evaluate(trial)[0]:choice=trial;method='short_triple_feasibility_only';break
                if choice is None:raise ValueError(f'No witness found for {dataset}/{row_index}; this does not prove infeasibility')
                okay,result=evaluate(choice,all_counts=True);assert okay
                counts,texts=result
                changed=choice!=original
                source_results.append(dict(dataset=dataset,row_index=row_index,text_id=row.text_id,changed=changed,method=method,kept_top1=original[0] in choice,kept_top2=all(i in choice for i in original[:2]),retained_original_examples=len(set(choice)&set(original)),original_mean_cosine=float(np.mean(cosine[original])),candidate_mean_cosine=float(np.mean(cosine[choice])),selected_retrieval_ranks=json.dumps([rank[i] for i in choice]),candidate_checks=candidates_tried))
                for pos,i in enumerate(choice,1):
                    example=pool.iloc[i]
                    selected_records.append(dict(dataset=dataset,test_row_index=row_index,test_text_id=row.text_id,rank=pos,retrieval_rank=rank[i],training_row_index=int(example.training_row_index),training_text_id=example.text_id,cosine_similarity=float(cosine[i]),original=example.original,reference=example.reference))
                for prompt,text in texts.items():
                    parsed=extract(text)
                    assert len(parsed)==3 and text.split('EXAMPLE 1')[0]==templates[prompt].split('EXAMPLE 1')[0]
                    for item,idx in zip(parsed,choice):
                        example=pool.iloc[idx]
                        assert item['original']==slots.normalized(example.original) and item['reference']==slots.normalized(example.reference) and item['displayed_id']==example.text_id
                    if not changed:
                        frozen=HERE/'prompts'/dataset/prompt/f'row_{row_index:03d}.md'
                        assert frozen.read_text(encoding='utf-8')==text
                    for model in ['llama','mixtral']:
                        count=counts[model,prompt]
                        token_records.append(dict(model=model,dataset=dataset,prompt=prompt,row_index=row_index,text_id=row.text_id,prompt_tokens=count,total_budget=count+512,spare_tokens=7680-count,fits=count+512<=8192,changed_selection=changed,instructions_sha256=hashlib.sha256(text.encode()).hexdigest()))
                if row_index%25==0:print(f'{dataset}: {row_index+1}/{len(test)} checked',flush=True)
    finally:
        for vocab in vocabs.values():vocab.close()
    sources=pd.DataFrame(source_results);counts=pd.DataFrame(token_records);selections=pd.DataFrame(selected_records)
    assert len(sources)==373 and len(counts)==2238 and len(selections)==1119 and counts.fits.all()
    for name,digest in input_hashes.items():assert sha(ROOT/name)==digest
    assert sha(HERE/'experiment_manifest.json')==frozen_before
    study.validate()
    sources.to_csv(OUT/'source_selection_changes.csv',index=False)
    selections.to_csv(OUT/'candidate_selections.csv',index=False)
    counts.to_csv(OUT/'candidate_token_counts.csv',index=False)
    summary=counts.groupby(['model','dataset','prompt'],sort=True).agg(inputs=('fits','size'),max_prompt_tokens=('prompt_tokens','max'),max_total_budget=('total_budget','max'),minimum_spare_tokens=('spare_tokens','min'),fits=('fits','sum')).reset_index()
    summary.to_csv(OUT/'summary.csv',index=False)
    result=dict(status='complete_feasibility_only',queries=373,model_prompt_queries=2238,all_fit=True,changed_source_rows=int(sources.changed.sum()),kept_top1_all=bool(sources.kept_top1.all()),kept_top2_all=bool(sources.kept_top2.all()),methods=sources.method.value_counts().to_dict(),frozen_manifest_sha256=frozen_before,frozen_inputs_unchanged=True,input_sha256=input_hashes,code_sha256=sha(Path(__file__)),generation_calls=0,embedding_calls=0,active_prompts_changed=False,active_experiment_changed=False,tsar_reference_policy_changed=False,search_is_globally_optimal=False,short_witness_candidates=30,ranked_scan_candidates=128)
    (OUT/'complete.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
