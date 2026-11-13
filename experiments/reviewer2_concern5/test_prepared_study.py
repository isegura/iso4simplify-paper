import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import prepared_study as s


class PreparedStudyTests(unittest.TestCase):
    def test_pilot_resume_completion_and_tamper_guard(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);plan=root/'plan';plan.mkdir()
            (root/'model_utils.py').write_text('# mock inference source')
            (root/'instructions.md').write_text('Mock instructions')
            test=pd.DataFrame([dict(text_id=str(i),original=f'source {i}',reference=f'reference {i}') for i in range(4)])
            test.to_csv(root/'test.csv',index=False)
            pd.DataFrame([dict(dataset='tsar2025',prompt='minimal',row_index=i,prompt_path='instructions.md',instructions_sha256=s.sha(root/'instructions.md')) for i in range(4)]).to_csv(plan/'prompt_index.csv',index=False)
            pd.DataFrame([dict(model='llama',dataset='tsar2025',prompt='minimal',row_index=i,prompt_tokens=100) for i in range(4)]).to_csv(plan/'token_counts.csv',index=False)
            pd.DataFrame([dict(dataset='tsar2025',test_row_index=i,rank=k,training_row_index=k,training_text_id=f'demo{k}',cosine_similarity=.5,reference_cefr='a2') for i in range(4) for k in range(3)]).to_csv(plan/'selected_examples.csv',index=False)
            job=dict(job_id='mock_job',model='llama',ollama_model='mock',dataset='tsar2025',prompt='minimal',n=4,test_path='test.csv',prediction_path='plan/predictions/test.csv')
            manifest={'jobs':[job]};(plan/'experiment_manifest.json').write_text(json.dumps(manifest))
            calls=[]
            def mock(**kwargs):
                calls.append(kwargs['texto'])
                return 'simplified',0,0,0,dict(prompt_eval_count=100,done_reason='stop',eval_count=1)
            with patch.object(s,'ROOT',root),patch.object(s,'PLAN',plan),patch.object(s,'validate',return_value=manifest):
                s.run('llama','tsar2025',True,limit=2,generator=mock)
                marker=plan/'logs/llama/mock_job.complete.json'
                self.assertFalse(marker.exists());self.assertEqual(len(calls),2)
                s.run('llama','tsar2025',True,generator=mock)
                self.assertEqual(len(calls),4);self.assertTrue(marker.exists())
                s.run('llama','tsar2025',True,generator=mock)
                self.assertEqual(len(calls),4)
                output=plan/'predictions/test.csv';output.write_text(output.read_text().replace('simplified','altered'))
                with self.assertRaises(ValueError):s.run('llama','tsar2025',True,generator=mock)
                # A server-side prompt-count discrepancy is preserved and stops the pilot;
                # it cannot be silently accepted on resume or certified complete.
                manifest['jobs']=[dict(job,job_id='warning_job',prediction_path='plan/predictions/warning.csv')]
                def mismatch(**kwargs):return 'saved for inspection',0,0,0,dict(prompt_eval_count=99,done_reason='stop',eval_count=1)
                with self.assertRaises(RuntimeError):s.run('llama','tsar2025',True,limit=2,generator=mismatch)
                self.assertEqual(len(pd.read_csv(plan/'predictions/warning.csv')),1)
                self.assertFalse((plan/'logs/llama/warning_job.complete.json').exists())
                with self.assertRaises(ValueError):s.run('llama','tsar2025',True,limit=2,generator=mismatch)


if __name__=='__main__':unittest.main()
