"""Use the existing six-metric evaluator with the new validated study inputs."""
import argparse
import importlib.util
from prepared_study import HERE,ROOT,PLAN,validate,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',choices=['llama','mixtral'])
    parser.add_argument('--dataset',choices=['cochrane','plaba','tsar2025'])
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('prepared_retrieval_metrics',HERE/'evaluate_retrieval.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.HERE=PLAN;module.ROOT=ROOT;module.validate=validate;module.sha=sha
    module.evaluate(args.model,args.dataset,args.execute)


if __name__=='__main__':main()
