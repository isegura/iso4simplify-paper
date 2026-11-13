"""Count frozen complete prompts with native model vocabularies; never generate text."""
import ast
import csv
import hashlib
import json
from pathlib import Path
import pandas as pd
from native_tokenizer import Vocabulary,LIBDIR

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'token_preflight'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if (OUT/'complete.json').exists():
        raise FileExistsError('Preflight already exists; review it before replacing evidence.')
    import study
    manifest=study.validate()
    index=pd.read_csv(HERE/'prompt_index.csv',keep_default_na=False,dtype={'text_id':str})
    assert len(index)==1119
    # Evaluate only the literal f-string assigned to prompt in the actual generation helper.
    tree=ast.parse((ROOT/'model_utils.py').read_text(encoding='utf-8'))
    helper=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='simplify_one_ollama')
    expr=next(n.value for n in helper.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prompt' for t in n.targets))
    assert isinstance(expr,ast.JoinedStr) and not any(isinstance(n,ast.Call) for n in ast.walk(expr))
    code=compile(ast.Expression(expr),'generation_prompt_fstring','eval')
    build=lambda original,instructions:eval(code,{'__builtins__':{}},{'texto':original,'instrucciones':instructions})
    old=json.loads((ROOT/'experiments/reviewer2_concern2/experiment_manifest.json').read_text(encoding='utf-8'))
    test={d:pd.read_csv(ROOT/f'data/{d}/{d}_test.csv',keep_default_na=False,dtype={'text_id':str}) for d in ['cochrane','plaba','tsar2025']}
    models=Path.home()/'.ollama/models'
    records=[];calibration=[];input_hashes={};model_proofs={}
    for model,name,vocab_size,showname in [('llama','llama3.1/8b',128256,'llama3.1_show.json'),('mixtral','mixtral/latest',32000,'mixtral_show.json')]:
        mpath=models/'manifests/registry.ollama.ai/library'/name
        m=json.loads(mpath.read_text());digest=sha(mpath)
        provenance=ROOT/'experiments/focused_ablation'/('model_provenance.json' if model=='llama' else 'mixtral/model_provenance.json')
        assert digest==json.loads(provenance.read_text())['digest']
        show=json.loads((OUT/showname).read_text(encoding='utf-8'))
        assert not show.get('system')
        t_layer=next(x for x in m['layers'] if x['mediaType']=='application/vnd.ollama.image.template')
        t_path=models/'blobs'/t_layer['digest'].replace(':','-')
        assert t_path.read_text(encoding='utf-8')==show['template']
        assert ('<|start_header_id|>' in show['template']) if model=='llama' else (show['template']=='[INST] {{ if .System }}{{ .System }} {{ end }}{{ .Prompt }} [/INST] {{ .Response }}\n')
        def render(content):
            if model=='llama':return '<|start_header_id|>user<|end_header_id|>\n\n'+content+'<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n'
            return '[INST] '+content+' [/INST] '
        layer=next(x for x in m['layers'] if x['mediaType']=='application/vnd.ollama.image.model')
        blob=models/'blobs'/layer['digest'].replace(':','-')
        vocab=Vocabulary(blob,vocab_size)
        try:
            # Held-out saved generations: first, middle and last row of all 18 seed-44 conditions/model.
            for job in [j for j in old['jobs'] if j['model']==model and j['selection_seed']==44]:
                path=ROOT/job['prediction_path'];proof_path=ROOT/f"experiments/reviewer2_concern2/logs/{model}/seed_44/{job['job_id']}.complete.json"
                cert=json.loads(proof_path.read_text());assert cert['status']=='complete' and cert['prediction_sha256']==sha(path)
                prompt=ROOT/job['prompt_path'];instructions=prompt.read_text(encoding='utf-8')
                saved=pd.read_csv(path,keep_default_na=False,dtype={'text_id':str})
                for idx in [0,len(saved)//2,len(saved)-1]:
                    row=saved.iloc[idx];count=len(vocab.encode(render(build(row.original,instructions))))
                    calibration.append(dict(model=model,job=job['job_id'],row_index=idx,offline_tokens=count,recorded_tokens=int(row.prompt_eval_count),matches=count==int(row.prompt_eval_count)))
                for p in [path,prompt,proof_path]:input_hashes[p.relative_to(ROOT).as_posix()]=sha(p)
            assert all(r['matches'] for r in calibration), 'Template/tokenizer did not reproduce recorded counts'
            for entry in index.itertuples(index=False):
                prompt=ROOT/entry.prompt_path;assert sha(prompt)==entry.instructions_sha256
                row=test[entry.dataset].iloc[int(entry.row_index)];assert row.text_id==entry.text_id
                content=build(row.original,prompt.read_text(encoding='utf-8'));rendered=render(content)
                tokens=len(vocab.encode(rendered));records.append(dict(model=model,dataset=entry.dataset,prompt=entry.prompt,row_index=entry.row_index,text_id=entry.text_id,instruction_path=entry.prompt_path,instruction_sha256=sha(prompt),complete_rendered_sha256=hashlib.sha256(rendered.encode()).hexdigest(),prompt_tokens=tokens,reserved_output_tokens=512,context=8192,total_budget=tokens+512,spare_tokens=8192-512-tokens,fits=tokens+512<=8192))
                input_hashes[entry.prompt_path]=sha(prompt)
            (OUT/(model+'_vocabulary_load.log')).write_text(''.join(vocab.logs),encoding='utf-8')
            model_proofs[model]=dict(ollama_model=name,manifest_digest=digest,gguf_layer_digest=layer['digest'],template_sha256=sha(t_path),vocabulary_size=vocab_size,vocab_only=True,weights_skipped=True,backend_context_created=False)
        finally:vocab.close()
    assert len(records)==2238 and len(calibration)==108
    frame=pd.DataFrame(records)
    frame.to_csv(OUT/'per_input_token_counts.csv',index=False)
    pd.DataFrame(calibration).to_csv(OUT/'historical_count_validation.csv',index=False)
    summary=frame.groupby(['model','dataset','prompt'],sort=True).agg(inputs=('fits','size'),min_prompt_tokens=('prompt_tokens','min'),max_prompt_tokens=('prompt_tokens','max'),max_total_budget=('total_budget','max'),minimum_spare_tokens=('spare_tokens','min'),fits=('fits','sum')).reset_index()
    summary['over_budget']=summary.inputs-summary.fits
    summary.to_csv(OUT/'summary.csv',index=False)
    for d in test:input_hashes[f'data/{d}/{d}_test.csv']=sha(ROOT/f'data/{d}/{d}_test.csv')
    for name,digest in input_hashes.items():assert sha(ROOT/name)==digest,name
    result=dict(status='complete',all_fit=bool(frame.fits.all()),outputs_checked=2238,over_budget=int((~frame.fits).sum()),historical_count_checks=108,historical_count_mismatches=0,native_library_sha256=sha(LIBDIR/'libllama.dll'),native_build='620d2225c',model_proofs=model_proofs,input_sha256=input_hashes,model_utils_sha256=sha(ROOT/'model_utils.py'),preflight_code_sha256=sha(Path(__file__)),tokenizer_wrapper_sha256=sha(HERE/'native_tokenizer.py'),generated_simplifications=0,gpu_model_loads=0,templates_reconstructed_for_one_user_message_no_system_no_tools=True,limitation='Offline exact-vocabulary counts validated against 108 saved Ollama inputs; not a guarantee of behavior after runtime/template/model changes.')
    (OUT/'complete.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(summary.to_string(index=False))
    print('Total over budget:',result['over_budget'],'of',len(frame),'; no generated text.')


if __name__=='__main__':main()
