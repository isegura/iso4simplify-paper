"""Extend unchanged screening rules to the complete 162-configuration study."""
from pathlib import Path
import csv, hashlib, itertools, json, statistics, sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(HERE.parent))
from detectors import extra_flags
from generate_systematic_error_analysis_512 import classify_row

FLAGS=['empty_prediction','reached_generation_limit','ended_abruptly',
       'stop_no_terminal_punctuation_candidate','endpoint_screen_union','preamble_candidate',
       'list_markers_present','two_or_more_list_markers','acronym_without_detected_expansion_candidate',
       'new_acronym_without_detected_expansion_candidate','source_copied_verbatim']
DISPLAY=[('preamble_candidate','Preamble'),('list_markers_present','Lists'),
         ('acronym_without_detected_expansion_candidate','Acronyms'),('endpoint_screen_union','Endings')]
LABEL={'llama':'Llama~3.1~8B','mixtral':'Mixtral~8x7B','cochrane':'Cochrane','plaba':'PLABA','tsar2025':'TSAR~2025',
       'minimal':'Baseline','iso':'ISO','iso_examples':'ISO+examples','zero':'zero','one':'one',
       'few_random':'few-random','few_metric':'few-metric','few_retrieval':'few-retrieval'}

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,r):
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(r[0]));w.writeheader();w.writerows(r)

