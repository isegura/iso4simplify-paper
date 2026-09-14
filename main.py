import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import gc
import requests
import torch
from tqdm import tqdm
from transformers import data, logging as hf_logging

from data_utils import (
    append_prediction,
    build_output_path,
    initialize_output_csv,
    load_dataset,
    load_prompt,
    save_outputs,
)
from logger_utils import log_gpu_info, log_run_summary, setup_logger
from model_utils import get_ollama_model_runtime_info, load_model_and_tokenizer, resolve_input_device, simplify_one
# from eval import evaluate

hf_logging.set_verbosity_error()
gc.collect()
torch.cuda.empty_cache()
torch.backends.cuda.matmul.allow_tf32 = True
torch.set_float32_matmul_precision("high")


# =========================================================
# CONFIGURACIÓN DEL EXPERIMENTO
# =========================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
PROMPT_DIR = PROJECT_DIR / "prompts"
OUTPUTS_DIR = PROJECT_DIR / "outputs"
LOGS_DIR = PROJECT_DIR / "logs"
EVAL_LANG = "en"

# MODEL_NAME = "google/gemma-3-27b-it"
# google/gemma-3-27b-it
    # meta-llama/Llama-3.1-8B
    # mistralai/Ministral-3-14B-Instruct-2512

BACKEND = "hf"          # "hf", "ollama"
HF_TOKEN_ENV = "HF_TOKEN"
MODEL_NAME = "mistralai/Ministral-3-14B-Instruct-2512"

DATASET_NAME = "cochrane"          # "cochrane", "plaba", "tsar2025"
PROMPT_TYPE = "iso_examples"            # "minimal", "iso", "iso_examples"
STRATEGY = "few"                   # "zero", "one", "few"
SAMPLING_METHOD = "metric"        # None, "random", "metric"

ID_COL = "text_id"
SOURCE_COL = "original"
REF_COL = "reference"

MARKER = "SIMPLIFIED TEXT:"
MAX_INPUT_TOKENS = 4096
MAX_NEW_TOKENS = 512
OLLAMA_NUM_CTX = 8192
OLLAMA_TEMPERATURE = 0.0
OLLAMA_SEED = 42
OLLAMA_TOP_K = 1
OLLAMA_TOP_P = 1.0
OLLAMA_REPEAT_PENALTY = 1.1
OLLAMA_REPEAT_LAST_N = 64
OLLAMA_NUM_GPU = 999
OLLAMA_REQUIRE_GPU = True
OLLAMA_TIMEOUT = 900
HEAD_N = None
SHOW_DATASET_INFO = False
PREFER_INPUT_DEVICE = "cuda:0"

import requests

def ollama_device():
    data = requests.get("http://localhost:11434/api/ps").json()
    models = data.get("models", [])
    
    if not models:
        return "cpu"
    
    return "gpu" if models[0].get("size_vram", 0) > 0 else "cpu"

def build_prompt_map(dataset_name: str, prompt_type: str, sampling_method: str) -> Dict[str, str]:
    return {
        "zero": f"{prompt_type}_zero.md",
        "one": f"{dataset_name}_{prompt_type}_one.md",
        "few": f"{dataset_name}_{prompt_type}_few_{sampling_method}.md",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default=BACKEND)
    parser.add_argument("--model", default=MODEL_NAME)
    parser.add_argument("--dataset", default=DATASET_NAME)
    parser.add_argument("--type_prompt", default=PROMPT_TYPE)
    parser.add_argument("--strategy", default=STRATEGY)
    parser.add_argument("--sampling_method", default=SAMPLING_METHOD)
    parser.add_argument("--head", type=int, default=HEAD_N)
    parser.add_argument("--outputs_dir", type=Path, default=OUTPUTS_DIR)
    parser.add_argument("--max_new_tokens", type=int, default=MAX_NEW_TOKENS)
    parser.add_argument("--ollama_num_ctx", type=int, default=OLLAMA_NUM_CTX)
    parser.add_argument("--ollama_temperature", type=float, default=OLLAMA_TEMPERATURE)
    parser.add_argument("--ollama_seed", type=int, default=OLLAMA_SEED)
    parser.add_argument("--ollama_top_k", type=int, default=OLLAMA_TOP_K)
    parser.add_argument("--ollama_top_p", type=float, default=OLLAMA_TOP_P)
    parser.add_argument("--ollama_repeat_penalty", type=float, default=OLLAMA_REPEAT_PENALTY)
    parser.add_argument("--ollama_repeat_last_n", type=int, default=OLLAMA_REPEAT_LAST_N)
    parser.add_argument("--ollama_num_gpu", type=int, default=OLLAMA_NUM_GPU)
    parser.add_argument(
        "--ollama_require_gpu",
        action=argparse.BooleanOptionalAction,
        default=OLLAMA_REQUIRE_GPU,
    )
    parser.add_argument("--ollama_timeout", type=int, default=OLLAMA_TIMEOUT)
    return parser.parse_args()


