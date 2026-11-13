"""Generate integration tables from completed evaluations; no model or manuscript edits."""
import hashlib
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
DEST = HERE / 'manuscript_proposals'
ROOT = HERE.parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, text):
    path = DEST/name
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text.rstrip()+'\n',encoding='utf-8')


def longtable(caption,label,headers,rows):
    n=len(headers)
    header=' & '.join(headers)+r' \\'+'\n'
    return ('\\begingroup\n\\scriptsize\n\\setlength{\\tabcolsep}{3pt}\n'
        +'\\begin{longtable}{@{}l'+'r'*(n-1)+'@{}}\n'
        +'\\caption{'+caption+'}\\label{'+label+r'}\\'+'\n'
        +'\\toprule\n'+header+'\\midrule\n\\endfirsthead\n'
        +'\\multicolumn{'+str(n)+r'}{l}{\textit{Continued from previous page}}\\'+'\n'
        +'\\toprule\n'+header+'\\midrule\n\\endhead\n'
        +'\\midrule\n\\multicolumn{'+str(n)+r'}{r}{\textit{Continued on next page}}\\'+'\n'
        +'\\endfoot\n\\bottomrule\n\\endlastfoot\n'+'\n'.join(rows)
        +'\n\\end{longtable}\n\\endgroup\n')


def config(row):
    return {'minimal':'B','iso':'I','iso_examples':'E'}[row['prompt']]+'-'+{'one':'O','few_random':'R'}[row['strategy']]


def pformat(value):
    return '$<0.0001$' if value<.0001 else f'{value:.4f}'


