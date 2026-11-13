"""Summarize existing descriptors across three selections without loading models."""
import hashlib
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DEST = HERE / 'evaluation/descriptors/summaries'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    keys = ['model', 'dataset', 'prompt', 'strategy']
    frames = []
    inputs = {}
    for seed in [42, 44, 46]:
        stem = f'all_models_all_datasets_seed_{seed}'
        path = DEST / (stem + '.csv')
        proof_path = DEST / (stem + '.json')
        proof = json.loads(proof_path.read_text(encoding='utf-8'))
        assert proof['predictions_verified_unchanged'] and proof['configurations'] == 36
        assert proof['descriptor_code_sha256'] == sha(HERE/'evaluate_descriptors.py')
        assert proof['screening_code_sha256'] == sha(ROOT/'generate_systematic_error_analysis_512.py')
        for name, digest in proof['input_sha256'].items():
            assert sha(ROOT/name) == digest, name
        frame = pd.read_csv(path)
        assert len(frame) == 36 and set(frame.selection_seed) == {seed}
        assert int(frame.n.sum()) == 4476
        assert not frame.duplicated(keys).any()
        frames.append(frame)
        for f in [path, proof_path]:
            inputs[f.relative_to(ROOT).as_posix()] = sha(f)
    raw = pd.concat(frames, ignore_index=True)
    records = []
    measures = ['mean_LEN_COMPLEX','mean_LEN_PRED','mean_LEN_REF',
                'mean_compression_ratio','mean_copy_rate']
    for key, group in raw.groupby(keys, sort=True):
        assert set(group.selection_seed) == {42,44,46} and len(group) == 3
        assert group.n.nunique() == 1
        for measure in measures:
            values = group.set_index('selection_seed')[measure]
            records.append(dict(zip(keys,key), measure=measure, n_seeds=3,
                n_test=int(group.n.iloc[0]), seed_42=float(values[42]),
                seed_44=float(values[44]), seed_46=float(values[46]),
                mean=float(values.mean()), sd=float(values.std(ddof=1)),
                minimum=float(values.min()), maximum=float(values.max())))
    raw.to_csv(DEST/'all_models_all_datasets_per_seed.csv',index=False)
    pd.DataFrame(records).to_csv(DEST/'all_models_all_datasets_mean_sd.csv',index=False)
    (DEST/'all_models_all_datasets_methodology.json').write_text(json.dumps(dict(
        seeds=[42,44,46],sd_ddof=1,configurations=108,conditions=36,
        descriptors=measures,input_sha256=inputs,summary_code_sha256=sha(Path(__file__)),
        model_calls=0,original_fixed_conditions_replicated=False,
        interpretation='Descriptive variation between the three selected demonstration sets, not inferential uncertainty.'),indent=2)+'\n',encoding='utf-8')
    print('Summarized descriptors: 108 configurations, 36 conditions, three selections; no models.')


if __name__ == '__main__':
    main()
