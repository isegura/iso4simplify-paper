"""Evaluate saved text with identical descriptive rules across selection seeds.

No LLM calls, no semantic metric downloads, no modification of predictions.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from generate_systematic_error_analysis_512 import classify_row

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def measures(source,prediction,references):
    words=source.split();out=prediction.split();vocabulary=set(words)
    assert words,'Empty source: compression is undefined'
    return dict(LEN_COMPLEX=len(words),LEN_PRED=len(out),
        LEN_REF=sum(len(r.split()) for r in references)/len(references),
        compression_ratio=len(out)/len(words),
        copy_rate=sum(w in vocabulary for w in out)/len(out) if out else 0.0)

def evaluate(seed,model=None,dataset=None):
    m=json.loads((HERE/'experiment_manifest.json').read_text(encoding='utf-8'))
    # The seed-44 jobs provide one entry per model/dataset/prompt/strategy.
    jobs=[j for j in m['jobs'] if j['selection_seed']==(44 if seed==42 else seed)
        and (model is None or j['model']==model) and (dataset is None or j['dataset']==dataset)]
    result_root=HERE/'evaluation/descriptors'
    summaries=[];hashes={};total=0
    gold_path=ROOT/'data/tsar2025/tsar2025_test_200.csv'
    gold=pd.read_csv(gold_path,keep_default_na=False,dtype={'text_id':str})
    gold['base_id']=gold.text_id.str.extract(r'^(\d+)')
    for j in jobs:
        path=ROOT/j['historical_prediction_path' if seed==42 else 'prediction_path']
        if not path.exists():raise FileNotFoundError(f'Complete generation first: {path}')
        frame=pd.read_csv(path,keep_default_na=False,dtype={'text_id':str})
        test_path=ROOT/j['test_path']
        test=pd.read_csv(test_path,keep_default_na=False,dtype={'text_id':str})
        assert len(frame)==j['n'] and frame[['text_id','original','reference']].equals(test[['text_id','original','reference']]),path
        for p in [path,test_path]:hashes[p.relative_to(ROOT).as_posix()]=sha(p)
        if j['dataset']=='tsar2025':hashes[gold_path.relative_to(ROOT).as_posix()]=sha(gold_path)
        if seed!=42:
            complete=HERE/'logs'/j['model']/f'seed_{seed}'/(j['job_id']+'.complete.json')
            proof=json.loads(complete.read_text())
            assert proof['status']=='complete' and proof['rows']==len(frame) and proof['prediction_sha256']==sha(path)
        records=[]
        for i,row in frame.iterrows():
            if j['dataset']=='tsar2025':
                g=gold[gold.base_id==row.text_id]
                assert len(g)==2 and set(g.original)=={row.original}
                refs=g.reference.astype(str).tolist()
            else:refs=[str(row.reference)]
            derived=measures(row.original,row.prediction,refs)
            flags=classify_row(dict(model=j['model'],dataset=j['dataset'],prompt_type=j['prompt'],strategy=j['strategy'],sampling='random'),dict(row.to_dict(),**derived))
            record=dict(model=j['model'],dataset=j['dataset'],prompt=j['prompt'],strategy=j['strategy'],
                selection_seed=seed,row_index=i,text_id=row.text_id,references_json=json.dumps(refs,ensure_ascii=False),
                done_reason=row.done_reason,**derived,
                observed_input_plus_512_over_context=int(row.prompt_eval_count)+512>8192)
            for name in ['empty_prediction','reached_generation_limit','too_brief_vs_reference','ended_abruptly',
                         'format_related_marker','list_like_format','technical_or_statistical_markers']:
                record[name]=flags[name]
            records.append(record)
        items=pd.DataFrame(records)
        destination=result_root/j['model']/f'seed_{seed}'
        destination.mkdir(parents=True,exist_ok=True)
        items.to_csv(destination/f"{j['dataset']}_{j['prompt']}_{j['strategy']}_items.csv",index=False)
        aggregate=dict(model=j['model'],dataset=j['dataset'],prompt=j['prompt'],strategy=j['strategy'],selection_seed=seed,n=len(items))
        for name in ['LEN_COMPLEX','LEN_PRED','LEN_REF','compression_ratio','copy_rate']:
            aggregate['mean_'+name]=float(items[name].mean())
        for name in ['empty_prediction','reached_generation_limit','too_brief_vs_reference','ended_abruptly','format_related_marker','list_like_format','technical_or_statistical_markers']:
            aggregate[name+'_n']=int(items[name].sum())
        summaries.append(aggregate);total+=len(items)
    destination=result_root/'summaries';destination.mkdir(parents=True,exist_ok=True)
    key=f"{model or 'all_models'}_{dataset or 'all_datasets'}_seed_{seed}"
    pd.DataFrame(summaries).to_csv(destination/(key+'.csv'),index=False)
    for name,digest in hashes.items():assert sha(ROOT/name)==digest,name
    (destination/(key+'.json')).write_text(json.dumps(dict(seed=seed,configurations=len(jobs),rows=total,
        input_sha256=hashes,predictions_verified_unchanged=True,model_calls=0,
        evaluated_descriptors_only=True,semantic_metrics_computed=False,
        descriptor_code_sha256=sha(Path(__file__)),screening_code_sha256=sha(ROOT/'generate_systematic_error_analysis_512.py')),
        indent=2),encoding='utf-8')
    print(f'Evaluated descriptors: seed {seed}, {len(jobs)} configurations, {total} rows. No predictions modified; no model calls.')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',required=True,type=int,choices=[42,44,46])
    parser.add_argument('--model',choices=['llama','mixtral'])
    parser.add_argument('--dataset',choices=['cochrane','plaba','tsar2025'])
    args=parser.parse_args()
    evaluate(args.seed,args.model,args.dataset)
