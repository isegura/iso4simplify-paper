"""Independent arithmetic, pairing, link and artifact checks for retrieval delivery."""
from pathlib import Path
import hashlib
from html.parser import HTMLParser
import json
import re
import numpy as np
import pandas as pd
from scipy.stats import false_discovery_control

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / 'experiments/reviewer2_concern5/prepared_retrieval_20261102'
A = PLAN / 'analysis'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.details = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.extend(v for k, v in attrs if k == 'href')
        if tag == 'details':
            self.details += 1


def main():
    proof = json.loads((A / 'verification.json').read_text())
    for path, digest in {**proof['inputs'], **proof['outputs']}.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    e = pd.read_csv(A / 'sari_contrasts.csv')
    d = pd.read_csv(A / 'descriptive_comparisons.csv')
    z = np.load(A / 'bootstrap_draws.npz')
    assert z['effects'].shape == (10000, 36)
    np.testing.assert_allclose(np.quantile(z['effects'], [.025, .975], axis=0), e[['bootstrap_ci_low', 'bootstrap_ci_high']].to_numpy().T)
    for family, group in e.groupby('family'):
        assert len(group) == 18
        np.testing.assert_allclose(false_discovery_control(group.p, method='bh'), group.q_bh)
    for r in e.itertuples():
        cell = d[(d.model == r.model) & (d.dataset == r.dataset) & (d.prompt == r.prompt)].set_index('strategy')
        comparator = 'few_metric' if r.family == 'retrieval_minus_metric' else 'few_random_mean'
        assert np.isclose(r.effect, cell.loc['few_retrieval', 'SARI'] - cell.loc[comparator, 'SARI'])
    manifest = json.loads((PLAN / 'experiment_manifest.json').read_text())
    for j in manifest['jobs']:
        stem = f"{j['dataset']}_{j['prompt']}"
        new = pd.read_csv(PLAN / 'evaluation' / j['model'] / (stem + '_few_retrieval_items.csv'), keep_default_na=False, dtype={'text_id': str})
        for seed in [42, 44, 46]:
            old = pd.read_csv(ROOT / f"experiments/reviewer2_concern2/evaluation/metrics/{j['model']}/seed_{seed}/{stem}_few_random_items.csv", keep_default_na=False, dtype={'text_id': str})
            assert new.text_id.tolist() == old.text_id.tolist()
            assert [sorted(json.loads(v)) for v in new.references_json] == [sorted(json.loads(v)) for v in old.references_json]
        folder = A / 'error_analysis' / j['model'] / j['dataset']
        filename = Path(j['prediction_path']).stem
        all_items = pd.read_csv(folder / (filename + '_all_items.csv'), keep_default_na=False, dtype={'text_id': str})
        low = pd.read_json(folder / (filename + '_lowest_sari.json'), dtype={'text_id': str})
        assert all_items.row_index.tolist() == list(range(j['n']))
        assert low.row_index.tolist() == all_items.nsmallest(15, 'SARI', keep='first').row_index.tolist()
        for suffix, count in [('_all.html', j['n']), ('_lowest_sari.html', 15)]:
            path = folder / (filename + suffix)
            parser = Links()
            parser.feed(path.read_text(encoding='utf-8'))
            assert parser.details == count
            for link in parser.links:
                assert (path.parent / link).resolve().is_file(), link
    for path in (A / 'error_analysis').rglob('*.html'):
        parser = Links()
        parser.feed(path.read_text(encoding='utf-8'))
        for link in parser.links:
            assert (path.parent / link).resolve().is_file()
    labels = []
    for path in (PLAN / 'manuscript_proposals').rglob('*.tex'):
        labels.extend(re.findall(r'\\label\{([^}]+)\}', path.read_text()))
    assert len(labels) == len(set(labels))
    result = dict(status='passed', reference_pairing_checks=54, paired_effects_checked=36,
                  bh_families_checked=2, bootstrap_intervals_checked=36, full_reports=18,
                  low_sari_reports=18, all_html_links_resolve=True, unique_latex_labels=True,
                  input_output_hashes_match=True, new_inference_calls=0)
    (PLAN / 'DELIVERY_QA.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
