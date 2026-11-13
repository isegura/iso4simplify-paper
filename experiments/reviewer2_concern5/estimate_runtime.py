"""Reference timing from saved few-random/few-metric runs; no generation."""
from pathlib import Path
import hashlib
import json
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    rows, hashes = [], {}
    for model,short in [('llama','llama3_1_8b'),('mixtral','mixtral_latest')]:
        for dataset,n in [('cochrane',125),('plaba',148),('tsar2025',100)]:
            hours = {}
            for strategy in ['few_random','few_metric']:
                total = 0.
                for prompt in ['minimal','iso','iso_examples']:
                    path = ROOT/'outputs'/f'{model}_512'/f'predictions_{short}_{dataset}_{prompt}_{strategy}.csv'
                    hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
                    total += pd.read_csv(path,usecols=['wall_time_s']).wall_time_s.sum()
                hours[strategy] = total/3600
            reference = sum(hours.values())/2
            rows.append(dict(model=model,dataset=dataset,configurations=3,new_outputs=3*n,
                historical_few_random_hours=hours['few_random'],historical_few_metric_hours=hours['few_metric'],
                reference_hours=reference,planning_low_hours=reference*.8,planning_high_hours=reference*1.6))
    frame = pd.DataFrame(rows)
    frame.to_csv(HERE/'runtime_estimates.csv',index=False)
    (HERE/'runtime_estimates_method.json').write_text(json.dumps(dict(source_sha256=hashes,
        method='Mean summed historical wall_time_s for the three prompts in few-random and few-metric, per model/dataset',
        planning_range='0.8 to 1.6 times reference; not a confidence interval',
        excludes='retrieval preparation, evaluation, pauses and failures; new prompt lengths can change runtime'),indent=2),encoding='utf-8')
    print(frame[['model','dataset','reference_hours']].to_string(index=False))


if __name__ == '__main__':
    main()