def main():
    metric_path=HERE/'evaluation/metrics/summaries/all_models_all_datasets_mean_sd.csv'
    descriptor_path=HERE/'evaluation/descriptors/summaries/all_models_all_datasets_mean_sd.csv'
    primary_path=HERE/'statistics_results/joint_sari/primary_sari.csv'
    secondary_path=HERE/'statistics_results/joint_sari/secondary_sari.csv'
    inputs=[metric_path,descriptor_path,primary_path,secondary_path]
    before={p.relative_to(ROOT).as_posix():sha(p) for p in inputs}
    metrics=pd.read_csv(metric_path);desc=pd.read_csv(descriptor_path)
    primary=pd.read_csv(primary_path);secondary=pd.read_csv(secondary_path)
    assert len(metrics)==216 and len(desc)==180 and len(primary)==7 and len(secondary)==36
    for frame in [metrics,desc]:
        assert set(frame.n_seeds)=={3}
        values=frame[['seed_42','seed_44','seed_46']]
        assert (abs(values.mean(axis=1)-frame['mean'])<1e-10).all()
        assert (abs(values.std(axis=1,ddof=1)-frame.sd)<1e-10).all()
    labels={'iso_minus_baseline':'ISO $-$ baseline','iso_examples_minus_baseline':'ISO+examples $-$ baseline',
       'iso_examples_minus_iso':'ISO+examples $-$ ISO','one_minus_zero':'One $-$ zero',
       'few_random_minus_one':'Few-random $-$ one','few_metric_minus_few_random':'Few-metric $-$ few-random',
       'mixtral_minus_llama':'Mixtral $-$ Llama'}
    body=[]
    for _,r in primary.iterrows():
        body.append(' & '.join([labels[r.contrast_id],f'{r.effect:+.3f}',
           f'[{r.bootstrap_ci_low:+.3f}, {r.bootstrap_ci_high:+.3f}]',pformat(r.q_bh)])+r' \\')
    write('paper/03_primary_sari_table.tex',
        '\\begin{table*}[t]\n\\centering\n\\small\n'
        +'\\caption{Joint SARI contrasts with balanced marginal weights. Positive effects favor the first condition. Bootstrap intervals are pointwise; BH-adjusted $q$ values refer to the seven grouped-model tests.}\n'
        +'\\label{tab:joint_sari_primary}\n\\begin{tabular}{lrrr}\n\\hline\n'
        +r'Contrast & $\Delta$ SARI & 95\% bootstrap CI & $q$ (BH)' +r' \\'+'\n\\hline\n'
        +'\n'.join(body)+'\n\\hline\n\\end{tabular}\n\\end{table*}')
    for dataset,title in [('cochrane','Cochrane'),('plaba','PLABA'),('tsar2025','TSAR 2025')]:
        rows=[]
        for model in ['llama','mixtral']:
            rows.append(r'\multicolumn{7}{l}{\textbf{'+('Llama 3.1 8B' if model=='llama' else 'Mixtral 8x7B')+r'}}\\')
            for prompt in ['minimal','iso','iso_examples']:
                for setting in ['one','few_random']:
                    subset=metrics[(metrics.dataset==dataset)&(metrics.model==model)&(metrics.prompt==prompt)&(metrics.strategy==setting)]
                    assert len(subset)==6
                    vals=[]
                    for metric in ['SARI','BLEU','BERTScore-F1','MeaningBERT','FKGL','FRE']:
                        r=subset[subset.metric==metric].iloc[0];scale=100 if metric=='BERTScore-F1' else 1
                        vals.append(f'${r["mean"]*scale:.2f} \\pm {r.sd*scale:.2f}$')
                    rows.append(' & '.join([config({'prompt':prompt,'strategy':setting})]+vals)+r' \\')
        write('supplement/01_metrics_'+dataset+'.tex',longtable(
            title+': mean $\\pm$ sample SD across demonstration selections 42, 44 and 46. BERT-F1 mean and SD are scaled by 100; other metrics retain their evaluation scales.',
            'supp:selection_metrics_'+dataset,['Config.','SARI','BLEU','BERT-F1','MeaningBERT','FKGL','FRE'],rows))
    sari=metrics[metrics.metric=='SARI']
    rows=[]
    for model in ['llama','mixtral']:
        for dataset in ['cochrane','plaba','tsar2025']:
            title=('Llama 3.1 8B' if model=='llama' else 'Mixtral 8x7B')+' / '+dataset.replace('tsar2025','TSAR 2025').title()
            rows.append(r'\multicolumn{6}{l}{\textbf{'+title+r'}}\\')
            for prompt in ['minimal','iso','iso_examples']:
                for setting in ['one','few_random']:
                    r=sari[(sari.model==model)&(sari.dataset==dataset)&(sari.prompt==prompt)&(sari.strategy==setting)].iloc[0]
                    rows.append(' & '.join([config(r)]+[f'{r[k]:.3f}' for k in ['seed_42','seed_44','seed_46','mean','sd']])+r' \\')
    write('supplement/02_individual_sari_selections.tex',longtable('Individual SARI values and their three-selection mean and sample SD. These are not test-item confidence intervals.',
        'supp:individual_selection_sari',['Config.','42','44','46','Mean','SD'],rows))
    rows=[]
    for model in ['llama','mixtral']:
        for dataset in ['cochrane','plaba','tsar2025']:
            title=('Llama 3.1 8B' if model=='llama' else 'Mixtral 8x7B')+' / '+dataset
            rows.append(r'\multicolumn{5}{l}{\textbf{'+title+r'}}\\')
            for prompt in ['minimal','iso','iso_examples']:
                for setting in ['one','few_random']:
                    subset=desc[(desc.model==model)&(desc.dataset==dataset)&(desc.prompt==prompt)&(desc.strategy==setting)]
                    assert len(subset)==5
                    vals=[]
                    for measure in ['mean_LEN_PRED','mean_compression_ratio','mean_copy_rate']:
                        r=subset[subset.measure==measure].iloc[0];prec=2 if measure=='mean_LEN_PRED' else 3
                        vals.append(f'${r["mean"]:.{prec}f} \\pm {r.sd:.{prec}f}$')
                    rows.append(' & '.join([config({'prompt':prompt,'strategy':setting}),str(int(subset.n_test.iloc[0]))]+vals)+r' \\')
    write('supplement/03_three_selection_descriptors.tex',longtable('Output descriptors: mean $\\pm$ sample SD across selections 42, 44 and 46. Ratio and Copy are fractions; $N$ is the test-row count for each selection.',
        'supp:selection_descriptors',['Config.','$N$','Words','Ratio','Copy'],rows))
    rows=[]
    for model in ['llama','mixtral']:
        for dataset in ['cochrane','plaba','tsar2025']:
            rows.append(r'\multicolumn{6}{l}{\textbf{'+model+' / '+dataset+r'}}\\')
            for contrast in list(labels)[:6]:
                r=secondary[secondary.contrast_id==f'{contrast}/{model}/{dataset}'].iloc[0]
                rows.append(' & '.join([labels[contrast],f'{r.effect:+.3f}',f'{r.standard_error:.3f}',
                    pformat(r.p),pformat(r.q_bh),f'[{r.bootstrap_ci_low:+.3f}, {r.bootstrap_ci_high:+.3f}]'])+r' \\')
    write('supplement/04_secondary_sari_contrasts.tex',longtable('Joint SARI contrasts by model/dataset. BH uses a single family of 36 tests; bootstrap intervals are pointwise and not BH-adjusted.',
         'supp:joint_sari_secondary',['Contrast','$\\Delta$','SE','$p$','$q$ (BH)','95\\% bootstrap CI'],rows))
    for p in DEST.rglob('*.tex'):
        text=p.read_text(encoding='utf-8');assert text.count('{')==text.count('}'),p
    assert before=={p.relative_to(ROOT).as_posix():sha(p) for p in inputs}
    write('table_generation_verification.json',json.dumps(dict(inputs_sha256=before,inputs_unchanged=True,
         metric_conditions=36,metrics_per_condition=6,individual_sari_rows=36,descriptor_conditions=36,
         primary_contrasts=7,secondary_contrasts=36,sd_ddof=1,original_tex_edited=False,
         model_calls=0),indent=2))
    print('Prepared primary table, three metric tables, individual SARI, descriptors and secondary contrasts.')


if __name__=='__main__':
    main()
