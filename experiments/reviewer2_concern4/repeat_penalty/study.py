"""Prepare frozen subset or run it explicitly; never changes original results."""
import argparse
import ast
import hashlib
import json
import random
import sys
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SEED = 20261022

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def prepare():
    if (HERE / 'manifest.json').exists():
        raise FileExistsError('Frozen manifest exists; refusing to replace selection')
    cases = {}
    frames = {}
    datasets = {}
    hashes = {'model_utils.py': digest(ROOT / 'model_utils.py')}
    tree = ast.parse((ROOT / 'model_utils.py').read_text(encoding='utf-8-sig'))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'simplify_one_ollama')
    expr = next(n.value for n in fn.body if isinstance(n, ast.Assign) and
                any(isinstance(t, ast.Name) and t.id == 'prompt' for t in n.targets))
    code = compile(ast.Expression(expr), '<shared prompt>', 'eval')

    def add(dataset, row_index, prompt, strategy, reason):
        key = (dataset, row_index, prompt, strategy)
        if key in cases:
            cases[key]['selection_reasons'].append(reason)
            return
        path = ROOT / 'outputs/mixtral_512' / f'predictions_mixtral_latest_{dataset}_{prompt}_{strategy}.csv'
        if path not in frames:
            frame = pd.read_csv(path, keep_default_na=False, dtype={'text_id': str})
            if dataset not in datasets:
                datasets[dataset] = pd.read_csv(ROOT/'data'/dataset/f'{dataset}_test.csv',
                    keep_default_na=False, dtype={'text_id': str})
            assert frame[['text_id','original','reference']].equals(
                datasets[dataset][['text_id','original','reference']]), f'Alignment mismatch: {path}'
            frames[path] = frame
        frame = frames[path]
        row = frame.iloc[row_index]
        name = f'{prompt}_zero.md' if strategy == 'zero' else f'{dataset}_{prompt}_{strategy}.md'
        prompt_path = ROOT / 'prompts' / name
        for p in [path, prompt_path]:
            hashes[str(p.relative_to(ROOT))] = digest(p)
        instructions = prompt_path.read_text(encoding='utf-8')
        message = eval(code, {'__builtins__': {}}, {'instrucciones': instructions, 'texto': row.original})
        cases[key] = dict(case_id=f'{dataset}_{row_index}_{prompt}_{strategy}', dataset=dataset,
            row_index=row_index, text_id=row.text_id, prompt=prompt, strategy=strategy,
            selection_reasons=[reason], original=row.original, reference=row.reference,
            historical_prediction=row.prediction, historical_done_reason=row.done_reason,
            historical_eval_count=int(row.eval_count), prompt_file=name, instructions=instructions,
            full_user_message=message, full_user_message_sha256=hashlib.sha256(message.encode()).hexdigest())

    # Draw first, without using prediction text, SARI, termination flags or lengths.
    random_draws = {}
    for offset, dataset in enumerate(['cochrane', 'plaba', 'tsar2025']):
        data = ROOT / 'data' / dataset / f'{dataset}_test.csv'
        hashes[str(data.relative_to(ROOT))] = digest(data)
        n = len(pd.read_csv(data))
        indexes = sorted(random.Random(SEED + offset).sample(range(n), 10))
        random_draws[dataset] = indexes
        for index in indexes:
            for prompt in ['iso', 'iso_examples']:
                for strategy in ['zero', 'one', 'few_random', 'few_metric']:
                    add(dataset, index, prompt, strategy, 'random_sample')
    # Apparent incomplete ORIGINAL zero-shot outputs recorded in the qualitative notes.
    for dataset, index, prompt in [('cochrane',124,'iso_examples'),
        ('plaba',110,'iso'), ('plaba',110,'iso_examples'), ('plaba',147,'iso')]:
        add(dataset,index,prompt,'zero','documented_original_zero_shot_fragment')
    notes = ROOT / 'experiments/focused_ablation/mixtral/qualitative/observations.json'
    hashes[str(notes.relative_to(ROOT))] = digest(notes)
    # Exact excerpts mentioned by the reviewer, searched across all original configurations.
    for path in sorted((ROOT / 'outputs/mixtral_512').glob('predictions_*.csv')):
        stem = path.stem.removeprefix('predictions_mixtral_latest_')
        dataset = stem.split('_')[0]
        config = stem[len(dataset)+1:]
        for strategy in ['few_random','few_metric','zero','one']:
            if config.endswith('_'+strategy):
                prompt = config[:-(len(strategy)+1)]
                break
        frame = pd.read_csv(path, keep_default_na=False)
        for index, row in frame.iterrows():
            if str(row.prediction).strip().endswith(('over 13,00','from 2006 to 2')):
                add(dataset,index,prompt,strategy,'reviewer_exact_fragment')
    records = list(cases.values())
    jobs = []
    for i, case in enumerate(records):
        for penalty in ([1.1,1.0] if i % 2 == 0 else [1.0,1.1]):
            jobs.append(dict(case_id=case['case_id'], repeat_penalty=penalty,
                job_id=f"{case['case_id']}_rp{str(penalty).replace('.', '_')}"))
    manifest = dict(design_version=2, model='mixtral:latest', sampling_seed=SEED,
        random_sample_strategies=['zero','one','few_random','few_metric'],
        random_sample_prompts=['iso','iso_examples'],
        random_draws=random_draws, sampling_unit='test CSV row; PLABA repeated IDs retained',
        options=dict(num_predict=512,num_ctx=8192,temperature=0.0,seed=42,top_k=1,
            top_p=1.0,repeat_last_n=64,num_gpu=999),
        source_sha256=hashes, cases=records, jobs=jobs)
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    pd.DataFrame([{k:v for k,v in c.items() if k not in ['instructions','full_user_message','original','reference']}
        for c in records]).to_csv(HERE/'selected_cases.csv',index=False)
    print(f'Prepared {len(records)} paired cases; {len(jobs)} generations. No inference executed.')

