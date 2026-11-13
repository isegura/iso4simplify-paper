"""Pin the earlier MeaningBERT implementation for focused evaluation only."""
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "experiments/focused_ablation"
MODULE = BASE / "metric_sources/meaningbert_original/meaningbert_original.py"


def configure():
    # Use the installed, smoke-tested snapshots; never resolve newer remote defaults.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    provenance = json.loads((BASE / "metric_sources/provenance.json").read_text(encoding="utf-8"))
    if hashlib.sha256(MODULE.read_bytes()).hexdigest() != provenance["sha256"]:
        raise ValueError("Pinned MeaningBERT implementation has changed")
    from huggingface_hub.constants import HF_HUB_CACHE
    cache = Path(HF_HUB_CACHE) / "models--davebulaval--MeaningBERT"
    revision = (cache / "refs/main").read_text().strip()
    if revision != provenance["model_revision"]:
        raise ValueError("MeaningBERT cached checkpoint changed; refusing to resolve another version")
    snapshot = cache / "snapshots" / revision
    for name, key in (("config.json", "model_config_sha256"), ("model.safetensors", "model_weights_sha256")):
        with (snapshot / name).open("rb") as handle:
            if hashlib.file_digest(handle, "sha256").hexdigest() != provenance[key]:
                raise ValueError(f"MeaningBERT checkpoint file changed: {name}")
    import evaluate
    import eval_utils

    @lru_cache(maxsize=1)
    def pinned_meaningbert():
        return evaluate.load(str(MODULE))

    eval_utils.get_meaningbert_metric = pinned_meaningbert
    return provenance
