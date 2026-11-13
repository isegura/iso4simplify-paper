"""Build browsable reports exclusively from saved predictions and scores."""
from pathlib import Path
import csv, hashlib, html, itertools, json, re
from collections import Counter
from urllib.parse import unquote

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'reports'
METRICS=['SARI','BERTScore-F1','MeaningBERT','FKGL','FRE']
LABEL={'minimal':'Baseline','iso':'ISO','iso_examples':'ISO+examples'}
HASHES={}
def read(p):
    HASHES[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def esc(x):return html.escape(str(x),quote=True)
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
STYLE='''body{font:16px/1.5 Arial,sans-serif;color:#172b3a;background:#f6f8fa;margin:0}main{max-width:1400px;margin:auto;padding:24px}article{background:white;padding:20px;margin:24px 0;border:1px solid #cad4df;border-radius:8px}.texts{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}.text{padding:16px;background:#edf4fc;white-space:pre-wrap;overflow-wrap:anywhere}.text.output{background:#fff3e4}h3{margin-top:0}table{border-collapse:collapse;background:white}td,th{padding:7px 12px;border:1px solid #ccd3da;text-align:left}nav,.note{padding:12px;background:#e7eef6}a{color:#07569a}details{margin:12px 0}input{padding:10px;width:90%;max-width:700px}small{overflow-wrap:anywhere}'''
def page(title,body):return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><style>'+STYLE+'</style><main><h1>'+esc(title)+'</h1>'+body+'</main></html>'
def cards(source,refs,outputs):
    parts=[('Source',source,False)]+[(f'Reference {i+1}',r,False) for i,r in enumerate(refs)]+[(k,v,True) for k,v in outputs]
    return '<div class="texts">'+''.join('<section class="text'+(' output' if out else '')+'"><h3>'+esc(k)+'</h3>'+esc(v or '[Empty output]')+'</section>' for k,v,out in parts)+'</div>'
def table(rows,keys):return '<table><tr>'+''.join('<th>'+esc(k)+'</th>' for k in keys)+'</tr>'+''.join('<tr>'+''.join('<td>'+esc(r.get(k,''))+'</td>' for k in keys)+'</tr>' for r in rows)+'</table>'
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Inventory pre-existing reports before creating the new archive.
    old=[p for p in ROOT.rglob('*.html') if not any(x.startswith('.venv') or x in ['.git','node_modules','tmp','html_reports_20261113'] for x in p.parts)]
    old_counts=Counter(p.relative_to(ROOT).parts[0] for p in old)
    gold=read(ROOT/'data/tsar2025/tsar2025_test_200.csv')
    tsar={}
    for r in gold:tsar.setdefault(re.match(r'\d+',r['text_id']).group(),[]).append(r['reference'])
    manifest=[]; index=[];covered=0
    for model,dataset,prompt,strategy in itertools.product(['llama','mixtral'],['cochrane','plaba','tsar2025'],LABEL,['zero','one','few_random','few_metric','few_retrieval']):
      for seed in ([42,44,46] if strategy in ['one','few_random'] else ['fixed']):
        name=f"predictions_{'llama3_1_8b' if model=='llama' else 'mixtral_latest'}_{dataset}_{prompt}_{strategy}.csv"
        if strategy=='few_retrieval':
            base=ROOT/'experiments/reviewer2_concern5/prepared_retrieval_20261102'
            raw=base/'predictions'/model/name
            score=base/f'evaluation/{model}/{dataset}_{prompt}_{strategy}_items.csv'
        elif seed in [44,46]:
            base=ROOT/'experiments/reviewer2_concern2'
            raw=base/f'predictions/{model}/seed_{seed}'/name
            score=base/f'evaluation/metrics/{model}/seed_{seed}/{dataset}_{prompt}_{strategy}_items.csv'
        else:
            raw=ROOT/f'outputs/{model}_512'/name
            score=(ROOT/f'experiments/reviewer2_concern2/evaluation/metrics/{model}/seed_42/{dataset}_{prompt}_{strategy}_items.csv' if seed==42 else raw)
        data,scores,test=read(raw),read(score),read(ROOT/f'data/{dataset}/{dataset}_test.csv')
        assert len(data)==len(scores)==len(test)
        title=f'{model} / {dataset} / {LABEL[prompt]} / {strategy.replace("_","-")} / selection {seed}'
        articles=[]
        for i,(r,s,t) in enumerate(zip(data,scores,test)):
            assert r['text_id']==s['text_id']==t['text_id'] and r['original']==t['original']
            if 'row_index' in s:assert int(s['row_index'])==i
            refs=json.loads(s['references_json']) if s.get('references_json') else tsar[r['text_id']] if dataset=='tsar2025' else [r['reference']]
            assert all(isinstance(x,str) for x in refs)
            for key in METRICS:float(s[key])
            meta={k:s[k] for k in METRICS}
            meta.update(text_id=r['text_id'],row_index=i,done_reason=r.get('done_reason',''),generated_tokens=r.get('eval_count',''),input_tokens=r.get('prompt_eval_count',''))
            article='<article id="row-'+str(i)+'"><h2>Row '+str(i)+' · '+esc(r['text_id'])+'</h2>'+table([meta],list(meta))+cards(r['original'],refs,[('Generated simplification',r['prediction'])])+'</article>'
            articles.append((float(s['SARI']),i,article))
        rel=Path('main')/model/dataset/f'{prompt}_{strategy}_{seed}'
        intro='<nav><a href="../../../index.html">Report index</a></nav><p class="note">Saved outputs and existing per-item scores. No inference or metric recomputation. BLEU is a corpus-level result and is not presented as an item-level score. Selection seeds identify demonstration sets.</p><small>Predictions: '+esc(raw.relative_to(ROOT).as_posix())+'<br>Scores: '+esc(score.relative_to(ROOT).as_posix())+'</small>'
        write(OUT/(str(rel)+'_all.html'),page(title,intro+'<p>All '+str(len(data))+' outputs in test-row order.</p>'+''.join(x[2] for x in articles)))
        write(OUT/(str(rel)+'_lowest_sari.html'),page(title+' / lowest SARI',intro+'<p>15 lowest-SARI outputs; ties ordered by test-row index. This is an automatic selection, not a new qualitative evaluation.</p>'+''.join(x[2] for x in sorted(articles)[:15])))
        record=dict(model=model,dataset=dataset,prompt=prompt,strategy=strategy,selection_seed=seed,n=len(data),prediction_path=raw.relative_to(ROOT).as_posix(),score_path=score.relative_to(ROOT).as_posix(),all_report=str(rel).replace('\\','/')+'_all.html',lowest_report=str(rel).replace('\\','/')+'_lowest_sari.html')
        manifest.append(record);covered+=len(data)
        index.append('<tr class="run"><td>'+esc(title)+'</td><td>'+str(len(data))+'</td><td><a href="'+record['all_report']+'">All outputs</a></td><td><a href="'+record['lowest_report']+'">Lowest 15 SARI</a></td></tr>')
    assert len(manifest)==162 and covered==20142
    # Separate matched-pair ablation reports, preserving existing scores.
    abl_count=0
    for model,folder in [('llama',ROOT/'experiments/focused_ablation'),('mixtral',ROOT/'experiments/focused_ablation/mixtral')]:
        data=read(folder/'per_item/all_paired_items.csv')
        for dataset,prompt in itertools.product(['cochrane','plaba','tsar2025'],['iso','iso_examples']):
            rows=[r for r in data if r['dataset']==dataset and r['prompt']==prompt];assert len(rows)=={'cochrane':125,'plaba':148,'tsar2025':100}[dataset]
            body='<nav><a href="../index.html">Report index</a></nav><p>Matched zero-shot outputs; automatic presentation of saved pairs, not a new qualitative review.</p>'
            for r in rows:
                body+='<article><h2>Row '+esc(r['row_index'])+' · '+esc(r['text_id'])+'</h2>'+table([r],['original_SARI','ablated_SARI','delta_SARI','original_done_reason','ablated_done_reason'])+cards(r['source'],json.loads(r['references_json']),[('Original prompt',r['original_output']),('Organization/summary block removed',r['ablated_output'])])+'</article>'
            path=f'ablation/{model}_{dataset}_{prompt}.html';write(OUT/path,page(f'Ablation: {model} / {dataset} / {prompt}',body));index.append('<tr><td>Ablation '+esc(f'{model} / {dataset} / {prompt}')+'</td><td>'+str(len(rows))+'</td><td colspan="2"><a href="'+path+'">Matched pairs</a></td></tr>');abl_count+=len(rows)
    assert abl_count==1492
    diag=read(ROOT/'experiments/reviewer2_concern4/repeat_penalty/cochrane_iso_shared_subset/combined_review/all_62_paired_comparisons.csv')
    assert len(diag)==62
    for strategy in ['zero','few_random']:
        rows=[r for r in diag if r['strategy']==strategy];assert len(rows)==31
        body='<nav><a href="../index.html">Report index</a></nav><p>Selected diagnostic subset. Existing penalty-1.1 outputs versus saved penalty-1.0 rerun. These selected cases do not estimate full-test-set error frequency.</p>'
        for r in rows:body+='<article><h2>'+esc(r['text_id'])+'</h2>'+table([r],['selection_group','historical_done_reason','new_done_reason','historical_endpoint_label','new_endpoint_label'])+cards(r['original'],[r['reference']],[('Repetition penalty 1.1',r['historical_prediction']),('Repetition penalty 1.0',r['new_prediction'])])+'</article>'
        path=f'diagnostic/{strategy}.html';write(OUT/path,page('Repetition penalty: Mixtral / Cochrane / ISO / '+strategy,body));index.append('<tr><td>Repetition penalty '+strategy+'</td><td>31</td><td colspan="2"><a href="'+path+'">Matched pairs</a></td></tr>')
    write(OUT/'index.html',page('iso4simplify — saved-output reports','<p>Main study: 162 configurations and 20,142 outputs. Ablation: 12 comparisons and 1,492 pairs. Repetition-penalty diagnostic: 62 pairs. The latter two are separate from main-study totals.</p><input id="search" placeholder="Filter by model, dataset, prompt, strategy or seed" oninput="document.querySelectorAll(\'tbody tr\').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase()))"><table><thead><tr><th>Configuration / study</th><th>Outputs or pairs</th><th colspan="2">Reports</th></tr></thead><tbody>'+''.join(index)+'</tbody></table>'))
    # Verify every local HTML link and every generated document structure.
    files=list(OUT.rglob('*.html'));links=0
    for p in files:
        content=p.read_text(encoding='utf-8');assert content.startswith('<!doctype html>') and content.endswith('</html>')
        for link in re.findall(r'href="([^"]+)"',content):
            assert (p.parent/unquote(link.split('#')[0])).is_file(),(p,link)
            links+=1
    proof=dict(main_configurations=len(manifest),main_outputs=covered,ablation_pairs=abl_count,diagnostic_pairs=len(diag),html_files=len(files),local_links_verified=links,existing_html_count=len(old),existing_html_by_root=dict(old_counts),source_sha256=HASHES,no_inference=True,no_metric_recomputation=True)
    write(HERE/'manifest.json',json.dumps(manifest,indent=2));write(HERE/'verification.json',json.dumps(proof,indent=2))
    write(HERE/'README.md','# HTML reports\n\nOpen `reports/index.html`. Built only from saved outputs and scores. Main study, ablation and repetition-penalty diagnostic are kept separate. Existing HTML reports are preserved. Every configuration has a full report and a lowest-15-SARI report; ranking uses saved SARI with row-index tie breaks. Both TSAR references are included. BLEU is not shown as an item-level metric.\n\nRebuild: `python experiments/html_reports_20261113/build_reports.py`. See `manifest.json` for per-run provenance and `verification.json` for source hashes and coverage checks. No new qualitative judgments are introduced.\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
