"""Secondary paired SARI contrasts: ablated minus original baseline zero-shot.

No generations or semantic metrics are rerun. Primary ablation contrasts are
preserved; Holm over 12 secondary contrasts is defined before calculation.
"""
from focused_metric_runtime import configure, ROOT, BASE
configure()
from functools import lru_cache
import importlib
import hashlib
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from eval_utils import get_sari_metric
from evaluate_all import load_data_tsar
from run_focused_ablation import EXPECTED, rows, aligned

B, P, SEED = 10000, 19999, 20261022


def holm(values):
    order = np.argsort(values)
    adjusted = np.zeros(len(values))
    previous = 0.
    for rank, index in enumerate(order):
        previous = max(previous, (len(values)-rank)*values[index])
        adjusted[index] = min(1., previous)
    return adjusted


def main():
    started=time.perf_counter()
    dest=BASE/"combined/baseline_comparisons"
    dest.mkdir(exist_ok=True)
    output=dest/"sari_vs_baseline.csv"
    if output.exists():
        raise FileExistsError("Secondary analysis already exists; refusing overwrite")
    metric=get_sari_metric()
    module=importlib.import_module(metric.__class__.__module__)
    raw_kernel=module.SARIsent
    @lru_cache(maxsize=None)
    def kernel(s,p,r):
        return raw_kernel(s,p,r)
    module.normalize=lru_cache(maxsize=None)(module.normalize)
    module.SARIsent=lambda s,p,r: kernel(s,p,tuple(r))
    def corpus(s,p,r):
        return float(metric._compute(sources=s,predictions=p,references=r)["sari"])
    metric_rows=pd.read_csv(BASE/"combined/all_metrics.csv")
    jobs=[(model,folder,orig,short,d,p) for model,folder,orig,short in (
        ("Llama 3.1 8B",BASE,"llama_512","llama3_1_8b"),
        ("Mixtral 8x7B",BASE/"mixtral","mixtral_512","mixtral_latest"))
        for d in EXPECTED for p in ("iso","iso_examples")]
    streams=np.random.SeedSequence(SEED).spawn(24)
    results=[]
    input_hashes={}
    for job_index,(model,folder,orig,short,d,prompt) in enumerate(jobs):
        original_path=ROOT/"outputs"/orig/f"predictions_{short}_{d}_minimal_zero.csv"
        family="llama" if short.startswith("llama") else "mixtral"
        ablated_path=folder/"predictions"/family/f"predictions_{short}_{d}_{prompt}_ablated_zero.csv"
        old,new=rows(original_path),rows(ablated_path)
        aligned(new,old);aligned(old,rows(ROOT/"data"/d/f"{d}_test.csv"))
        for path in (original_path,ablated_path):input_hashes[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
        if d=="tsar2025":
            baseline,sources,refs,_,joined=load_data_tsar(original_path,ROOT/"data/tsar2025/tsar2025_test_200.csv")
            ablated,sources2,refs2,_,joined2=load_data_tsar(ablated_path,ROOT/"data/tsar2025/tsar2025_test_200.csv")
            assert sources==sources2 and refs==refs2 and joined.text_id.tolist()==joined2.text_id.tolist()
        else:
            sources=[r['original'] for r in old];refs=[[r['reference']] for r in old]
            baseline=[r['prediction'] for r in old];ablated=[r['prediction'] for r in new]
        n=EXPECTED[d]
        assert len(baseline)==len(ablated)==len(sources)==len(refs)==n
        score_o=float(metric.compute(sources=sources,predictions=baseline,references=refs)["sari"])
        score_a=float(metric.compute(sources=sources,predictions=ablated,references=refs)["sari"])
        assert corpus(sources,baseline,refs)==score_o and corpus(sources,ablated,refs)==score_a
        for name,value in (("minimal",score_o),(prompt+"_ablated",score_a)):
            saved=metric_rows[(metric_rows.model==model)&(metric_rows.dataset==d)&(metric_rows.prompt==name)].iloc[0]
            assert round(value,2)==float(saved.SARI)
        observed=score_a-score_o
        print(f"START {model} {d} {prompt}; delta={observed:.6f}",flush=True)
        rng=np.random.default_rng(streams[2*job_index]);dist=np.empty(B)
        for b in range(B):
            ix=rng.integers(0,n,size=n);s=[sources[i] for i in ix];r=[refs[i] for i in ix]
            dist[b]=corpus(s,[ablated[i] for i in ix],r)-corpus(s,[baseline[i] for i in ix],r)
        lo,hi=np.percentile(dist,[2.5,97.5]);rng=np.random.default_rng(streams[2*job_index+1]);extreme=0
        for b in range(P):
            swap=rng.integers(0,2,size=n)
            one=[ablated[i] if swap[i] else baseline[i] for i in range(n)]
            two=[baseline[i] if swap[i] else ablated[i] for i in range(n)]
            difference=corpus(sources,one,refs)-corpus(sources,two,refs)
            extreme+=abs(difference)>=abs(observed)-1e-12
        r={"model":model,"dataset":d,"prompt":prompt,"n":n,"baseline_SARI":score_o,
           "ablated_SARI":score_a,"delta_SARI":observed,"ci95_low":float(lo),"ci95_high":float(hi),
           "p_two_sided":(extreme+1)/(P+1)}
        results.append(r)
        key=short+'_'+d+'_'+prompt
        np.save(dest/(key+'_bootstrap.npy'),dist)
        pd.DataFrame({"model":model,"dataset":d,"prompt":prompt,"row_index":range(n),
            "text_id":[r['text_id'] for r in old],"source":sources,"baseline_output":baseline,
            "ablated_output":ablated,"references_json":[json.dumps(r,ensure_ascii=False) for r in refs],
            "baseline_SARI":[corpus([s],[p],[r]) for s,p,r in zip(sources,baseline,refs)],
            "ablated_SARI":[corpus([s],[p],[r]) for s,p,r in zip(sources,ablated,refs)]}).to_csv(dest/(key+'_paired_items.csv'),index=False)
        print(f"DONE {r}",flush=True)
        pd.DataFrame(results).to_csv(dest/"partial.csv",index=False)
    result=pd.DataFrame(results)
    result['p_holm_secondary_12']=holm(result.p_two_sided.to_numpy())
    primary=pd.read_csv(BASE/"combined/sari_comparisons.csv")
    both=np.concatenate([primary.p_two_sided.to_numpy(),result.p_two_sided.to_numpy()])
    all24=holm(both)
    primary['comparison']='ablated_minus_original';primary['p_holm_all_24']=all24[:12]
    secondary=result.copy();secondary['comparison']='ablated_minus_baseline';secondary['p_holm_all_24']=all24[12:]
    result['p_holm_all_24']=all24[12:]
    result.to_csv(output,index=False)
    pd.concat([primary,secondary],ignore_index=True).to_csv(dest/"all_24_comparisons.csv",index=False)
    method={"analysis":"secondary exploratory; ablated minus original baseline zero-shot",
        "bootstrap_replicates":B,"permutations":P,"seed":SEED,"rng":"SeedSequence(seed).spawn(24), two independent streams per comparison",
        "CI":"pointwise paired percentile 95%, raw corpus SARI recalculated on both sampled datasets",
        "p":"two-sided within-item randomization; (extreme+1)/(19999+1)",
        "multiplicity":"Holm over 12 secondary contrasts; additional Holm across all 24 primary+secondary contrasts",
        "primary_analysis":"unchanged; not selected based on secondary results",
        "cache":"only deterministic normalize/SARIsent operations cached; same raw installed corpus implementation",
        "sari_module_sha256":hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "inputs":input_hashes,"reference_file_sha256":hashlib.sha256((ROOT/'data/tsar2025/tsar2025_test_200.csv').read_bytes()).hexdigest(),
        "limits":"conditional on fixed runs/test rows; no equivalence or ISO causal attribution; within-document dependence not modeled in PLABA; no filtering of incomplete/capped outputs",
        "elapsed_seconds":time.perf_counter()-started,"complete":True}
    (dest/"methodology.json").write_text(json.dumps(method,indent=2),encoding='utf-8')
    print('COMPLETE',flush=True)


if __name__=="__main__":main()
