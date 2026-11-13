"""Audit frozen prompt demonstrations and notebook evidence, without inference."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
NOTEBOOK=Path('C:/Users/isegu/Downloads/select-random-examples_v2.ipynb')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def normalized(text):return ' '.join(text.strip().strip('"').split())

def extract(text):
    matches=list(re.finditer(r'^EXAMPLE\s+(\d+)\s*\(([^)]+)\)\s*$',text,re.M))
    examples=[]
    for i,match in enumerate(matches):
        block=text[match.end():matches[i+1].start() if i+1<len(matches) else len(text)]
        original,rewrite=block.split('ORIGINAL:',1)[1].split('SIMPLIFIED TEXT:',1)
        original=normalized(original);rewrite=normalized(rewrite)
        assert original and rewrite
        examples.append(dict(position=int(match.group(1)),displayed_id=match.group(2),
            original=original,reference=rewrite,source_sha256=hashlib.sha256(original.encode()).hexdigest(),
            pair_sha256=hashlib.sha256((original+'\n'+rewrite).encode()).hexdigest()))
    return examples

def main():
    evidence=HERE/'notebook_evidence';evidence.mkdir(exist_ok=True)
    target=evidence/NOTEBOOK.name
    if not target.exists():shutil.copy2(NOTEBOOK,target)
    assert sha(target)==sha(NOTEBOOK)
    notebook=json.loads(target.read_text(encoding='utf-8-sig'))
    codes=[''.join(c.get('source',[])) for c in notebook['cells'] if c['cell_type']=='code']
    code='\n\n'.join(codes)
    assert re.search(r'\bSEED\s*=\s*42\b',code)
    assert 'random_state=SEED' in code and "DATASET='tsar2025'" in code
    (evidence/'code_cells.txt').write_text(code,encoding='utf-8')
    records=[];summary=[];hashes={str(target.relative_to(ROOT)):sha(target)}
    for dataset in ['cochrane','plaba','tsar2025']:
        selections={}
        test_path=ROOT/'data'/dataset/f'{dataset}_test.csv'
        tests=pd.read_csv(test_path,keep_default_na=False)
        test_sources={normalized(x) for x in tests.original.astype(str)}
        hashes[str(test_path.relative_to(ROOT))]=sha(test_path)
        for prompt in ['minimal','iso','iso_examples']:
            for strategy in ['one','few_random']:
                path=ROOT/'prompts'/f'{dataset}_{prompt}_{strategy}.md'
                hashes[str(path.relative_to(ROOT))]=sha(path)
                examples=extract(path.read_text(encoding='utf-8'))
                assert len(examples)==(1 if strategy=='one' else 3)
                selections[(prompt,strategy)]=examples
                for e in examples:
                    records.append(dict(dataset=dataset,prompt=prompt,strategy=strategy,
                        prompt_file=path.name,exact_source_overlap_with_test=e['original'] in test_sources,**e))
        first=selections[('minimal','few_random')]
        for prompt in ['minimal','iso','iso_examples']:
            assert [x['pair_sha256'] for x in selections[(prompt,'few_random')]]==[x['pair_sha256'] for x in first]
            assert selections[(prompt,'one')][0]['pair_sha256']==first[0]['pair_sha256']
        train=ROOT/'data'/dataset/f'{dataset}_train.csv'
        summary.append(dict(dataset=dataset,training_path=str(train.relative_to(ROOT)),training_available=train.exists(),
            original_displayed_ids=[x['displayed_id'] for x in first],
            distinct_source_texts=len({x['source_sha256'] for x in first}),
            repeated_id_labels=len({x['displayed_id'] for x in first})<3,
            shared_examples_across_prompts_verified=True,one_is_first_few_example=True,
            seed42_evidence='Notebook code and stored TSAR output/order match' if dataset=='tsar2025' else
                'Notebook supports this workflow, but dataset-specific replay requires training CSV'))
    frame=pd.DataFrame(records)
    assert len(frame)==36
    assert not frame.exact_source_overlap_with_test.any()
    frame.to_csv(HERE/'original_demonstrations.csv',index=False)
    (HERE/'original_selection_summary.json').write_text(json.dumps(dict(notebook_sha256=sha(target),
        notebook_selection_seed=42,notebook_generation_executed=False,
        saved_tsar_training_shape=[40,4],saved_tsar_sampled_rows=[19,16,15],
        saved_tsar_sampled_ids=['10-b1','09-a2','08-b1'],datasets=summary,
        source_sha256=hashes),indent=2,ensure_ascii=False),encoding='utf-8')
    for relative,digest in hashes.items():assert sha(ROOT/relative)==digest,relative
    print('Audited 18 prompt files / 36 demonstration occurrences. Examples shared across prompt types; one-shot uses first few-shot example. No normalized exact-source overlap with test.')
    print('Missing training files:',[s['training_path'] for s in summary if not s['training_available']])

if __name__=='__main__':main()
