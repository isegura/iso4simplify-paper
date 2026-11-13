"""Audit all 162 main-study runs from saved metadata; never run inference."""
from pathlib import Path
import csv, hashlib, itertools, json, statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RETR = ROOT / 'experiments/reviewer2_concern5/prepared_retrieval_20261102'
DATASETS = {'cochrane': 125, 'plaba': 148, 'tsar2025': 100}
PROMPTS = ['minimal', 'iso', 'iso_examples']
STRATEGIES = ['zero', 'one', 'few_random', 'few_metric', 'few_retrieval']
LABEL = {'minimal':'Baseline','iso':'ISO','iso_examples':'ISO+examples',
         'cochrane':'Cochrane','plaba':'PLABA','tsar2025':'TSAR~2025',
         'zero':'zero','one':'one','few_random':'few-random',
         'few_metric':'few-metric','few_retrieval':'few-retrieval'}

def read(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def write(name, rows):
    with (HERE/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    runs=[]; items=[]; hashes={}; checks=[]
    preflight={(r['model'],r['dataset'],r['prompt'],int(r['row_index'])):int(r['prompt_tokens'])
               for r in read(RETR/'token_counts.csv')}
    hashes[str((RETR/'token_counts.csv').relative_to(ROOT))]=sha(RETR/'token_counts.csv')
    for model,dataset,prompt,strategy in itertools.product(['llama','mixtral'],DATASETS,PROMPTS,STRATEGIES):
        short='llama3_1_8b' if model=='llama' else 'mixtral_latest'
        testpath=ROOT/f'data/{dataset}/{dataset}_test.csv'
        test=read(testpath); hashes[str(testpath.relative_to(ROOT))]=sha(testpath)
        seeds=[42,44,46] if strategy in ['one','few_random'] else [0]
        for seed in seeds:
            name=f'predictions_{short}_{dataset}_{prompt}_{strategy}.csv'
            if strategy=='few_retrieval': p=RETR/'predictions'/model/name
            elif seed in [44,46]: p=ROOT/f'experiments/reviewer2_concern2/predictions/{model}/seed_{seed}'/name
            else: p=ROOT/f'outputs/{model}_512'/name
            data=read(p); hashes[str(p.relative_to(ROOT))]=sha(p)
            assert len(data)==DATASETS[dataset], p
            assert [(r['text_id'],r['original']) for r in data]==[(r['text_id'],r['original']) for r in test],p
            base=dict(model=model,dataset=dataset,prompt=prompt,strategy=strategy,selection_seed=seed or 'fixed')
            current=[]
            for i,r in enumerate(data):
                tokens=int(r['prompt_eval_count']); generated=int(r['eval_count'])
                assert tokens>0 and int(r['num_ctx'])==8192 and int(r['num_predict'])==512,p
                assert r['done_reason'] in ['length','stop'],(p,i,r['done_reason'])
                capped=r['done_reason']=='length'
                if strategy=='few_retrieval':
                    assert tokens==preflight[model,dataset,prompt,i]==int(r['preflight_prompt_tokens'])
                    assert tokens<=7616
                row=dict(**base,row_index=i,text_id=r['text_id'],done_reason=r['done_reason'],
                         generated_tokens=generated,prompt_eval_count=tokens,token_capped=int(capped),
                         empty_output=int(not r['prediction'].strip()),headroom_after_512=8192-512-tokens,
                         prediction_path=str(p.relative_to(ROOT)))
                current.append(row);items.append(row)
            vals=[r['prompt_eval_count'] for r in current]
            runs.append(dict(**base,n=len(data),capped=sum(r['token_capped'] for r in current),
                             capped_percent=100*sum(r['token_capped'] for r in current)/len(data),
                             prompt_min=min(vals),prompt_median=statistics.median(vals),prompt_max=max(vals),
                             min_headroom_after_512=7680-max(vals),empty=sum(r['empty_output'] for r in current)))
    assert len(runs)==162 and len(items)==20142
    write('per_output_metadata.csv',items);write('per_run_summary.csv',runs)
    totals=[]
    for model in ['llama','mixtral']:
        for dataset in ['all',*DATASETS]:
            rr=[r for r in runs if r['model']==model and (dataset=='all' or r['dataset']==dataset)]
            n=sum(r['n'] for r in rr); c=sum(r['capped'] for r in rr)
            totals.append(dict(model=model,dataset=dataset,runs=len(rr),n=n,capped=c,percent=100*c/n,
                               prompt_max=max(r['prompt_max'] for r in rr),min_headroom_after_512=min(r['min_headroom_after_512'] for r in rr)))
    write('totals.csv',totals)
    # Reproduce old published counts as a check on the metadata definition.
    old={m:sum(r['capped'] for r in runs if r['model']==m and r['strategy']!='few_retrieval' and r['selection_seed'] not in [44,46]) for m in ['llama','mixtral']}
    assert old=={'llama':17,'mixtral':107},old
    delivery=HERE/'delivery';delivery.mkdir(exist_ok=True)
    tables=[]
    for model in ['llama','mixtral']:
        title='Llama~3.1~8B' if model=='llama' else 'Mixtral~8x7B'
        lines=[r'{\small',r'\begin{longtable}{lllrr}',
               r'\caption{\rev{Outputs reaching the 512-token generation limit for '+title+r'. Random conditions are reported separately for each demonstration-selection seed. Only rows with at least one capped output are shown.}}',
               r'\label{tab:supp_truncation_'+model+r'_nonzero}\\',r'\toprule',
               r'Dataset & Prompt & Strategy & Seed & Capped / outputs \\',r'\midrule',r'\endfirsthead',
               r'\toprule',r'Dataset & Prompt & Strategy & Seed & Capped / outputs \\',r'\midrule',r'\endhead']
        for r in runs:
            if r['model']==model and r['capped']:
                lines.append(' & '.join([LABEL[r['dataset']],LABEL[r['prompt']],LABEL[r['strategy']],str(r['selection_seed']) if r['selection_seed']!='fixed' else '--',f"{r['capped']}/{r['n']}"])+r' \\')
        t=next(t for t in totals if t['model']==model and t['dataset']=='all')
        lines += [r'\midrule',f"Total & -- & -- & -- & {t['capped']}/{t['n']}"+r' \\',r'\bottomrule',r'\end{longtable}',r'}']
        tables.append('\n'.join(lines))
    intro=r'''\section{Truncation Analysis}
\label{supp:truncation}

\rev{We count an output as token-capped when the execution metadata report \texttt{done\_reason=length}. This definition distinguishes reaching the 512-token generation limit from abrupt endings reported as \texttt{stop}; it does not classify linguistic completeness. The analysis covers all 162 configurations in the main study: zero-shot, metric-based few-shot, and retrieval-based few-shot once per dataset--model--prompt combination, and one-shot and random few-shot with demonstration-selection seeds 42, 44, and 46. There are 20,142 recorded outputs, or 10,071 per model. Ablation runs and the diagnostic without repetition penalty are excluded from these totals.}

\rev{To select the generation limit, we previously evaluated a 256-token limit with Llama on Cochrane, the dataset with the longest source texts. In that preliminary evaluation, 16.60\% of outputs reached the limit. We therefore used 512 tokens for the main study. The counts below describe the completed main-study runs at that limit.}

\rev{Tables}~\ref{tab:supp_truncation_llama_nonzero} \rev{and}~\ref{tab:supp_truncation_mixtral_nonzero} \rev{show each configuration and selection with at least one token-capped output. All omitted configurations and selections have zero capped outputs. Fixed conditions are counted once. Overall percentages describe the recorded runs, whose repeated random conditions contribute more outputs; they are not estimates over independent source texts or equally weighted prompting strategies.}
'''
    summary=[]
    for m in ['llama','mixtral']:
        rs=[r for r in totals if r['model']==m];allr=rs[0]
        detail=', '.join(f"{LABEL[t['dataset']]}: {t['capped']}/{t['n']} ({t['percent']:.2f}\\%)" for t in rs[1:])
        summary.append(r'\rev{'+f"For {'Llama' if m=='llama' else 'Mixtral'}, {allr['capped']} of {allr['n']:,} outputs reached the generation limit ({allr['percent']:.2f}\\%). The dataset-specific counts are {detail}."+'}')
    ret={m:sum(r['capped'] for r in runs if r['model']==m and r['strategy']=='few_retrieval') for m in ['llama','mixtral']}
    summary.append(r'\rev{Retrieval-based few-shot prompting accounts for '+str(ret['llama'])+' token-capped outputs for Llama and '+str(ret['mixtral'])+r' for Mixtral, out of 1,119 outputs per model. The Cochrane Mixtral ISO+examples zero-shot configuration remains at 29/125 (23.2\%). All outputs, including capped and empty responses, remain in the evaluation.}')
    trunc=intro+'\n\n'.join(tables+summary)+'\n'
    (delivery/'truncation_replacement.tex').write_text(trunc,encoding='utf-8')
    focus=[r for r in runs if r['dataset']=='cochrane' and r['prompt']=='iso_examples']
    write('cochrane_iso_examples_lengths.csv',focus)
    lengths=r'''\subsection{Observed processed-input lengths}
\label{supp:observed_prompt_lengths}

\rev{We audit Ollama's processed-input token count (\texttt{prompt\_eval\_count}) for all 20,142 outputs from the 162 main-study configurations. These counts measure the input processed by the runtime, including prompt instructions and demonstrations. Historical runtime counts alone cannot exclude truncation before processing. For retrieval-based prompts, we additionally verify that every runtime count matches the saved pre-generation count from native tokenization of the complete prompt. All retrieval inputs meet the 7,616-token input budget, which reserves 512 output tokens and a 64-token safety margin.}

'''
    mx=max(r['prompt_eval_count'] for r in items);over=sum(r['headroom_after_512']<0 for r in items)
    lengths+=r'\rev{Across the complete audit, the maximum processed-input count is '+str(mx)+f' tokens; {over} inputs exceed the 8,192-token context after reserving 512 tokens for generation.'+'}\n\n'
    lengths+=r'''\rev{The table below reports Cochrane ISO+examples input lengths for all five strategies, separating the three selections for one-shot and random few-shot. For Mixtral zero-shot, the maximum is 4,950 tokens, including among the 29 token-capped outputs. Adding the 512-token output allowance gives 5,462 tokens, leaving 2,730 tokens within the configured context. These runtime counts show no context-budget excess for that configuration; the observed outputs reached the generation limit.}

\begin{table}[htbp]
\centering
\small
\caption{\rev{Processed-input token counts for Cochrane ISO+examples ($n=125$ per row). Headroom is 8,192 minus the maximum observed input count minus 512. Seeds identify demonstration selection, not the decoding seed.}}
\label{tab:supp_observed_prompt_lengths}
\begin{tabular}{lllrrrr}
\toprule
Model & Strategy & Seed & Min & Median & Max & Headroom \\
\midrule
'''
    for r in focus:
        lengths+=' & '.join(['Llama' if r['model']=='llama' else 'Mixtral',LABEL[r['strategy']],str(r['selection_seed']) if r['selection_seed']!='fixed' else '--',str(r['prompt_min']),f"{r['prompt_median']:g}",str(r['prompt_max']),str(r['min_headroom_after_512'])])+r' \\'+'\n'
    lengths+=r'\bottomrule'+'\n'+r'\end{tabular}'+'\n'+r'\end{table}'+'\n'
    (delivery/'prompt_lengths_replacement.tex').write_text(lengths,encoding='utf-8')
    source=Path(r'C:\Users\isegu\Downloads\supplementary_material (4).tex')
    text=source.read_text(encoding='utf-8-sig'); hashes[str(source)]=sha(source)
    start=text.index(r'\section{Truncation Analysis}')
    diagnostic=text.index(r'\subsection{Focused diagnostic rerun without repetition penalization}',start)
    # Preserve the collaborator's diagnostic exactly; replace the two audits only.
    oldlength=text.index(r'\subsection{Observed processed-input lengths}',diagnostic)
    comment=text.rfind('\n',diagnostic,oldlength)
    end=text.index(r'\section{Qualitative Error-Analysis Evidence}',oldlength)
    revised=text[:start]+trunc+'\n'+text[diagnostic:oldlength]+lengths+'\n'+text[end:]
    (delivery/'supplementary_material_updated.tex').write_text(revised,encoding='utf-8')
    proof=dict(configurations=len(runs),outputs=len(items),old_counts_reproduced=old,retrieval_counts_match_preflight=True,
               input_excess_count=over,max_observed_input=mx,input_sha256=hashes,totals=totals)
    (HERE/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
    (HERE/'REPORT.md').write_text('# Auditoría de truncamiento y longitudes actualizada\n\n162 configuraciones; 20.142 salidas. Sin nuevas generaciones.\n\n'+json.dumps(totals,indent=2)+'\n\nLos totales son descriptivos de ejecuciones guardadas, no tasas independientes por texto. Los diagnósticos de penalización y ablación quedan separados.\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in proof.items() if k!='input_sha256'},indent=2))

if __name__=='__main__': main()
