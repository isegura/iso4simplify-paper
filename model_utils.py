import os
import time
from typing import Any, Dict, Tuple
import requests


os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from transformers import Mistral3ForConditionalGeneration, MistralCommonBackend


import requests     # para trabajar con ollama

BACKEND_HF = "hf"
BACKEND_OLLAMA = "ollama"


def get_ollama_model_runtime_info(model_name: str, timeout: int = 10) -> Dict[str, Any]:
    try:
        response = requests.get("http://localhost:11434/api/ps", timeout=timeout)
        response.raise_for_status()
        models = response.json().get("models", [])
    except requests.RequestException:
        return {}

    for model in models:
        if model.get("name") == model_name or model.get("model") == model_name:
            return model
    return models[0] if models else {}


def pick_dtype() -> torch.dtype:
    if torch.cuda.is_available():
        major, _minor = torch.cuda.get_device_capability(0)
        if major >= 8:
            return torch.bfloat16
    return torch.float16


def load_model_and_tokenizer(model_name: str, backend : str = "hf", hf_token_env: str = "HF_TOKEN"):
    print(f"\nLoading model and tokenizer for {model_name}..."  )
    print(backend)
    if backend == "ollama":
        return None, None
        
    token = os.environ.get(hf_token_env)

    print("\nMODEL:", model_name)

    if "Ministral-3" in model_name or "ministral-3" in model_name:
        tokenizer = MistralCommonBackend.from_pretrained(model_name)

        model = Mistral3ForConditionalGeneration.from_pretrained(
            model_name,
            token=token,
            device_map="auto",
            low_cpu_mem_usage=True,
        )

        model.eval()
        return model, tokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name, token=token)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        token=token,
        device_map="auto",
        quantization_config=bnb,
        low_cpu_mem_usage=True,
    )

    model.eval()
    return model, tokenizer

def resolve_input_device(prefer_input_device: str = "cuda:0") -> torch.device:
    if torch.cuda.is_available():
        return torch.device(prefer_input_device)
    return torch.device("cpu")


def simplify_one_ollama(
    texto: str,
    instrucciones: str,
    model_name: str,
    marker: str,
    max_new_tokens: int = 256,
    num_ctx: int | None = None,
    temperature: float | None = None,
    seed: int | None = None,
    top_k: int | None = None,
    top_p: float | None = None,
    repeat_penalty: float | None = None,
    repeat_last_n: int | None = None,
    num_gpu: int | None = None,
    require_gpu: bool = False,
    timeout: int = 300,
) -> tuple[str, int, int, float, Dict[str, Any]]:

    t0 = time.perf_counter()

    prompt = (
        f"{instrucciones}\n\n"
        "# TARGET TEXT\n\n"
        f'"""\n{texto}\n"""\n\n'
        "# ANSWER\n"
        "Write the simplified version below and nothing else.\n"
    )

    options = {
        "num_predict": max_new_tokens,
    }
    if num_ctx is not None:
        options["num_ctx"] = num_ctx
    if temperature is not None:
        options["temperature"] = temperature
    if seed is not None:
        options["seed"] = seed
    if top_k is not None:
        options["top_k"] = top_k
    if top_p is not None:
        options["top_p"] = top_p
    if repeat_penalty is not None:
        options["repeat_penalty"] = repeat_penalty
    if repeat_last_n is not None:
        options["repeat_last_n"] = repeat_last_n
    if num_gpu is not None:
        options["num_gpu"] = num_gpu

    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": options,
    }

    r = requests.post(
        "http://localhost:11434/api/chat",
        json=payload,
        timeout=timeout
    )

    r.raise_for_status()

    data = r.json()

    output = data["message"]["content"].strip()

    elapsed = time.perf_counter() - t0
    prompt_eval_count = int(data.get("prompt_eval_count") or 0)
    eval_count = int(data.get("eval_count") or 0)
    total_duration_s = (data.get("total_duration") or 0) / 1_000_000_000
    prompt_eval_duration_s = (data.get("prompt_eval_duration") or 0) / 1_000_000_000
    eval_duration_s = (data.get("eval_duration") or 0) / 1_000_000_000
    runtime_info = get_ollama_model_runtime_info(model_name)
    ollama_size_vram = int(runtime_info.get("size_vram") or 0)
    ollama_device = "gpu" if ollama_size_vram > 0 else "cpu"

    if require_gpu and ollama_device != "gpu":
        raise RuntimeError(
            "Ollama did not report GPU usage for this model. "
            "Check that the NVIDIA/AMD driver is visible to Ollama and that the model fits in VRAM."
        )

    metadata = {
        "wall_time_s": round(elapsed, 6),
        "done_reason": data.get("done_reason"),
        "eval_count": eval_count,
        "prompt_eval_count": prompt_eval_count,
        "total_duration": data.get("total_duration"),
        "load_duration": data.get("load_duration"),
        "prompt_eval_duration": data.get("prompt_eval_duration"),
        "eval_duration": data.get("eval_duration"),
        "total_duration_s": round(total_duration_s, 6),
        "prompt_eval_duration_s": round(prompt_eval_duration_s, 6),
        "eval_duration_s": round(eval_duration_s, 6),
        "prompt_tokens_per_s": round(prompt_eval_count / prompt_eval_duration_s, 4)
        if prompt_eval_duration_s > 0
        else None,
        "eval_tokens_per_s": round(eval_count / eval_duration_s, 4)
        if eval_duration_s > 0
        else None,
        "num_predict": max_new_tokens,
        "num_ctx": num_ctx,
    }

    return output, prompt_eval_count, eval_count, elapsed, metadata