def main():
    metadata=ROOT/'experiments/reviewer2_concern4/updated_scope_20261110/per_output_metadata.csv'
    descriptors_proof=json.loads((ROOT/'experiments/reviewer2_concern3/integration_20261112/verification.json').read_text())
    hashes={};cache={};items=[]
    for r in read(metadata):
        path=ROOT/r['prediction_path'];rel=path.relative_to(ROOT).as_posix()
        if rel not in cache:
            assert sha(path)==descriptors_proof['source_sha256'][rel]
            hashes[rel]=sha(path);cache[rel]=read(path)
        raw=cache[rel][int(r['row_index'])]
        assert raw['text_id']==r['text_id'] and raw['done_reason']==r['done_reason']
        legacy=classify_row(dict(dataset=r['dataset']),dict(raw,LEN_PRED=len(raw['prediction'].split())))
        extra=extra_flags(raw['original'],raw['prediction'],raw['done_reason'])
        flags={k:int(legacy[k]) for k in ['empty_prediction','reached_generation_limit','ended_abruptly']}
        flags.update({k:int(extra[k]) for k in FLAGS if k in extra})
        flags['endpoint_screen_union']=int(bool(flags['ended_abruptly'] or flags['stop_no_terminal_punctuation_candidate']))
        items.append({k:r[k] for k in ['model','dataset','prompt','strategy','selection_seed','row_index','text_id']}|flags)
    assert len(items)==20142 and len(cache)==162
    # Exact row-level reproduction of every indicator already computed for original runs.
    oldpath=HERE.parent/'screening/all_8952_flags.csv';old=read(oldpath)
    oldmap={(r['model'],r['dataset'],r['prompt'],r['strategy'],r['row_index']):r for r in old}
    checked=0
    for r in items:
        if r['selection_seed'] not in ['44','46'] and r['strategy']!='few_retrieval':
            prior=oldmap[tuple(r[k] for k in ['model','dataset','prompt','strategy','row_index'])]
            assert all(r[k]==int(prior[k]) for k in FLAGS)
            checked+=1
    assert checked==8952
    groups={}
    for r in items:
        key=tuple(r[k] for k in ['model','dataset','prompt','strategy','selection_seed'])
        groups.setdefault(key,[]).append(r)
    runs=[]
    for key,group in groups.items():
        record=dict(zip(['model','dataset','prompt','strategy','selection_seed'],key),n=len(group))
        for f in FLAGS:
            record[f+'_n']=sum(x[f] for x in group)
            record[f+'_pct']=100*record[f+'_n']/len(group)
        runs.append(record)
    assert len(runs)==162
    summary=[]
    for model,dataset,prompt,strategy in itertools.product(['llama','mixtral'],['cochrane','plaba','tsar2025'],
            ['minimal','iso','iso_examples'],['zero','one','few_random','few_metric','few_retrieval']):
        group=[r for r in runs if (r['model'],r['dataset'],r['prompt'],r['strategy'])==(model,dataset,prompt,strategy)]
        assert len(group)==(3 if strategy in ['one','few_random'] else 1)
        record=dict(model=model,dataset=dataset,prompt=prompt,strategy=strategy,selections=len(group))
        for f in FLAGS:
            record[f+'_mean_pct']=statistics.mean(r[f+'_pct'] for r in group)
            record[f+'_seed_sd_pct']=statistics.stdev(r[f+'_pct'] for r in group) if len(group)==3 else ''
        summary.append(record)
    write(HERE/'all_20142_flags.csv',items);write(HERE/'by_configuration_seed_162.csv',runs)
    write(HERE/'by_strategy_mean_sd_90.csv',summary)
    totals=[]
    for m in ['llama','mixtral']:
        group=[r for r in items if r['model']==m]
        row=dict(model=m,n=len(group))
        for f in FLAGS:
            row[f+'_n']=sum(r[f] for r in group);row[f+'_pct']=100*row[f+'_n']/len(group)
        totals.append(row)
    write(HERE/'by_model.csv',totals)
    dest=HERE/'delivery';dest.mkdir(exist_ok=True)
    text=r'''\section[Automatic Output Screening]{\rev{Automatic Output Screening}}
\label{supp:automatic_screening}

\rev{We apply the same automatic rules to all 162 main-study configurations, without selecting outputs by SARI score. The indicators identify possible preambles, list markers, acronyms without a detected parenthetical expansion, and possible incomplete endings before the generation limit. These are screening indicators, not confirmed errors or measures of ISO adherence.}

\rev{Preamble candidates are outputs beginning with expressions such as ``Here is'', ``Here are'', ``Here's'', ``Sure'', or a simplified/rewritten/revised text label. List presence requires at least one line beginning with a bullet or numbered-list marker. Acronym candidates are uppercase tokens of two to eight letters, optionally followed by a plural s, for which no parenthetical expansion with matching initials is detected. The ending screen combines the existing numeric/very-short-ending rule with a check for missing terminal punctuation in nonempty outputs reported as \texttt{done\_reason=stop}. Outputs reaching the generation limit are counted separately in the truncation analysis.}

\rev{Each table entry is the percentage of outputs triggering the indicator. For one-shot and random few-shot, we report the mean and sample standard deviation of percentages across seeds 42, 44, and 46. Indicators overlap and should not be summed into an overall error rate. Lists may be appropriate and are requested by ISO prompts; acronyms can be familiar or explained in forms not recognized by the rules; complete list items and numerical expressions can trigger the ending screen. No precision or recall estimates are available, and the counts should not be interpreted as validated error frequencies.}

'''
    for m,d in itertools.product(['llama','mixtral'],['cochrane','plaba','tsar2025']):
        lines=[r'\begin{table}[htbp]',r'\centering',r'\small',
               r'\caption{\rev{Automatic screening indicators for '+LABEL[m]+' on '+LABEL[d]+r'. Values are percentages, with mean and sample standard deviation across three seeds for random conditions. The indicators are not confirmed error rates.}}',
               r'\label{tab:screening_'+d+'_'+m+'}',r'\begin{tabular}{llrrrr}',r'\toprule',
               r'Prompt & Strategy & Preamble & Lists & Acronyms & Endings \\',r'\midrule']
        for i,r in enumerate(x for x in summary if x['model']==m and x['dataset']==d):
            if i and i%5==0:lines.append(r'\midrule')
            cells=[LABEL[r['prompt']],LABEL[r['strategy']]]
            for f,label in DISPLAY:
                v=f"{r[f+'_mean_pct']:.1f}"
                if r['selections']==3:v+=r' $\pm$ '+f"{r[f+'_seed_sd_pct']:.1f}"
                cells.append(v)
            lines.append(' & '.join(r'\rev{'+x+'}' for x in cells)+r' \\')
        lines.extend([r'\bottomrule',r'\end{tabular}',r'\end{table}'])
        block='\n'.join(lines)+'\n';(dest/f'{d}_{m}.tex').write_text(block,encoding='utf-8');text+='\n'+block
    (dest/'automatic_screening_all.tex').write_text(text,encoding='utf-8')
    for p,h in hashes.items():assert sha(ROOT/p)==h
    proof=dict(configurations=162,outputs=20142,original_rows_reproduced=checked,model_calls=0,
               rules_unchanged=True,source_sha256=hashes,
               detector_sha256=sha(HERE.parent/'detectors.py'),legacy_rule_sha256=sha(ROOT/'generate_systematic_error_analysis_512.py'))
    (HERE/'verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
    print(json.dumps(totals,indent=2))

if __name__=='__main__':main()