def log_config(logger, args: argparse.Namespace, dataset_path: Path, prompt_file: str) -> None:
    logger.info("=== CONFIG ===")
    logger.info(f"Backend: {args.backend}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Dataset: {dataset_path}")
    logger.info(f"Prompt type: {args.type_prompt}")
    logger.info(f"Strategy: {args.strategy}")
    logger.info(f"Prompt file: {prompt_file}")
    logger.info(f"Outputs dir: {args.outputs_dir}")
    if args.strategy == "few":
        logger.info(f"Sampling method: {args.sampling_method}")
    logger.info(f"Head: {args.head}")
    logger.info(f"Max new tokens: {args.max_new_tokens}")
    if args.backend == "hf":
        logger.info(f"Max input tokens: {MAX_INPUT_TOKENS}")
    if args.backend == "ollama":
        logger.info(f"Ollama num_ctx: {args.ollama_num_ctx}")
        logger.info(f"Ollama temperature: {args.ollama_temperature}")
        logger.info(f"Ollama seed: {args.ollama_seed}")
        logger.info(f"Ollama top_k: {args.ollama_top_k}")
        logger.info(f"Ollama top_p: {args.ollama_top_p}")
        logger.info(f"Ollama repeat_penalty: {args.ollama_repeat_penalty}")
        logger.info(f"Ollama repeat_last_n: {args.ollama_repeat_last_n}")
        logger.info(f"Ollama num_gpu: {args.ollama_num_gpu}")
        logger.info(f"Ollama require_gpu: {args.ollama_require_gpu}")
        logger.info(f"Ollama timeout: {args.ollama_timeout}")
        runtime_info = get_ollama_model_runtime_info(args.model)
        size_vram = int(runtime_info.get("size_vram") or 0)
        logger.info(f"Ollama runtime device before run: {'gpu' if size_vram > 0 else 'cpu_or_not_loaded'}")
        logger.info(f"Ollama runtime size_vram before run: {size_vram}")
    logger.info("================")