def simplify_one_hf(
    texto: str,
    instrucciones: str,
    model,
    tokenizer,
    input_device: torch.device,
    max_input_tokens: int = 4096,
    max_new_tokens: int = 256,
    marker: str = "SIMPLIFIED TEXT:",
) -> Tuple[str, int, int, float, Dict[str, Any]]:
    """
    Devuelve (simplificado, in_tokens, new_tokens, elapsed_s).
    """
    t0 = time.perf_counter()

    prompt = (
        f"{instrucciones}\n\n"
        "# TARGET TEXT\n\n"
        f'"""\n{texto}\n"""\n\n'
        "# ANSWER\n"
        "Write the simplified version below and nothing else.\n"
    )

    enc = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_input_tokens,
    )
    in_tokens = int(enc["input_ids"].shape[1])
    enc = {k: v.to(input_device) for k, v in enc.items()}

    with torch.inference_mode():
        out = model.generate(
            **enc,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            repetition_penalty=1.05,
            no_repeat_ngram_size=3,
            eos_token_id=tokenizer.eos_token_id,
        )

    out_tokens_total = int(out.shape[1])
    new_tokens = max(0, out_tokens_total - in_tokens)

    gen_only = out[0, in_tokens:]
    decoded = tokenizer.decode(gen_only, skip_special_tokens=True)
    simplified = decoded.strip()

    elapsed = time.perf_counter() - t0

    return simplified, in_tokens, new_tokens, elapsed, {"wall_time_s": round(elapsed, 6)}

def simplify_one(
    backend: str,
    texto: str,
    instrucciones: str,
    model,
    tokenizer,
    model_name: str,
    input_device,
    max_input_tokens,
    max_new_tokens,
    marker,
    ollama_num_ctx=None,
    ollama_temperature=None,
    ollama_seed=None,
    ollama_top_k=None,
    ollama_top_p=None,
    ollama_repeat_penalty=None,
    ollama_repeat_last_n=None,
    ollama_num_gpu=None,
    ollama_require_gpu=False,
    ollama_timeout=300,
):

    if backend == "hf":

        return simplify_one_hf(
            texto,
            instrucciones,
            model,
            tokenizer,
            input_device,
            max_input_tokens,
            max_new_tokens,
            marker,
        )

    elif backend == "ollama":

        return simplify_one_ollama(
            texto,
            instrucciones,
            model_name,
            marker,
            max_new_tokens=max_new_tokens,
            num_ctx=ollama_num_ctx,
            temperature=ollama_temperature,
            seed=ollama_seed,
            top_k=ollama_top_k,
            top_p=ollama_top_p,
            repeat_penalty=ollama_repeat_penalty,
            repeat_last_n=ollama_repeat_last_n,
            num_gpu=ollama_num_gpu,
            require_gpu=ollama_require_gpu,
            timeout=ollama_timeout,
        )

    else:
        raise ValueError(f"Unknown backend: {backend}")
