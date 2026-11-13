# Copyright 2020 The HuggingFace Evaluate Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" MeaningBERT metric. """

from contextlib import contextmanager
from itertools import chain
from typing import List, Dict

import datasets
import evaluate
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


@contextmanager
def filter_logging_context():
    def filter_log(record):
        return (
            False if "This IS expected if you are initializing" in record.msg else True
        )

    logger = datasets.utils.logging.get_logger("transformers.modeling_utils")
    logger.addFilter(filter_log)
    try:
        yield
    finally:
        logger.removeFilter(filter_log)


_CITATION = """\
@ARTICLE{10.3389/frai.2023.1223924,
AUTHOR={Beauchemin, David and Saggion, Horacio and Khoury, Richard},    
TITLE={MeaningBERT: assessing meaning preservation between sentences},      
JOURNAL={Frontiers in Artificial Intelligence},      
VOLUME={6},           
YEAR={2023},      
URL={https://www.frontiersin.org/articles/10.3389/frai.2023.1223924},       
DOI={10.3389/frai.2023.1223924},      
ISSN={2624-8212},   
}
"""

_DESCRIPTION = """\
MeaningBERT is an automatic and trainable metric for assessing meaning preservation between sentences. MeaningBERT was
proposed in our
article [MeaningBERT: assessing meaning preservation between sentences](https://www.frontiersin.org/articles/10.3389/frai.2023.1223924/full).
Its goal is to assess meaning preservation between two sentences that correlate highly with human judgments and sanity 
checks. For more details, refer to our publicly available article.

See the project's README at https://github.com/GRAAL-Research/MeaningBERT for more information.
"""

_KWARGS_DESCRIPTION = """
MeaningBERT metric for assessing meaning preservation between sentences.

Args:
    predictions (list of str): Predictions sentences.
    references (list of str): References sentences (same number of element as predictions).

Returns:
    score: the meaning score between two sentences in alist format respecting the order of the predictions and 
    references pairs.
    hashcode: Hashcode of the library.

Examples:

    >>> references = ["hello there", "general kenobi"]
    >>> predictions = ["hello there", "general kenobi"]
    >>> meaning_bert = evaluate.load("davebulaval/meaningbert")
    >>> results = meaning_bert.compute(predictions=predictions, references=references)
"""

_HASH = "21845c0cc85a2e8e16c89bb0053f489095cf64c5b19e9c3865d3e10047aba51b"


@evaluate.utils.file_utils.add_start_docstrings(_DESCRIPTION, _KWARGS_DESCRIPTION)
class MeaningBERT(evaluate.Metric):
    def _info(self):
        return evaluate.MetricInfo(
            description=_DESCRIPTION,
            citation=_CITATION,
            homepage="https://github.com/GRAAL-Research/MeaningBERT",
            inputs_description=_KWARGS_DESCRIPTION,
            features=[
                datasets.Features(
                    {
                        "predictions": datasets.Value("string", id="sequence"),
                        "references": datasets.Value("string", id="sequence"),
                    }
                )
            ],
            codebase_urls=["https://github.com/GRAAL-Research/MeaningBERT"],
            reference_urls=[
                "https://github.com/GRAAL-Research/MeaningBERT",
                "https://www.frontiersin.org/articles/10.3389/frai.2023.1223924/full",
            ],
            module_type="metric",
        )

    def _compute(
        self,
        predictions: List,
        references: List,
    ) -> Dict:
        assert len(references) == len(
            predictions
        ), "The number of references is different of the number of predictions."
        hashcode = _HASH

        # Index of sentence with perfect match between two sentences
        matching_index = [i for i, item in enumerate(references) if item in predictions]

        # We load the MeaningBERT pretrained model
        scorer = AutoModelForSequenceClassification.from_pretrained(
            "davebulaval/MeaningBERT"
        )
        scorer.eval()

        with torch.no_grad():
            # We load MeaningBERT tokenizer
            tokenizer = AutoTokenizer.from_pretrained("davebulaval/MeaningBERT")

            # We tokenize the text as a pair and return Pytorch Tensors
            tokenize_text = tokenizer(
                references,
                predictions,
                truncation=True,
                padding=True,
                return_tensors="pt",
            )

            with filter_logging_context():
                # We process the text
                scores = scorer(**tokenize_text)

            scores = scores.logits.tolist()

            # Flatten the list of list of logits
            scores = list(chain(*scores))

            # Handle case of perfect match
            if len(matching_index) > 0:
                for matching_element_index in matching_index:
                    scores[matching_element_index] = 100

            output_dict = {
                "scores": scores,
                "hashcode": hashcode,
            }
        return output_dict
