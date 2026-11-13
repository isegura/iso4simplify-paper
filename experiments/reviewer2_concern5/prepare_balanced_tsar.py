"""Fix one balanced reference per TSAR training source and revalidate all prompts.

No inference, new embeddings, reranking by reference, or overwrite of older inputs.
"""
import ast
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from native_tokenizer_20261102 import Vocabulary,LIBDIR
from retrieval_engine import document_id
import study

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PREVIOUS=HERE/'context_selection_20261102'
OUT=HERE/'prepared_retrieval_20261102'
ASSIGNMENT_SEED=42


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUT.exists():raise FileExistsError('Prepared inputs exist; no automatic overwrite.')
    study.validate();old_manifest_sha=sha(HERE/'experiment_manifest.json')
    previous=json.loads((PREVIOUS/'complete.json').read_text());assert previous['all_fit']
    assert sha(LIBDIR/'libllama.dll')==previous['native_sha256']
    index=pd.read_csv(PREVIOUS/'prompt_index.csv',keep_default_na=False,dtype={'text_id':str})
    selected=pd.read_csv(PREVIOUS/'selected_examples.csv',keep_default_na=False,dtype={'test_text_id':str,'training_text_id':str})
    assert len(index)==1119 and len(selected)==1119
    for row in index.itertuples(index=False):assert sha(ROOT/row.prompt_path)==row.instructions_sha256
    train_path=ROOT/'data/tsar2025/tsar2025_train.csv'
    train=pd.read_csv(train_path,keep_default_na=False,dtype={'text_id':str})
    train['source_id']=[document_id(x,'tsar2025') for x in train.text_id]
    train['training_row_index']=range(len(train))
    source_ids=sorted(train.source_id.unique().tolist())
    assert len(train)==40 and len(source_ids)==20
    for source_id,g in train.groupby('source_id'):
        assert len(g)==2 and set(g.target_cefr)=={'a2','b1'} and g.original.nunique()==1
    permutation=np.random.Generator(np.random.PCG64(ASSIGNMENT_SEED)).permutation(len(source_ids))
    a2={source_ids[int(i)] for i in permutation[:10]}
    assignments=[];by_source={}
    for source_id in source_ids:
        level='a2' if source_id in a2 else 'b1'
        row=train[(train.source_id==source_id)&(train.target_cefr==level)].iloc[0]
        by_source[source_id]=row
        assignments.append(dict(source_id=source_id,reference_cefr=level,training_text_id=row.text_id,
            training_row_index=int(row.training_row_index),source_sha256=hashlib.sha256(row.original.encode()).hexdigest()))
    assert sum(x['reference_cefr']=='a2' for x in assignments)==10
    selected['embedding_training_row_index']=selected.training_row_index
    selected['reference_cefr']=''
    for idx,row in selected[selected.dataset=='tsar2025'].iterrows():
        candidate=by_source[document_id(row.training_text_id,'tsar2025')]
        assert candidate.original==row.original
        selected.loc[idx,['training_row_index','training_text_id','reference','reference_cefr']]=[
            int(candidate.training_row_index),candidate.text_id,candidate.reference,candidate.target_cefr]
    helper=ROOT/'experiments/reviewer2_concern2';sys.path.insert(0,str(helper))
    spec=importlib.util.spec_from_file_location('balanced_demo_slots',helper/'study.py')
    slots=importlib.util.module_from_spec(spec);spec.loader.exec_module(slots)
    from inspect_original_selection import extract
    fn=next(n for n in ast.parse((ROOT/'model_utils.py').read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='simplify_one_ollama')
    expr=next(n.value for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prompt' for t in n.targets))
    assert isinstance(expr,ast.JoinedStr) and not any(isinstance(n,ast.Call) for n in ast.walk(expr))
    code=compile(ast.Expression(expr),'actual_generation_prompt','eval')
    build=lambda text,instructions:eval(code,{'__builtins__':{}},{'texto':text,'instrucciones':instructions})
    def render(model,text):
        return ('<|start_header_id|>user<|end_header_id|>\n\n'+text+'<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n') if model=='llama' else '[INST] '+text+' [/INST] '
    OUT.mkdir();pd.DataFrame(assignments).to_csv(OUT/'tsar_reference_assignment.csv',index=False)
    selected.to_csv(OUT/'selected_examples.csv',index=False)
    tests={d:pd.read_csv(ROOT/f'data/{d}/{d}_test.csv',keep_default_na=False,dtype={'text_id':str}) for d in ['cochrane','plaba','tsar2025']}
    vocabs={};model_store=Path.home()/'.ollama/models'
    try:
        for model,name,size in [('llama','llama3.1/8b',128256),('mixtral','mixtral/latest',32000)]:
            mp=model_store/'manifests/registry.ollama.ai/library'/name
            assert sha(mp)==previous['model_proofs'][model]['manifest_digest']
            mf=json.loads(mp.read_text());digest=next(x['digest'] for x in mf['layers'] if x['mediaType']=='application/vnd.ollama.image.model')
            tp=next(x['digest'] for x in mf['layers'] if x['mediaType']=='application/vnd.ollama.image.template')
            assert sha(model_store/'blobs'/tp.replace(':','-'))==previous['model_proofs'][model]['template_sha256']
            vocabs[model]=Vocabulary(model_store/'blobs'/digest.replace(':','-'),size)
        new_index=[];counts=[];changed_tsar_prompts=0
        for entry in index.itertuples(index=False):
            original=ROOT/entry.prompt_path
            dest=OUT/'prompts'/entry.dataset/entry.prompt/f'row_{entry.row_index:03d}.md'
            dest.parent.mkdir(parents=True,exist_ok=True)
            if entry.dataset=='tsar2025':
                chosen=selected[(selected.dataset=='tsar2025')&(selected.test_row_index==entry.row_index)].sort_values('rank').copy()
                chosen=chosen.rename(columns={'training_text_id':'text_id'})
                template=(ROOT/f'prompts/tsar2025_{entry.prompt}_few_random.md').read_text(encoding='utf-8')
                text=slots.substitute(template,chosen)
                parsed=extract(text)
                assert len(parsed)==3 and text.split('EXAMPLE 1')[0]==template.split('EXAMPLE 1')[0]
                for part,(_,row) in zip(parsed,chosen.iterrows()):
                    assert (part['original'],part['reference'],part['displayed_id'])==(slots.normalized(row.original),slots.normalized(row.reference),row.text_id)
                changed_tsar_prompts+=int(text!=original.read_text(encoding='utf-8'))
                dest.write_text(text,encoding='utf-8')
            else:
                shutil.copyfile(original,dest);assert sha(original)==sha(dest)
                text=dest.read_text(encoding='utf-8')
            source=tests[entry.dataset].iloc[int(entry.row_index)]
            assert source.text_id==entry.text_id
            new_index.append(dict(dataset=entry.dataset,prompt=entry.prompt,row_index=entry.row_index,text_id=entry.text_id,prompt_path=dest.relative_to(ROOT).as_posix(),instructions_sha256=sha(dest)))
            for model,vocab in vocabs.items():
                n=len(vocab.encode(render(model,build(source.original,text))))
                assert n+512+64<=8192,(model,entry.dataset,entry.row_index,n)
                counts.append(dict(model=model,dataset=entry.dataset,prompt=entry.prompt,row_index=entry.row_index,text_id=entry.text_id,prompt_tokens=n,output_reserve=512,safety_margin=64,spare_after_output=8192-n-512,total_reserved=n+512+64,fits=True))
        frame=pd.DataFrame(counts);pd.DataFrame(new_index).to_csv(OUT/'prompt_index.csv',index=False)
        frame.to_csv(OUT/'token_counts.csv',index=False)
        frame.groupby(['model','dataset','prompt']).agg(inputs=('fits','size'),max_prompt_tokens=('prompt_tokens','max'),max_reserved=('total_reserved','max'),minimum_spare_after_output=('spare_after_output','min')).reset_index().to_csv(OUT/'summary.csv',index=False)
        assert len(frame)==2238
        for entry in index.itertuples(index=False):assert sha(ROOT/entry.prompt_path)==entry.instructions_sha256
        assert sha(HERE/'experiment_manifest.json')==old_manifest_sha;study.validate()
        tsar=selected[selected.dataset=='tsar2025']
        proof=dict(status='inputs_ready_no_generation_started',date='2026-11-02',reference_assignment_seed=ASSIGNMENT_SEED,
            reference_rng='numpy.PCG64',numpy_version=np.__version__,source_order=source_ids,
            tsar_training_sources=20,assigned_a2=10,assigned_b1=10,
            tsar_demo_occurrences=tsar.reference_cefr.value_counts().to_dict(),
            changed_tsar_prompt_files=changed_tsar_prompts,source_retrieval_selection_unchanged=True,
            prompt_files=1119,model_input_combinations=2238,all_fit=True,
            context=8192,output_reserve=512,safety_margin=64,old_manifest_unchanged=True,
            previous_selection_complete_sha256=sha(PREVIOUS/'complete.json'),
            tsar_train_sha256=sha(train_path),native_sha256=sha(LIBDIR/'libllama.dll'),
            code_sha256=sha(Path(__file__)),inference_calls=0,embedding_calls=0,
            generation_launcher_not_yet_connected=True)
        (OUT/'complete.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(proof,indent=2))
    finally:
        for v in vocabs.values():v.close()


if __name__=='__main__':main()
