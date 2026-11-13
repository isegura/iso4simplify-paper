"""Plot existing local SARI contrasts, without refitting or recalculating tests."""
from pathlib import Path
import csv, hashlib, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'experiments/joint_analysis_all_pairs/results/local_sari.csv'
PROOF=ROOT/'experiments/joint_analysis_all_pairs/results/complete.json'
OUT=HERE/'output/pdf'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    proof=json.loads(PROOF.read_text())
    assert sha(SOURCE)==proof['output_hashes'][SOURCE.relative_to(ROOT).as_posix()]
    with SOURCE.open(encoding='utf-8-sig',newline='') as f: allrows=list(csv.DictReader(f))
    rows=[r for r in allrows if r['contrast_id'].split('/')[0] in ['iso_minus_baseline','iso_examples_minus_baseline']]
    assert len(rows)==12 and all(r['family']=='local_78' for r in rows)
    for r in rows:
        assert float(r['bootstrap_ci_low'])<=float(r['effect'])<=float(r['bootstrap_ci_high'])
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'sari_differences_data.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,
                         'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8.5,
                         'pdf.fonttype':42,'ps.fonttype':42,'axes.linewidth':0.65})
    fig,axs=plt.subplots(3,2,figsize=(8.0,5.8),sharex=True)
    fig.subplots_adjust(left=.14,right=.89,top=.91,bottom=.13,wspace=.86,hspace=.66)
    lookup={r['contrast_id']:r for r in rows}
    dataset_names={'cochrane':'Cochrane','plaba':'PLABA','tsar2025':'TSAR 2025'}
    colors=['#17618A','#B74B13']
    for ri,dataset in enumerate(['cochrane','plaba','tsar2025']):
        for ci,model in enumerate(['llama','mixtral']):
            ax=axs[ri,ci]
            name='Llama 3.1 8B' if model=='llama' else 'Mixtral 8x7B'
            ax.set_title(f"({chr(97+ri*2+ci)}) {name} / {dataset_names[dataset]}",loc='left',pad=16,fontweight='medium')
            ax.axvline(0,color='#515151',lw=.9,ls=(0,(3,3)),zorder=1)
            ax.set_xlim(-2.7,3.7);ax.set_ylim(-.6,1.6)
            ax.set_yticks([1,0],labels=['ISO','ISO+examples'])
            ax.xaxis.set_major_locator(MultipleLocator(1))
            ax.grid(axis='x',color='#E7E7E7',lw=.6,zorder=0)
            ax.set_axisbelow(True)
            for spine in ['top','right','left']:ax.spines[spine].set_visible(False)
            ax.tick_params(axis='y',length=0,pad=7)
            ax.tick_params(axis='x',length=3,labelbottom=True)
            ax.text(1.045,1.095,'Adjusted q',transform=ax.transAxes,fontsize=8,color='#444444',ha='left')
            for j,contrast in enumerate(['iso_minus_baseline','iso_examples_minus_baseline']):
                r=lookup[f'{contrast}/{model}/{dataset}'];y=1-j
                effect=float(r['effect']);low=float(r['bootstrap_ci_low']);high=float(r['bootstrap_ci_high'])
                ax.errorbar(effect,y,xerr=[[effect-low],[high-effect]],fmt=['o','s'][j],
                            color=colors[j],ecolor=colors[j],markersize=5.1,elinewidth=1.3,
                            capsize=3,capthick=1.1,zorder=3)
                q=float(r['q_bh']);label='<0.001' if q<.001 else f'{q:.3f}'
                ax.text(1.045,y,label,transform=ax.get_yaxis_transform(),va='center',ha='left',fontsize=8.5)
    fig.supxlabel('SARI difference from Baseline (points)',x=.515,y=.055,fontsize=10)
    fig.savefig(OUT/'sari_differences_from_baseline.pdf',bbox_inches='tight',pad_inches=.12,
                metadata={'Title':'SARI differences from Baseline by model and dataset',
                          'Subject':'Equal-strategy marginal contrasts; pointwise 95% source-group bootstrap intervals; q adjusted over 78 local contrasts'})
    fig.savefig(OUT/'sari_differences_from_baseline.png',dpi=220,bbox_inches='tight',pad_inches=.12)
    plt.close(fig)
    latex=r'''% Upload sari_differences_from_baseline.pdf to the Overleaf project.
% Insert in Results, within Joint Analysis of Prompting Strategies.
\begin{figure*}[t]
\centering
\includegraphics[width=\textwidth]{sari_differences_from_baseline.pdf}
\caption{\rev{SARI differences between ISO-based prompts and Baseline within each model--dataset combination, averaged equally over the five prompting strategies. For one-shot and random few-shot, the three demonstration selections are averaged first. Points show estimated differences; bars show pointwise 95\% confidence intervals from 10,000 source-group bootstrap resamples within each dataset. Positive values favor the ISO-based prompt. Adjusted $q$ values use Benjamini--Hochberg correction across all 78 model--dataset contrasts. The intervals are not adjusted for multiple comparisons; significance is determined by $q<0.05$.}}
\label{fig:sari_differences_baseline}
\end{figure*}

\rev{Figure}~\ref{fig:sari_differences_baseline} \rev{shows the SARI differences between ISO-based prompts and Baseline for each model and dataset. Full results for all six automatic metrics are reported in Supplementary Tables~S1--S6.}
'''
    (OUT/'figure_insertion.tex').write_text(latex,encoding='utf-8')
    verify=dict(source=str(SOURCE.relative_to(ROOT)),source_sha256=sha(SOURCE),contrasts=12,
                inference_calls=0,new_statistical_tests=0,intervals='bootstrap_ci_low/high, pointwise 95%',
                adjustment='q_bh from the full local_78 family; not recalculated for the 12 plotted contrasts',
                max_absolute_rounding_error=0,source_unchanged=sha(SOURCE)==proof['output_hashes'][SOURCE.relative_to(ROOT).as_posix()])
    (OUT/'verification.json').write_text(json.dumps(verify,indent=2),encoding='utf-8')
    print(json.dumps(verify,indent=2))

if __name__=='__main__':main()
