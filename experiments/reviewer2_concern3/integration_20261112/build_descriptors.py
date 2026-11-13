"""Verify saved descriptors against all raw outputs and build main-study tables."""
from pathlib import Path
import csv
import hashlib
import itertools
import json
import math
import statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DEST=HERE/'delivery'
LABEL={'cochrane':'Cochrane','plaba':'PLABA','tsar2025':'TSAR~2025',
       'llama':'Llama~3.1~8B','mixtral':'Mixtral~8x7B','minimal':'Baseline',
       'iso':'ISO','iso_examples':'ISO+examples','zero':'zero','one':'one',
       'few_random':'few-random','few_metric':'few-metric','few_retrieval':'few-retrieval'}
SIZES={'cochrane':125,'plaba':148,'tsar2025':100}
MEASURES=['output_words','compression_ratio','copy_rate']

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write(p,rows):
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    DEST.mkdir(exist_ok=True)
    hashes={};runs=[];item_count=0
    for model,dataset,prompt,strategy in itertools.product(
            ['llama','mixtral'],SIZES,['minimal','iso','iso_examples'],
            ['zero','one','few_random','few_metric','few_retrieval']):
        for seed in ([42,44,46] if strategy in ['one','few_random'] else [0]):
            short='llama3_1_8b' if model=='llama' else 'mixtral_latest'
            name=f'predictions_{short}_{dataset}_{prompt}_{strategy}.csv'
            basename=f'{dataset}_{prompt}_{strategy}_items.csv'
            if strategy=='few_retrieval':
                folder=ROOT/'experiments/reviewer2_concern5/prepared_retrieval_20261102'
                raw=folder/'predictions'/model/name
                saved=folder/'evaluation'/model/basename
            elif seed in [42,44,46]:
                folder=ROOT/'experiments/reviewer2_concern2'
                raw=(ROOT/f'outputs/{model}_512'/name if seed==42 else folder/f'predictions/{model}/seed_{seed}'/name)
                saved=folder/f'evaluation/descriptors/{model}/seed_{seed}'/basename
            else:
                raw=ROOT/f'outputs/{model}_512'/name
                saved=ROOT/f'experiments/reviewer2_concern3/evaluation/historical_fixed/items/{model}'/basename
            testpath=ROOT/f'data/{dataset}/{dataset}_test.csv'
            for p in [raw,saved,testpath]:hashes[p.relative_to(ROOT).as_posix()]=digest(p)
            a,b,test=read(raw),read(saved),read(testpath)
            assert len(a)==len(b)==len(test)==SIZES[dataset]
            values=[]
            for index,(r,s,t) in enumerate(zip(a,b,test)):
                assert r['text_id']==s['text_id']==t['text_id']
                assert r['original']==t['original']
                assert int(s['row_index'])==index
                source=r['original'].split();out=r['prediction'].split();vocabulary=set(source)
                metrics=dict(output_words=len(out),compression_ratio=len(out)/len(source),
                             copy_rate=sum(x in vocabulary for x in out)/len(out) if out else 0.)
                assert int(s['LEN_COMPLEX'])==len(source)
                assert int(s['LEN_PRED'])==metrics['output_words']
                for key in ['compression_ratio','copy_rate']:
                    assert math.isclose(metrics[key],float(s[key]),rel_tol=0,abs_tol=1e-12),(saved,index,key)
                values.append(metrics)
            item_count+=len(a)
            runs.append(dict(model=model,dataset=dataset,prompt=prompt,strategy=strategy,
                             selection_seed=seed or 'fixed',n=len(a),
                             **{k:statistics.mean(r[k] for r in values) for k in MEASURES}))
    assert len(runs)==162 and item_count==20142
    rows=[]
    for model,dataset,prompt,strategy in itertools.product(
            ['llama','mixtral'],SIZES,['minimal','iso','iso_examples'],
            ['zero','one','few_random','few_metric','few_retrieval']):
        group=[r for r in runs if (r['model'],r['dataset'],r['prompt'],r['strategy'])==(model,dataset,prompt,strategy)]
        assert len(group)==(3 if strategy in ['one','few_random'] else 1)
        result=dict(model=model,dataset=dataset,prompt=prompt,strategy=strategy,selections=len(group),n_per_selection=SIZES[dataset])
        for k in MEASURES:
            result[k+'_mean']=statistics.mean(r[k] for r in group)
            result[k+'_seed_sd']=statistics.stdev(r[k] for r in group) if len(group)==3 else ''
        rows.append(result)
    assert len(rows)==90
    write(HERE/'per_selection_descriptors_162.csv',runs)
    write(HERE/'descriptors_90_mean_sd.csv',rows)
    tables=[]
    for number,(model,dataset) in enumerate(itertools.product(['llama','mixtral'],SIZES),1):
        name=f'{number:02d}_{dataset}_{model}.tex'
        table=[r'\begin{table}[htbp]',r'\centering',r'\small',
               r'\caption{\rev{Output characteristics for '+LABEL[model]+' on '+LABEL[dataset]+r'. Words denotes mean output word count; compression is the output-to-source word-count ratio; lexical overlap is the percentage of output tokens also present in the source. Random conditions report the mean and sample standard deviation across three demonstration-selection seeds.}}',
               r'\label{tab:descriptors_'+dataset+'_'+model+'}',r'\begin{tabular}{llrrr}',r'\toprule',
               r'Prompt & Strategy & Words & Compression & Lexical overlap (\%) \\',r'\midrule']
        for i,r in enumerate(x for x in rows if x['model']==model and x['dataset']==dataset):
            if i and i%5==0:table.append(r'\midrule')
            cells=[LABEL[r['prompt']],LABEL[r['strategy']]]
            for key,digits,scale in [('output_words',1,1),('compression_ratio',3,1),('copy_rate',1,100)]:
                value=f"{r[key+'_mean']*scale:,.{digits}f}"
                if r['selections']==3:value+=r' $\pm$ '+f"{r[key+'_seed_sd']*scale:,.{digits}f}"
                cells.append(value)
            table.append(' & '.join(r'\rev{'+v+'}' for v in cells)+r' \\')
        table.extend([r'\bottomrule',r'\end{tabular}',r'\end{table}'])
        block='\n'.join(table)+'\n';(DEST/name).write_text(block,encoding='utf-8');tables.append(block)
    methods=r'''\section[Output Characteristics]{\rev{Output Characteristics}}
\label{supp:output_characteristics}

\rev{We report output word count, compression ratio, and lexical overlap with the source for all main-study configurations. Words are counted by splitting on whitespace. Compression is the number of output words divided by the number of source words, calculated separately for each test item and then averaged. Values below 1 indicate shorter outputs than sources; values above 1 indicate longer outputs.}

\rev{Lexical overlap (copy rate) is the proportion of output tokens that also occur in the source. Each output token is checked against the set of source tokens, with repeated output tokens counted separately. Token matching preserves case and punctuation; no lowercasing or punctuation removal is applied. Empty outputs receive an overlap value of zero. The tables express overlap as a percentage. This measure describes shared vocabulary, not the proportion of copied phrases or sentences, and does not assess factual accuracy or meaning preservation.}

\rev{For each configuration and selection, the three measures are averaged over all test rows. For one-shot and random few-shot, we report the mean and sample standard deviation of these averages across seeds 42, 44, and 46. The other strategies contribute one evaluated selection each. All outputs are retained, including empty responses and outputs reaching the generation limit. These are descriptive summaries, with no significance tests. Output length, compression, and lexical overlap alone do not establish simplification quality, reader comprehension, or adherence to ISO principles.}

'''
    (DEST/'output_characteristics_all.tex').write_text(methods+'\n'.join(tables),encoding='utf-8')
    paper=r'''\rev{We also describe the outputs using word count, the output-to-source word-count ratio, and lexical overlap with the source. These measures help characterize compression and shared vocabulary but do not establish meaning preservation or reader comprehension. Definitions and results for all configurations are provided in the Supplementary Material.}
'''
    (DEST/'paper_descriptor_methods.tex').write_text(paper,encoding='utf-8')
    for p,h in hashes.items():assert digest(ROOT/p)==h
    proof=dict(configurations=162,scored_outputs=20142,reported_rows=90,
               saved_descriptor_values_verified_against_raw_outputs=True,input_files_unchanged=True,
               inference_calls=0,source_sha256=hashes)
    (HERE/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in proof.items() if k!='source_sha256'},indent=2))

if __name__=='__main__':main()
