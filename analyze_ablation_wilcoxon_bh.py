"""Wilcoxon + BH main analysis; retain earlier randomization/Holm as sensitivity.

Family definitions are fixed here before running: primary 12, secondary 12.
BH across all 24 is reported as an additional sensitivity, not selected per result.
No inference, metric evaluation, bootstrap or supplied manuscript is modified.
"""
from pathlib import Path
import json
import hashlib
import time
import numpy as np
import pandas as pd
import scipy
from scipy.stats import wilcoxon, false_discovery_control, rankdata

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'experiments/focused_ablation'
DEST=BASE/'combined/wilcoxon_bh'


def main():
    DEST.mkdir(exist_ok=True)
    if (DEST/'all_24_comparisons.csv').exists():
        raise FileExistsError('Analysis already exists; refusing overwrite')
    primary=pd.read_csv(BASE/'combined/sari_comparisons.csv')
    secondary=pd.read_csv(BASE/'combined/baseline_comparisons/sari_vs_baseline.csv')
    result=[];hashes={}
    for name,frame in (('primary',primary),('secondary',secondary)):
        for r in frame.to_dict('records'):
            d,p=r['dataset'],r['prompt']
            llama=r['model'].startswith('Llama')
            folder=BASE if llama else BASE/'mixtral'
            original_folder='llama_512' if llama else 'mixtral_512'
            short='llama3_1_8b' if llama else 'mixtral_latest'
            path=(folder/'statistics'/f'{d}_{p}_paired_items.csv' if name=='primary' else
                  BASE/'combined/baseline_comparisons'/f'{short}_{d}_{p}_paired_items.csv')
            pairs=pd.read_csv(path,keep_default_na=False)
            comparator='original' if name=='primary' else 'baseline'
            reference_prompt=p if name=='primary' else 'minimal'
            saved_path=ROOT/'outputs'/original_folder/f'predictions_{short}_{d}_{reference_prompt}_zero.csv'
            saved=pd.read_csv(saved_path,keep_default_na=False)
            assert pairs.text_id.astype(str).tolist()==saved.text_id.astype(str).tolist()
            assert pairs.source.tolist()==saved.original.tolist()
            assert pairs[comparator+'_output'].tolist()==saved.prediction.tolist()
            a=pd.to_numeric(pairs.ablated_SARI).to_numpy()
            b=pd.to_numeric(pairs[comparator+'_SARI']).to_numpy()
            assert np.array_equal(np.round(b,2),pd.to_numeric(saved.SARI).to_numpy())
            # Match the two-decimal instance-score convention in saved originals.
            # Integer centipoints avoid floating-point noise in ties and zero differences.
            differences=np.rint(100*(np.round(a,2)-np.round(b,2))).astype(np.int64)
            n=len(differences);nonzero=differences[differences!=0]
            if len(nonzero):
                test=wilcoxon(differences,zero_method='wilcox',correction=False,
                              alternative='two-sided',method='auto',nan_policy='raise')
                statistic,pvalue=float(test.statistic),float(test.pvalue)
                ranks=rankdata(np.abs(nonzero),method='average')
                signed_rank_effect=float((ranks[nonzero>0].sum()-ranks[nonzero<0].sum())/ranks.sum())
            else:statistic,pvalue,signed_rank_effect=0.,1.,0.
            # Report the existing raw corpus mean difference and bootstrap CI unchanged.
            assert np.isclose((a-b).mean(),r['delta_SARI'],atol=1e-10)
            record={'family':name,'comparison':'ablated_minus_'+comparator,'model':r['model'],
                'dataset':d,'prompt':p,'n':n,'comparator_SARI':r['original_SARI'] if name=='primary' else r['baseline_SARI'],
                'ablated_SARI':r['ablated_SARI'],'delta_SARI':r['delta_SARI'],
                'ci95_low':r['ci95_low'],'ci95_high':r['ci95_high'],
                'W':statistic,'p_wilcoxon':pvalue,'nonzero_pairs':len(nonzero),
                'positive_pairs':int((differences>0).sum()),'negative_pairs':int((differences<0).sum()),
                'zero_pairs':int((differences==0).sum()),'median_item_difference':float(np.median(differences)/100),
                'rank_biserial':signed_rank_effect,'p_permutation':r['p_two_sided'],
                'p_holm_family12':r['p_holm_all_12'] if name=='primary' else r['p_holm_secondary_12']}
            result.append(record)
            hashes[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    combined=pd.DataFrame(result)
    combined['q_bh_family12']=np.nan
    for family in ('primary','secondary'):
        mask=combined.family==family
        assert mask.sum()==12
        combined.loc[mask,'q_bh_family12']=false_discovery_control(combined.loc[mask,'p_wilcoxon'].to_numpy(),method='bh')
    combined['q_bh_all24']=false_discovery_control(combined.p_wilcoxon.to_numpy(),method='bh')
    old=pd.read_csv(BASE/'combined/baseline_comparisons/all_24_comparisons.csv')
    combined['p_holm_all24']=old.p_holm_all_24.to_numpy()
    combined['significant_bh_family12']=combined.q_bh_family12<.05
    combined['significant_bh_all24']=combined.q_bh_all24<.05
    combined['significant_permutation_holm12']=combined.p_holm_family12<.05
    combined.to_csv(DEST/'all_24_comparisons.csv',index=False)
    combined[combined.family=='primary'].to_csv(DEST/'primary_sari.csv',index=False)
    combined[combined.family=='secondary'].to_csv(DEST/'secondary_vs_baseline.csv',index=False)
    method={'main_test':'two-sided scipy.stats.wilcoxon','scipy_version':scipy.__version__,
        'zero_method':'wilcox; zero differences omitted from ranks','continuity_correction':False,
        'method':'auto; SciPy selects appropriate exact/asymptotic handling; rank ties averaged',
        'all_zero_case':'W=0,p=1,rank_biserial=0',
        'test_precision':'two-decimal per-item standard SARI, matching saved original item columns; scaled to integer centipoints to prevent artificial ties/zero differences from floating point',
        'effect_and_CI':'raw corpus SARI delta and existing 10000 paired bootstrap CI, unchanged',
        'families_fixed_before_run':'12 primary ablated-original; 12 secondary ablated-baseline, BH independently; all-24 BH additionally reported',
        'threshold':.05,'BH_implementation':'scipy.stats.false_discovery_control(method=bh)',
        'robustness':'previous two-sided randomization and Holm retained unchanged, not selected as an alternative main test per comparison',
        'original_protocol_limit':'supplied manuscript specifies Wilcoxon+BH but original test code/defaults/family scope were not present; same method family, exact settings documented here rather than claiming bit-for-bit original statistical implementation',
        'limitations':'signed-rank inference concerns paired item differences under its usual assumptions, not the same null as the mean-difference permutation test; fixed runs/test rows; possible within-document PLABA dependence not modeled; no equivalence claim',
        'source_hashes':hashes,'complete':True}
    (DEST/'methodology.json').write_text(json.dumps(method,indent=2),encoding='utf-8')
    print(combined[['family','model','dataset','prompt','delta_SARI','p_wilcoxon','q_bh_family12','q_bh_all24','p_holm_family12']].to_string(index=False))


if __name__=='__main__':main()