def run_dataset(
    df,
    backend: str, 
    instrucciones: str,
    model,
    tokenizer,
    model_name: str, 
    max_input_tokens: int,
    max_new_tokens: int,
    ollama_num_ctx: int | None,
    ollama_temperature: float | None,
    ollama_seed: int | None,
    ollama_top_k: int | None,
    ollama_top_p: float | None,
    ollama_repeat_penalty: float | None,
    ollama_repeat_last_n: int | None,
    ollama_num_gpu: int | None,
    ollama_require_gpu: bool,
    source_col: str,
    marker: str,
    ollama_timeout: int,
    output_path: Path,
    prefer_input_device: str,
    logger,
):
    
    texts = df[source_col].astype(str).tolist()
    logger.info(f"Starting inference on {len(texts)} texts")
  

    if backend == "ollama":
        input_device = "ollama"
        logger.info("Ollama backend active; GPU usage will be checked after generation.")
    else:
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            input_device = torch.device(prefer_input_device)
        else:   
            input_device = torch.device("cpu")
    
    logger.info(f"Input device: {input_device}")


    t_dataset_start = time.perf_counter()

    textos_simplificados: List[str] = []
    metadata_rows: List[Dict[str, Any]] = []
    new_tok_sum = 0
    t_infer_sum = 0.0


    pbar = tqdm(texts, desc="Inferencia", unit="text")

    for i, texto in enumerate(pbar, start=1):
        simplified, in_toks, new_toks, elapsed_s, metadata = simplify_one(
            backend = backend, 
            texto=texto,
            instrucciones=instrucciones,
            model=model,
            tokenizer=tokenizer,
            model_name = model_name, 
            input_device=input_device,
            max_input_tokens=max_input_tokens,
            max_new_tokens=max_new_tokens,
            marker=marker,
            ollama_num_ctx=ollama_num_ctx,
            ollama_temperature=ollama_temperature,
            ollama_seed=ollama_seed,
            ollama_top_k=ollama_top_k,
            ollama_top_p=ollama_top_p,
            ollama_repeat_penalty=ollama_repeat_penalty,
            ollama_repeat_last_n=ollama_repeat_last_n,
            ollama_num_gpu=ollama_num_gpu,
            ollama_require_gpu=ollama_require_gpu,
            ollama_timeout=ollama_timeout,
        )

        textos_simplificados.append(simplified)
        metadata_rows.append(metadata)
        append_prediction(output_path, df.iloc[i - 1], simplified, metadata)
        new_tok_sum += new_toks
        t_infer_sum += elapsed_s

        if backend == "ollama" and i == 1:
            runtime_info = get_ollama_model_runtime_info(model_name)
            size_vram = int(runtime_info.get("size_vram") or 0)
            runtime_device = "gpu" if size_vram > 0 else "cpu"
            logger.info(f"Ollama runtime device after first generation: {runtime_device}")
            logger.info(f"Ollama runtime size_vram after first generation: {size_vram}")

        if i % 10 == 0 or i == len(texts):
            avg_s = t_infer_sum / i
            txt_per_s = i / t_infer_sum if t_infer_sum > 0 else 0.0
            tok_per_s = new_tok_sum / t_infer_sum if t_infer_sum > 0 else 0.0

            pbar.set_postfix({
                "avg_s/text": f"{avg_s:.2f}",
                "texts/s": f"{txt_per_s:.2f}",
                "new_tok/s": f"{tok_per_s:.1f}",
            })

            logger.info(
                f"progress | step={i}/{len(texts)} | "
                f"avg_s/text={avg_s:.2f} | "
                f"texts/s={txt_per_s:.2f} | "
                f"new_tok/s={tok_per_s:.1f} | "
                f"last_in_tokens={in_toks} | "
                f"last_new_tokens={new_toks}"
            )

    t_total = time.perf_counter() - t_dataset_start
    logger.info(f"Dataset inference finished in {t_total:.2f} s")

    stats = {
        "n_texts": len(textos_simplificados),
        "new_tokens": new_tok_sum,
        "total_inference_time": t_infer_sum,
        "dataset_wall_time": t_total,
    }

    return textos_simplificados, metadata_rows, stats


