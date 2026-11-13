"""End-to-end synthetic assembly/analysis. Never reads real predictions."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

import run_statistics as runner
from prepare_statistics import configurations, build_contrasts


class RunnerTests(unittest.TestCase):
    def test_complete_synthetic_pipeline_and_missing_guard(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporary:
            root = Path(temporary)
            here = root/'study'
            plan = here/'statistics_plan'
            plan.mkdir(parents=True)
            cells = configurations()
            contrasts = build_contrasts(cells)
            metadata = []
            for dataset in cells.dataset.unique():
                folder = root/'data'/dataset
                folder.mkdir(parents=True)
                test = pd.DataFrame(dict(text_id=['A', 'A', 'B'], original=['same', 'same', 'other'],
                                         reference=['first', 'second', 'third']))
                test.to_csv(folder/f'{dataset}_test.csv', index=False)
                for i, row in test.iterrows():
                    metadata.append(dict(dataset=dataset, row_index=i, text_id=row.text_id,
                        cluster_id=dataset+'/'+row.text_id,
                        source_sha256=runner.hashlib.sha256(row.original.encode()).hexdigest()))
            pd.DataFrame(metadata).to_csv(plan/'source_clusters.csv', index=False)
            audit = root/'audits/original_paper_statistics_20261022/methodology.json'
            audit.parent.mkdir(parents=True)
            historical_hashes = {}
            truth = []
            rng = np.random.default_rng(764)
            report = dict(rows=432, source_clusters=6)
            with patch.multiple(runner, ROOT=root, HERE=here, PLAN=plan, METRICS=here/'evaluation/metrics'), \
                 patch.object(runner, 'validate_plan', return_value=(cells, contrasts, report)):
                for cell in cells.to_dict('records'):
                    scores = rng.uniform(10, 60, size=3)
                    truth.append(scores.mean())
                    test = pd.read_csv(root/'data'/cell['dataset']/f"{cell['dataset']}_test.csv", keep_default_na=False)
                    if not cell['selection_seed']:
                        path = runner.fixed_prediction_path(cell)
                        path.parent.mkdir(parents=True, exist_ok=True)
                        test.assign(SARI=scores).to_csv(path, index=False)
                        historical_hashes[path.relative_to(root).as_posix()] = runner.sha(path)
                        continue
                    metadata_path, item_path = runner.metric_paths(cell)
                    item_path.parent.mkdir(parents=True, exist_ok=True)
                    item = pd.DataFrame(dict(row_index=range(3), text_id=test.text_id, SARI=scores))
                    for key in ['dataset', 'model', 'prompt', 'selection_seed']:
                        item[key] = cell[key]
                    item['strategy'] = cell['condition']
                    item.to_csv(item_path, index=False)
                    predicted = here/'predictions'/cell['model']/str(cell['selection_seed'])/(cell['cell_id'].replace('/', '_')+'.csv')
                    predicted.parent.mkdir(parents=True, exist_ok=True)
                    predicted.write_text('synthetic output only')
                    saved = dict(status='complete', items_sha256=runner.sha(item_path),
                        record={key: cell[key] for key in ['dataset', 'model', 'prompt', 'selection_seed']},
                        fingerprint={'inputs': {predicted.relative_to(root).as_posix(): runner.sha(predicted)}, 'code': {}})
                    saved['record'].update(strategy=cell['condition'], n=3, SARI=float(scores.mean()))
                    metadata_path.write_text(json.dumps(saved))
                    if cell['selection_seed'] != 42:
                        job = f"{cell['model']}_seed{cell['selection_seed']}_{cell['dataset']}_{cell['prompt']}_{cell['condition']}"
                        marker = here/'logs'/cell['model']/f"seed_{cell['selection_seed']}"/(job+'.complete.json')
                        marker.parent.mkdir(parents=True, exist_ok=True)
                        marker.write_text(json.dumps(dict(status='complete', rows=3, prediction_sha256=runner.sha(predicted))))
                audit.write_text(json.dumps({'source_hashes': historical_hashes}))
                _, _, groups, sums, counts, hashes = runner.assemble()
                self.assertEqual(sums.shape, (6, 144))
                self.assertEqual(int(counts.sum()), 432)
                # Two source rows with ID A stay in the same document cluster.
                self.assertEqual(int(counts[0].max()), 2)
                estimates, effects, covariance, draws = runner.analyze(cells, contrasts, groups, sums, counts, repetitions=256)
                np.testing.assert_allclose(estimates.SARI.to_numpy(), truth)
                self.assertEqual(len(effects), 43)
                self.assertEqual(draws.shape, (256, 43))
                self.assertEqual(covariance.shape, (144, 144))
                self.assertTrue(effects.q_bh.between(0, 1).all())
                self.assertTrue(effects.bootstrap_ci_low.le(effects.bootstrap_ci_high).all())
                self.assertTrue(hashes)
                # No metric/prediction reads if the required evaluation is incomplete.
                runner.metric_paths(cells[cells.selection_seed == 46].iloc[0].to_dict())[1].unlink()
                with patch.object(pd, 'read_csv', side_effect=AssertionError('Should not open outcomes')):
                    with self.assertRaisesRegex(ValueError, 'Complete all metric evaluations first'):
                        runner.assemble()


if __name__ == '__main__':
    unittest.main()
