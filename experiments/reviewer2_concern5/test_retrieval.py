import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
import study
import evaluate_retrieval
from retrieval_engine import select_three, normalized, encode_full_sources


class RetrievalTests(unittest.TestCase):
    def test_evaluation_gate_and_tsar_joint_references(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporary:
            root = Path(temporary);here = root/'retrieval';here.mkdir()
            job = dict(job_id='llama_tsar2025_iso_few_retrieval',model='llama',dataset='tsar2025',n=2,
                       prediction_path='retrieval/predictions.csv',test_path='test.csv')
            with patch.multiple(evaluate_retrieval, ROOT=root,HERE=here):
                with self.assertRaisesRegex(ValueError,'not certified complete'):
                    evaluate_retrieval.load_job(job)
                test = pd.DataFrame(dict(text_id=['21','22'],original=['source one','source two'],reference=['a','b']))
                test.to_csv(root/'test.csv',index=False)
                pred = root/job['prediction_path']
                test.assign(prediction=['output',''],context_budget_observed_warning=False).to_csv(pred,index=False)
                marker = here/'logs/llama'/(job['job_id']+'.complete.json')
                marker.parent.mkdir(parents=True)
                marker.write_text(json.dumps(dict(status='complete',rows=2,prediction_sha256=study.sha(pred))))
                gold_dir = root/'data/tsar2025';gold_dir.mkdir(parents=True)
                pd.DataFrame(dict(text_id=['21-a2','21-b1','22-a2','22-b1'],
                    original=['source one','source one','source two','source two'],
                    reference=['a2 first','b1 first','a2 second','b1 second'])).to_csv(gold_dir/'tsar2025_test_200.csv',index=False)
                loaded,refs,_ = evaluate_retrieval.load_job(job)
                self.assertEqual(refs,[['a2 first','b1 first'],['a2 second','b1 second']])
                self.assertEqual(loaded.prediction.tolist(),['output',''])
                pred.write_text('tampered')
                with self.assertRaisesRegex(ValueError,'certificate mismatch'):
                    evaluate_retrieval.load_job(job)

    def test_ranking_distinct_documents_and_no_self_match(self):
        pool = pd.DataFrame(dict(training_row_index=[0,1,2,3,4,5],text_id=['A','B','B','C','D','target'],
            original=['self','b','duplicate document','c','d','different source same target ID']))
        chosen = select_three(np.array([1.,.8,.9,.8,.7,.99]),pool,'self','target','plaba')
        self.assertEqual([i for i,_ in chosen],[2,3,4])
        self.assertEqual(normalized('  TEXT\nExample '), normalized('text example'))

    def test_full_source_chunk_pooling(self):
        class Tokenizer:
            def encode(self,text,add_special_tokens=False,**kwargs):
                ids = [int(x) for x in text.split()]
                return ids + ([0,0] if add_special_tokens else [])
            def decode(self,ids,**kwargs):
                return ' '.join(map(str,ids))
        class Encoder:
            tokenizer = Tokenizer()
            max_seq_length = 256
            def encode(self,chunks,**kwargs):
                vectors = np.array([[len(chunk.split()),1.] for chunk in chunks])
                return vectors/np.linalg.norm(vectors,axis=1,keepdims=True)
        vectors,lengths,n_chunks = encode_full_sources(Encoder(),[' '.join(map(str,range(500))),'1 2 3'])
        np.testing.assert_array_equal(lengths,[500,3])
        np.testing.assert_array_equal(n_chunks,[3,1])
        np.testing.assert_allclose(np.linalg.norm(vectors,axis=1),[1,1],atol=1e-6)

    def test_generation_checkpoint_resume_and_context_guard(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporary:
            root = Path(temporary);here = root/'retrieval';here.mkdir()
            (root/'model_utils.py').write_text('synthetic only')
            (here/'experiment_manifest.json').write_text('{}')
            frame = pd.DataFrame(dict(text_id=['T1','T2'],original=['source one','source two'],reference=['ref one','ref two']))
            frame.to_csv(root/'test.csv',index=False)
            jobs, entries, examples = [], [], []
            for prompt in ['minimal','iso','iso_examples']:
                path = here/f'{prompt}.md';path.write_text('synthetic instructions')
                jobs.append(dict(job_id=prompt,model='llama',dataset='cochrane',prompt=prompt,n=2,
                    ollama_model='llama3.1:8b',test_path='test.csv',prediction_path=f'retrieval/predictions/{prompt}.csv'))
                for i in range(2):
                    entries.append(dict(dataset='cochrane',prompt=prompt,row_index=i,prompt_path=path.relative_to(root).as_posix()))
            for i in range(2):
                for rank in range(1,4):
                    examples.append(dict(dataset='cochrane',test_row_index=i,test_text_id=f'T{i}',rank=rank,
                        training_row_index=rank,training_text_id=f'E{rank}',cosine_similarity=.9-rank*.1))
            pd.DataFrame(entries).to_csv(here/'prompt_index.csv',index=False)
            pd.DataFrame(examples).to_csv(here/'selected_examples.csv',index=False)
            counter = [0]
            def generator(**kwargs):
                counter[0] += 1
                if counter[0] == 2:
                    raise RuntimeError('simulated interruption')
                return '',0,0,0,dict(done_reason='stop',prompt_eval_count=100,eval_count=0)
            manifest = {'jobs':jobs}
            with patch.multiple(study, ROOT=root,HERE=here), patch.object(study,'validate',return_value=manifest):
                with self.assertRaisesRegex(RuntimeError,'simulated interruption'):
                    study.run('llama',execute=True,generator=generator)
                study.run('llama',execute=True,generator=generator)
                self.assertEqual(counter[0],7)  # six stored outputs plus failed request
                study.run('llama',execute=True,generator=generator)
                self.assertEqual(counter[0],7)
                self.assertTrue(pd.read_csv(root/jobs[0]['prediction_path'],keep_default_na=False).prediction.eq('').all())
                # Separate unfinished synthetic job records an over-budget output and refuses resume.
                extra = dict(jobs[0],job_id='warning',prediction_path='retrieval/predictions/warning.csv')
                manifest['jobs'] = [extra]
                def over_budget(**kwargs):
                    return 'output',0,0,0,dict(done_reason='stop',prompt_eval_count=8000,eval_count=1)
                with self.assertRaisesRegex(RuntimeError,'exceed context'):
                    study.run('llama',execute=True,generator=over_budget)
                with self.assertRaisesRegex(ValueError,'saved output has a context warning'):
                    study.run('llama',execute=True,generator=over_budget)


if __name__ == '__main__':
    unittest.main()