def run():
    import requests
    sys.path.insert(0,str(ROOT))
    from model_utils import simplify_one_ollama
    path = HERE/'manifest.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    for relative, expected in manifest['source_sha256'].items():
        assert digest(ROOT/relative)==expected, f'Input changed: {relative}'
    out = HERE/'results'
    out.mkdir(exist_ok=True)
    # Read-only runtime provenance; never pull or replace models.
    version = requests.get('http://localhost:11434/api/version',timeout=30)
    version.raise_for_status()
    show = requests.post('http://localhost:11434/api/show',json={'model':manifest['model']},timeout=30)
    show.raise_for_status()
    tags = requests.get('http://localhost:11434/api/tags',timeout=30)
    tags.raise_for_status()
    provenance = dict(version=version.json(),model=show.json(),tags=tags.json(),manifest_sha256=digest(path))
    runtime_path = HERE/'runtime.json'
    if runtime_path.exists():
        assert json.loads(runtime_path.read_text(encoding='utf-8'))==provenance, 'Runtime changed; refusing mixed-runtime resume'
    else:
        runtime_path.write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    cases = {c['case_id']:c for c in manifest['cases']}
    for i, job in enumerate(manifest['jobs']):
        target = out/(job['job_id']+'.json')
        if target.exists():
            saved=json.loads(target.read_text(encoding='utf-8'))
            assert saved['job']==job and saved['manifest_sha256']==digest(path)
            continue
        case=cases[job['case_id']]
        print(f"[{i+1}/{len(manifest['jobs'])}] {job['job_id']}",flush=True)
        prediction, _, _, _, metadata=simplify_one_ollama(
            texto=case['original'],instrucciones=case['instructions'],model_name=manifest['model'],
            marker='SIMPLIFIED TEXT:',max_new_tokens=512,num_ctx=8192,temperature=0.0,
            seed=42,top_k=1,top_p=1.0,repeat_penalty=job['repeat_penalty'],repeat_last_n=64,
            num_gpu=999,require_gpu=True,timeout=900)
        result=dict(job=job,manifest_sha256=digest(path),prediction=prediction,metadata=metadata)
        temporary=target.with_suffix('.tmp')
        temporary.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
        temporary.replace(target)
    print('Completed all generations. No metrics or human completeness labels calculated.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','run'])
    args=parser.parse_args()
    prepare() if args.action=='prepare' else run()
