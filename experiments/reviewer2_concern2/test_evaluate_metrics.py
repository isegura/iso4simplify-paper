"""Isolated contract checks: synthetic data are never research predictions."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import pandas as pd

spec = importlib.util.spec_from_file_location('seed_metrics', Path(__file__).with_name('evaluate_metrics.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class EvaluationContracts(unittest.TestCase):
    def test_corpus_bleu_and_empty_items(self):
        items = pd.DataFrame({metric: [10., 0.] for metric in m.ITEM_METRICS})
        scores, signature = m.aggregate(items, ['a simple sentence .', ''], [['a simple sentence .'], ['another sentence .']])
        from sacrebleu import corpus_bleu
        self.assertEqual(scores['BLEU'], corpus_bleu(['a simple sentence .', ''], [['a simple sentence .', 'another sentence .']]).score)
        self.assertEqual(scores['SARI'], 5.)
        self.assertIn('tok:13a', signature)

    def test_compute_passes_joint_references_and_source(self):
        refs = [['simple a', 'simple b'], ['other a', 'other b']]
        frame = pd.DataFrame(dict(original=['source one', 'source two'], prediction=['text', '']))
        calls = []
        class Sari:
            def compute(self, **kwargs):
                calls.append(kwargs)
                return {'sari': 12.345}
        def bert(predictions, references, **kwargs):
            self.assertEqual(references, refs)
            return {'BERTScore-F1': [.8, 0.]}
        def meaning(predictions, sources, **kwargs):
            self.assertEqual(sources, ['source one', 'source two'])
            return [50., 0.]
        stub = types.SimpleNamespace(get_sari_metric=lambda: Sari(), compute_bertscore=bert, compute_meaningbert=meaning)
        with patch.dict(sys.modules, {'eval_utils': stub}):
            items = m.compute_items(frame, refs)
        self.assertEqual(len(items), 2)
        self.assertEqual(items.SARI.tolist(), [12.35, 12.35])
        self.assertEqual(calls[1]['predictions'], [''])
        self.assertEqual(calls[0]['references'], [refs[0]])

    def test_completion_guard_and_three_seed_summary(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporary:
            root = Path(temporary)
            here = root / 'study'
            here.mkdir()
            frame = pd.DataFrame(dict(text_id=['1', '2'], original=['source', 'other'], reference=['ref', 'ref2'], prediction=['out', ''], done_reason=['stop', 'length']))
            test = root / 'test.csv'
            frame[['text_id', 'original', 'reference']].to_csv(test, index=False)
            jobs = []
            for seed in (44, 46):
                pred = root / f'pred_{seed}.csv'
                frame.to_csv(pred, index=False)
                jobs.append(dict(model='llama', dataset='cochrane', prompt='iso', strategy='one', selection_seed=seed,
                    job_id=f'job_{seed}', n=2, prediction_path=pred.name, test_path=test.name, historical_prediction_path='historical.csv'))
            manifest = dict(jobs=jobs, source_sha256={'test.csv': m.sha(test)})
            (here / 'experiment_manifest.json').write_text(json.dumps(manifest))
            with patch.multiple(m, ROOT=root, HERE=here, DEST=here/'evaluation'):
                with self.assertRaisesRegex(ValueError, 'not certified complete'):
                    m.load_job(jobs[0], 44)
                marker = here / 'logs/llama/seed_44/job_44.complete.json'
                m.save_json(marker, dict(status='complete', rows=2, prediction_sha256=m.sha(root/'pred_44.csv')))
                loaded, refs, hashes = m.load_job(jobs[0], 44)
                self.assertEqual(len(loaded), 2)
                self.assertEqual(refs, [['ref'], ['ref2']])
                for seed, value in ((42, 1.), (44, 2.), (46, 3.)):
                    folder = m.DEST / 'llama' / f'seed_{seed}'
                    folder.mkdir(parents=True)
                    item = folder/'cochrane_iso_one_items.csv'
                    item.write_text('synthetic only')
                    record = dict(model='llama', dataset='cochrane', prompt='iso', strategy='one', selection_seed=seed, n=2,
                                  **{metric: value for metric in m.METRICS})
                    m.save_json(folder/'cochrane_iso_one.json', dict(status='complete', record=record, items_sha256=m.sha(item), fingerprint={'inputs': hashes}))
                    if seed == 44:
                        with self.assertRaisesRegex(ValueError, 'All three evaluated seeds'):
                            m.summarize('llama', 'cochrane')
                m.summarize('llama', 'cochrane')
                summary = pd.read_csv(m.DEST/'summaries/llama_cochrane_mean_sd.csv')
                self.assertEqual(len(summary), 6)
                self.assertTrue(summary['mean'].eq(2.).all())
                self.assertTrue(summary.sd.eq(1.).all())
                (root/'pred_44.csv').write_text('tampered')
                with self.assertRaisesRegex(ValueError, 'certificate mismatch'):
                    m.load_job(jobs[0], 44)


if __name__ == '__main__':
    unittest.main()
