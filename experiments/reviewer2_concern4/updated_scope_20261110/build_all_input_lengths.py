"""Summarize all input lengths, pooling the three random selections per cell."""
from pathlib import Path
import csv
import itertools
import statistics

HERE=Path(__file__).resolve().parent
LABEL={'cochrane':'Cochrane','plaba':'PLABA','tsar2025':'TSAR~2025',
       'llama':'Llama','mixtral':'Mixtral','minimal':'Baseline','iso':'ISO',
       'iso_examples':'ISO+examples','zero':'zero','one':'one',
       'few_random':'few-random','few_metric':'few-metric','few_retrieval':'few-retrieval'}

def main():
    with (HERE/'per_output_metadata.csv').open(encoding='utf-8',newline='') as f:
        items=list(csv.DictReader(f))
    summary=[]
    for dataset,model,prompt,strategy in itertools.product(
            ['cochrane','plaba','tsar2025'],['llama','mixtral'],
            ['minimal','iso','iso_examples'],['zero','one','few_random','few_metric','few_retrieval']):
        group=[r for r in items if (r['dataset'],r['model'],r['prompt'],r['strategy'])==(dataset,model,prompt,strategy)]
        values=[int(r['prompt_eval_count']) for r in group]
        seeds=set(r['selection_seed'] for r in group)
        assert seeds==({'42','44','46'} if strategy in ['one','few_random'] else {'fixed'})
        expected={'cochrane':125,'plaba':148,'tsar2025':100}[dataset]*(3 if strategy in ['one','few_random'] else 1)
        assert len(values)==expected
        summary.append(dict(dataset=dataset,model=model,prompt=prompt,strategy=strategy,
                            n=len(values),minimum=min(values),median=statistics.median(values),
                            maximum=max(values),headroom=8192-512-max(values)))
    assert len(summary)==90 and sum(r['n'] for r in summary)==20142
    assert max(r['maximum'] for r in summary)==7615 and min(r['headroom'] for r in summary)==65
    with (HERE/'all_input_lengths_90.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    text=r'''\section[Input Length Analysis]{\rev{Input Length Analysis}}
\label{supp:observed_prompt_lengths}

\rev{We examine input lengths to assess whether the prompts fit within the 8,192-token context window while reserving 512 tokens for generation. We use the input-token counts reported by Ollama for all 162 configurations.}

\rev{Table}~\ref{tab:supp_observed_prompt_lengths} \rev{reports the minimum, median, and maximum input lengths for each combination of dataset, model, prompt type, and prompting strategy. For one-shot and random few-shot, these statistics are calculated over the inputs from all three demonstration-selection seeds (42, 44, and 46) together. This gives 90 rows summarizing the 162 configurations. The remaining context space is calculated by subtracting the maximum input length and the 512-token output allowance from 8,192.}

{\scriptsize
\setlength{\tabcolsep}{3pt}
\begin{longtable}{lllrrrrr}
\caption{\rev{Input lengths in tokens for all evaluated configurations. Each dataset block contains both models; prompt type and strategy are listed in separate columns. The number of inputs ($n$) includes all three seeds for one-shot and random few-shot. Headroom is the context space remaining after the maximum observed input length and the 512-token output allowance.}}\label{tab:supp_observed_prompt_lengths}\\
\toprule
Model & Prompt & Strategy & $n$ & Min & Median & Max & Headroom \\
\midrule
\endfirsthead
\toprule
Model & Prompt & Strategy & $n$ & Min & Median & Max & Headroom \\
\midrule
\endhead
\midrule
\multicolumn{8}{r}{Continued on next page}\\
\endfoot
\bottomrule
\endlastfoot
'''
    previous=None
    for r in summary:
        if r['dataset']!=previous:
            if previous is not None:text+=r'\midrule'+'\n'
            text+=r'\multicolumn{8}{l}{\textbf{'+LABEL[r['dataset']]+r'}}\\'+'\n'
            previous=r['dataset']
        vals=[LABEL[r['model']],LABEL[r['prompt']],LABEL[r['strategy']],str(r['n']),
              str(r['minimum']),f"{r['median']:g}",str(r['maximum']),str(r['headroom'])]
        text+=' & '.join(r'\rev{'+v+'}' for v in vals)+r' \\'+'\n'
    text+=r'''\end{longtable}
}

\rev{All inputs fit within this budget according to the token counts reported by Ollama. The maximum input length was 6,559 tokens for Llama and 7,615 for Mixtral, leaving at least 1,121 and 65 tokens, respectively, after reserving 512 tokens for generation. These counts alone cannot rule out input truncation before processing. For retrieval-based prompts, all reported input-token counts matched the saved counts obtained by native tokenization of the complete prompts before generation.}

\rev{For Mixtral with ISO+examples zero-shot on Cochrane, where 29 of 125 outputs reached the generation limit, the maximum input length was 4,950 tokens. This leaves 2,730 tokens within the context window after reserving 512 tokens for generation. The recorded counts therefore show no context-budget excess for this configuration.}
'''
    (HERE/'delivery/input_length_analysis_all_configurations.tex').write_text(text,encoding='utf-8')
    print('Verified 90 rows, 162 configurations, 20,142 inputs; pooled medians calculated from all individual input counts.')

if __name__=='__main__':main()
