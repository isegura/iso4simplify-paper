"""Historical generation-time estimates for the 12 runnable study blocks."""
from pathlib import Path
import hashlib
import json
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
RANGES={('llama','cochrane'):(.75,1.5),('llama','plaba'):(55/60,1.75),
        ('llama','tsar2025'):(.5,1),('mixtral','cochrane'):(18,36),
        ('mixtral','plaba'):(19,37),('mixtral','tsar2025'):(5,9)}

def main():
    records=[];hashes={}
    for model,short in [('llama','llama3_1_8b'),('mixtral','mixtral_latest')]:
        for dataset in ['cochrane','plaba','tsar2025']:
            seconds=0.;n=0
            for prompt in ['minimal','iso','iso_examples']:
                for strategy in ['one','few_random']:
                    path=ROOT/'outputs'/(model+'_512')/f'predictions_{short}_{dataset}_{prompt}_{strategy}.csv'
                    frame=pd.read_csv(path,keep_default_na=False)
                    times=pd.to_numeric(frame.wall_time_s,errors='raise')
                    assert times.notna().all() and (times>=0).all()
                    seconds+=float(times.sum());n+=len(frame)
                    hashes[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
            for seed in [44,46]:
                low,high=RANGES[(model,dataset)]
                records.append(dict(model=model,dataset=dataset,selection_seed=seed,
                    configurations=6,new_outputs=n,historical_generation_hours=seconds/3600,
                    planning_low_hours=low,planning_high_hours=high,
                    command=f'.\\experiments\\reviewer2_concern2\\run_block.ps1 -Model {model} -Seed {seed} -Dataset {dataset}'))
    result=pd.DataFrame(records)
    assert len(result)==12 and result.new_outputs.sum()==8952
    result.to_csv(HERE/'runtime_estimates.csv',index=False)
    (HERE/'runtime_estimates_method.json').write_text(json.dumps(dict(
        basis='Sum of original wall_time_s for the six matching full-test configurations per block; reused as estimate for each new selection seed',
        margins='Planning ranges selected as practical margins, not confidence intervals or measured new-seed runtimes',
        excludes='Metric evaluation, statistical analysis, human review, interrupted runs and machine downtime',
        limitations='New demonstration lengths, response lengths, early stops, offloading and concurrent GPU use can change runtime',
        source_sha256=hashes,total_historical_reference_hours=float(result.historical_generation_hours.sum()),
        total_planning_low_hours=float(result.planning_low_hours.sum()),
        total_planning_high_hours=float(result.planning_high_hours.sum())),indent=2),encoding='utf-8')
    print(result.groupby('model')[['historical_generation_hours','planning_low_hours','planning_high_hours']].sum().to_string())

if __name__=='__main__':main()