def main() -> None:
    args = parse_args()


    backend = args.backend
    dataset_path = DATA_DIR / args.dataset / f"{args.dataset}_test.csv"
    prompt_map = build_prompt_map(args.dataset, args.type_prompt, args.sampling_method)

    if args.strategy not in prompt_map:
        raise ValueError(
            f"Unknown strategy '{args.strategy}'. "
            f"Choose one of {list(prompt_map.keys())}"
        )

    prompt_file = prompt_map[args.strategy]

    model_short = args.model.split("/")[-1]
    run_name = (
        f"{model_short}_{args.dataset}_{args.type_prompt}_{args.strategy}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    logger = setup_logger(LOGS_DIR, run_name)
    log_config(logger, args, dataset_path, prompt_file)

    t_start = time.perf_counter()
    stats = {
        "n_texts": 0,
        "new_tokens": 0,
        "total_inference_time": 0.0,
    }

    try:

        logger.info("\n=== DATASET INFO ===")
        df = load_dataset(
            dataset_path=dataset_path,
            id_col=ID_COL,
            source_col=SOURCE_COL,
            ref_col=REF_COL,
            head_n=args.head,
            show_dataset_info=SHOW_DATASET_INFO,
        )
        logger.info(f"Dataset name: {args.dataset}")
        logger.info(f"Dataset path: {dataset_path}")
        logger.info(f"Dataset size: {df.shape}")
        logger.info("\n====================")

        logger.info("=== PROMPT INFO ===")
        prompt_path = PROMPT_DIR / prompt_file
        instrucciones = load_prompt(prompt_path=prompt_path)
        logger.info(f"Prompt path: {prompt_path}")
        logger.info(f"Prompt preview: {instrucciones[:120]}")
        logger.info("===================")

        logger.info("Loading model and tokenizer...")
        model, tokenizer = load_model_and_tokenizer(
            model_name=args.model,
            backend=args.backend,
            hf_token_env=HF_TOKEN_ENV,
        )
        if backend == "hf":
            log_gpu_info(logger)

            logger.info("=== MODEL INFO ===")
            logger.info(f"model device: {next(model.parameters()).device}")

        logger.info("=== SIMPLIFY===")
        out_path = build_output_path(
            outputs_dir=args.outputs_dir,
            model_name=args.model,
            dataset_name=args.dataset,
            prompt_type=args.type_prompt,
            strategy=args.strategy,
            sampling_method=args.sampling_method,
        )
        metadata_columns = ["wall_time_s"]
        if backend == "ollama":
            metadata_columns += [
                "done_reason",
                "eval_count",
                "prompt_eval_count",
                "total_duration",
                "load_duration",
                "prompt_eval_duration",
                "eval_duration",
                "total_duration_s",
                "prompt_eval_duration_s",
                "eval_duration_s",
                "prompt_tokens_per_s",
                "eval_tokens_per_s",
                "num_predict",
                "num_ctx",
            ]
        initialize_output_csv(df, out_path, extra_columns=metadata_columns)
        logger.info(f"Incremental predictions will be saved to: {out_path}")

        predictions, metadata_rows, stats = run_dataset(
            df=df,
            backend=backend,
            instrucciones=instrucciones,
            model=model,
            tokenizer=tokenizer,
            model_name=args.model,
            max_input_tokens=MAX_INPUT_TOKENS,
            max_new_tokens=args.max_new_tokens,
            ollama_num_ctx=args.ollama_num_ctx,
            ollama_temperature=args.ollama_temperature,
            ollama_seed=args.ollama_seed,
            ollama_top_k=args.ollama_top_k,
            ollama_top_p=args.ollama_top_p,
            ollama_repeat_penalty=args.ollama_repeat_penalty,
            ollama_repeat_last_n=args.ollama_repeat_last_n,
            ollama_num_gpu=args.ollama_num_gpu,
            ollama_require_gpu=args.ollama_require_gpu,
            source_col=SOURCE_COL,
            marker=MARKER,
            ollama_timeout=args.ollama_timeout,
            output_path=out_path,
            prefer_input_device=PREFER_INPUT_DEVICE,
            logger=logger,
        )
        logger.info(f"Predictions were generated")

        logger.info("=== SAVING OUTPUTS ===")
        out_path = save_outputs(
            df=df,
            predictions=predictions,
            metadata_rows=metadata_rows,
            outputs_dir=args.outputs_dir,
            model_name=args.model,
            dataset_name=args.dataset,
            prompt_type=args.type_prompt,
            strategy=args.strategy,
            sampling_method=args.sampling_method,
        )
        logger.info(f"Predictions saved to: {out_path}")

        # if args.backend == "hf":
        #     logger.info("=== EVALUATION ===")
        #     scores_df, score_path = evaluate(pred_path=out_path,lang=EVAL_LANG)
        #     logger.info(f"Scores saved to: {score_path}")
        #     logger.info(f"Scores row: {scores_df.to_dict(orient='records')[0]}")
        #     logger.info(f"Scores saved to: {score_path}")

    except Exception:
        logger.exception("Fatal error during experiment")
        raise

    finally:
        total_runtime = time.perf_counter() - t_start
        log_run_summary(
            logger=logger,
            n_texts=stats["n_texts"],
            total_runtime=total_runtime,
            total_inference_time=stats["total_inference_time"],
            new_tokens=stats["new_tokens"],
        )


if __name__ == "__main__":
    main()
