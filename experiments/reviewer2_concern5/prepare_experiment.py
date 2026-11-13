"""Freeze CPU source embeddings, selections and per-input demonstration prompts."""
import hashlib
import argparse
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from retrieval_engine import encode_full_sources, select_three, normalized
from study import HERE, ROOT, MODELS, OPTIONS, sha

ENCODER = 'sentence-transformers/all-MiniLM-L6-v2'
REVISION = '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
DATASETS = {'cochrane':125,'plaba':148,'tsar2025':100}


def cache_fingerprint(train_path,test_path,pool,queries,encoder_hashes):
    return dict(train_sha256=sha(train_path),test_sha256=sha(test_path),encoder_sha256=encoder_hashes,
        retrieval_engine_sha256=sha(HERE/'retrieval_engine.py'),
        training_rows=pool.training_row_index.tolist(),
        queries_sha256=hashlib.sha256(json.dumps(queries,ensure_ascii=False).encode()).hexdigest(),
        encoder_revision=REVISION,chunk_tokens=224,max_seq_length=256)


def prepare(resume=False):
    if (HERE/'experiment_manifest.json').exists():
        raise FileExistsError('Frozen retrieval preparation exists; refusing overwrite')
    for directory in ['prompts','embeddings']:
        if (HERE/directory).exists() and not resume:
            raise FileExistsError(f'Partial preparation exists; preserve/inspect it: {directory}')
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    os.environ['OMP_NUM_THREADS']='2';os.environ['MKL_NUM_THREADS']='2'
    import torch
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(42)
    torch.use_deterministic_algorithms(True)
    from huggingface_hub.constants import HF_HUB_CACHE
    from sentence_transformers import SentenceTransformer
    snapshot = Path(HF_HUB_CACHE)/'models--sentence-transformers--all-MiniLM-L6-v2'/'snapshots'/REVISION
    if not snapshot.exists():
        raise FileNotFoundError('Pinned local encoder snapshot is missing; no automatic downloads')
    encoder_model = SentenceTransformer(str(snapshot),device='cpu',local_files_only=True)
    if encoder_model.max_seq_length != 256:
        raise ValueError('Encoder max sequence length changed')
    encoder_hashes = {str(p.relative_to(snapshot).as_posix()):sha(p) for p in snapshot.rglob('*') if p.is_file()}
    # Reuse the already tested exact demonstration-slot replacement, without modifying it.
    helper_dir = ROOT/'experiments/reviewer2_concern2'
    sys.path.insert(0,str(helper_dir))
    spec = importlib.util.spec_from_file_location('existing_demo_slots',helper_dir/'study.py')
    slots = importlib.util.module_from_spec(spec);spec.loader.exec_module(slots)
    from inspect_original_selection import extract
    frozen_seed_manifest = json.loads((helper_dir/'experiment_manifest.json').read_text(encoding='utf-8'))
    code_files = [Path(__file__), HERE/'retrieval_engine.py', HERE/'study.py', HERE/'evaluate_retrieval.py',
        HERE/'run_block.ps1', HERE/'ANALYSIS_PLAN.md',ROOT/'model_utils.py',helper_dir/'study.py',
        helper_dir/'inspect_original_selection.py',helper_dir/'evaluate_metrics.py',helper_dir/'evaluate_descriptors.py',
        ROOT/'eval_utils.py',ROOT/'focused_metric_runtime.py']
    hashes = {p.relative_to(ROOT).as_posix():sha(p) for p in code_files}
    gold_path = ROOT/'data/tsar2025/tsar2025_test_200.csv'
    hashes[gold_path.relative_to(ROOT).as_posix()] = sha(gold_path)
    selections, indices, jobs, diagnostics, pools = [], [], [], [], []
    for dataset,n in DATASETS.items():
        print(f'Preparing {dataset}: CPU embeddings, no Ollama.',flush=True)
        train_path = ROOT/'data'/dataset/f'{dataset}_train.csv'
        test_path = ROOT/'data'/dataset/f'{dataset}_test.csv'
        for path in [train_path,test_path]:
            name = path.relative_to(ROOT).as_posix()
            if sha(path) != frozen_seed_manifest['source_sha256'][name]:
                raise ValueError('Author-supplied frozen train/test changed')
            hashes[name] = sha(path)
        train = pd.read_csv(train_path,keep_default_na=False,dtype={'text_id':str})
        test = pd.read_csv(test_path,keep_default_na=False,dtype={'text_id':str})
        if len(test) != n:
            raise ValueError('Unexpected test size')
        train['training_row_index'] = range(len(train))
        train['normalized_source'] = train.original.map(normalized)
        test_keys = set(test.original.map(normalized))
        pool = train.drop_duplicates('normalized_source',keep='first')
        overlaps = pool.normalized_source.isin(test_keys)
        excluded = int(overlaps.sum())
        pool = pool[~overlaps].reset_index(drop=True)
        if len(pool) < 3:
            raise ValueError('Insufficient distinct train sources')
        pools.append(dict(dataset=dataset,training_rows=len(train),distinct_sources_before_exclusions=train.normalized_source.nunique(),
            eligible_distinct_sources=len(pool),exact_test_source_exclusions=excluded,
            duplicate_source_policy='first original training row; no reference quality/CEFR-based choice'))
        # Duplicate test sources deliberately share one retrieval query and selection.
        test_unique = test.drop_duplicates('original',keep='first')
        unique_sources = test_unique.original.tolist()
        folder = HERE/'embeddings';folder.mkdir(exist_ok=True)
        cache = folder/f'{dataset}.npz'
        proof_path = folder/f'{dataset}.json'
        fingerprint = cache_fingerprint(train_path,test_path,pool,unique_sources,encoder_hashes)
        if cache.exists():
            if not resume or not proof_path.exists():
                raise ValueError('Embedding cache exists without verified resume provenance')
            proof = json.loads(proof_path.read_text())
            if proof['fingerprint'] != fingerprint or proof['cache_sha256'] != sha(cache):
                raise ValueError('Embedding cache provenance changed')
            cached = np.load(cache)
            train_vectors,query_vectors = cached['train'],cached['queries']
            lengths,chunks = cached['token_lengths'],cached['chunk_counts']
            if train_vectors.shape != (len(pool),384) or query_vectors.shape != (len(unique_sources),384):
                raise ValueError('Cached embedding shape mismatch')
            print(f'Reusing verified {dataset} CPU embeddings.',flush=True)
        else:
            embeddings,lengths,chunks = encode_full_sources(encoder_model,pool.original.tolist()+unique_sources)
            train_vectors,query_vectors = embeddings[:len(pool)],embeddings[len(pool):]
            np.savez_compressed(cache,train=train_vectors,queries=query_vectors,
                training_row_index=pool.training_row_index.to_numpy(),token_lengths=lengths,chunk_counts=chunks)
            proof_path.write_text(json.dumps(dict(fingerprint=fingerprint,cache_sha256=sha(cache)),indent=2),encoding='utf-8')
        hashes[cache.relative_to(ROOT).as_posix()] = sha(cache)
        hashes[proof_path.relative_to(ROOT).as_posix()] = sha(proof_path)
        query_lookup = {text:i for i,text in enumerate(unique_sources)}
        scores = query_vectors.astype(np.float64) @ train_vectors.astype(np.float64).T
        choices = {}
        for row_index,row in test.iterrows():
            selected = select_three(scores[query_lookup[row.original]],pool,row.original,row.text_id,dataset)
            selected_rows = pool.iloc[[i for i,_ in selected]].copy()
            choices[row_index] = selected_rows
            for rank,((pool_index,score),(_,candidate)) in enumerate(zip(selected,selected_rows.iterrows()),1):
                selections.append(dict(dataset=dataset,test_row_index=row_index,test_text_id=row.text_id,
                    rank=rank,training_row_index=int(candidate.training_row_index),training_text_id=candidate.text_id,
                    cosine_similarity=score,original=candidate.original,reference=candidate.reference))
        for prompt in ['minimal','iso','iso_examples']:
            template_path = ROOT/'prompts'/f'{dataset}_{prompt}_few_random.md'
            metric_path = ROOT/'prompts'/f'{dataset}_{prompt}_few_metric.md'
            for path in [template_path,metric_path]:
                hashes[path.relative_to(ROOT).as_posix()] = sha(path)
            template = template_path.read_text(encoding='utf-8')
            metric_template = metric_path.read_text(encoding='utf-8')
            instruction_prefix = template.split('EXAMPLE 1')[0]
            if ' '.join(instruction_prefix.split()) != ' '.join(metric_template.split('EXAMPLE 1')[0].split()):
                raise ValueError('Few-random/few-metric instruction content differs')
            historical_full_lengths = []
            def full_prompt(instructions, source):
                return f'{instructions}\n\n# TARGET TEXT\n\n"""\n{source}\n"""\n\n# ANSWER\nWrite the simplified version below and nothing else.\n'
            for source in test.original:
                historical_full_lengths += [len(full_prompt(template,source)),len(full_prompt(metric_template,source))]
            historical_max = max(historical_full_lengths)
            for row_index,row in test.iterrows():
                text = slots.substitute(template,choices[row_index])
                parsed = extract(text)
                if len(parsed) != 3 or text.split('EXAMPLE 1')[0] != instruction_prefix:
                    raise ValueError('Instruction preservation failed')
                for example, candidate in zip(parsed,choices[row_index].itertuples()):
                    if (example['original'],example['reference'],example['displayed_id']) != (slots.normalized(candidate.original),slots.normalized(candidate.reference),candidate.text_id):
                        raise ValueError('Demo slot content changed')
                path = HERE/'prompts'/dataset/prompt/f'row_{row_index:03d}.md'
                path.parent.mkdir(parents=True,exist_ok=True)
                if path.exists():
                    if path.read_text(encoding='utf-8') != text:
                        raise ValueError('Prepared prompt changed during preparation resume')
                else:
                    path.write_text(text,encoding='utf-8')
                hashes[path.relative_to(ROOT).as_posix()] = sha(path)
                length = len(full_prompt(text,row.original))
                indices.append(dict(dataset=dataset,prompt=prompt,row_index=row_index,text_id=row.text_id,
                    prompt_path=path.relative_to(ROOT).as_posix(),instructions_sha256=sha(path)))
                diagnostics.append(dict(dataset=dataset,prompt=prompt,row_index=row_index,prompt_characters=length,
                    historical_max_characters=historical_max,above_historical_max_characters=length>historical_max,
                    exact_ollama_token_count_available=False))
            for model,(ollama,short) in MODELS.items():
                output = HERE/'predictions'/model/f'predictions_{short}_{dataset}_{prompt}_few_retrieval.csv'
                jobs.append(dict(job_id=f'{model}_{dataset}_{prompt}_few_retrieval',model=model,ollama_model=ollama,
                    dataset=dataset,prompt=prompt,strategy='few_retrieval',n=n,test_path=test_path.relative_to(ROOT).as_posix(),
                    prediction_path=output.relative_to(ROOT).as_posix()))
    if len(jobs) != 18 or sum(j['n'] for j in jobs) != 2238 or len(indices) != 1119 or len(selections) != 1119:
        raise ValueError('Unexpected experiment dimensions')
    for filename, frame in [('selected_examples.csv',pd.DataFrame(selections)),('prompt_index.csv',pd.DataFrame(indices)),
                            ('context_length_comparison.csv',pd.DataFrame(diagnostics)),('training_pool.csv',pd.DataFrame(pools))]:
        path = HERE/filename;frame.to_csv(path,index=False)
        hashes[path.relative_to(ROOT).as_posix()] = sha(path)
    manifest = dict(study='Reviewer 2 Concern 5: per-input source-only semantic retrieval',jobs=jobs,options=OPTIONS,
        source_sha256=hashes,encoder=ENCODER,encoder_revision=REVISION,encoder_snapshot_path=str(snapshot),
        encoder_snapshot_sha256=encoder_hashes,embedding_device='cpu',embedding_threads=2,embedding_chunk_tokens=224,
        embedding_max_seq_length=256,chunk_pooling='token-length-weighted mean of unit chunk embeddings, then normalize',
        retrieval='cosine descending, stable training-row-index tie break; 3 distinct sources/documents',
        training_reference_policy='first original row per normalized source, independent of reference/CEFR/quality',
        test_reference_used_for_retrieval=False,generations_started=False,model_options_match_original=True,
        exact_ollama_token_preflight=False,context_policy='no trimming or rank changes; compare character lengths and inspect observed runtime tokens',
        versions={name:importlib.metadata.version(name) for name in ['torch','sentence-transformers','transformers','numpy','pandas']})
    for name,digest in hashes.items():
        if sha(ROOT/name) != digest:
            raise ValueError(f'Input changed during preparation: {name}')
    for name,digest in encoder_hashes.items():
        if sha(snapshot/name) != digest:
            raise ValueError('Encoder snapshot changed')
    (HERE/'planned_runs.csv').write_text(pd.DataFrame(jobs).to_csv(index=False),encoding='utf-8')
    (HERE/'experiment_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'Prepared 18 configurations / 2238 outputs; 1119 shared per-input prompts. No Ollama inference.',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume',action='store_true',help='Reuse only fingerprinted embedding caches and identical prepared prompts')
    prepare(parser.parse_args().resume)
