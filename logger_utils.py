import logging
import re
import sys
import os
import subprocess
import time
from pathlib import Path

import torch


# LOGGER SETUP
# =========================================================

def setup_logger(log_dir: Path, run_name: str) -> logging.Logger:
    """
    Create a logger that writes both to console and file.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    print(run_name)
    run_name  = re.sub(r"[:.]+", "_", run_name )

    log_path = log_dir / f"{run_name}.log"
    
    logger = logging.getLogger("experiment")
    logger.setLevel(logging.INFO)

    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    # File log
    fh = logging.FileHandler(log_path)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console log
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info(f"Log file: {log_path}")

    return logger


# =========================================================
# GPU INFO
# =========================================================

def log_gpu_info(logger):
    """
    Log information about GPUs and CUDA environment.
    """
    logger.info("=== GPU INFO ===")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    logger.info(f"CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', '(not set)')}")

    if not torch.cuda.is_available():
        logger.info("No CUDA devices detected.")
        logger.info("=================")
        return

    device_count = torch.cuda.device_count()
    logger.info(f"GPU count: {device_count}")

    for i in range(device_count):
        props = torch.cuda.get_device_properties(i)

        logger.info(
            f"cuda:{i} | {props.name} | "
            f"{round(props.total_memory / (1024**3), 2)} GB | "
            f"compute capability {props.major}.{props.minor} | "
            f"SMs {props.multi_processor_count}"
        )

    logger.info("=================")


# =========================================================
# RUN SUMMARY
# =========================================================

def log_run_summary(
    logger,
    n_texts: int,
    total_runtime: float,
    total_inference_time: float,
    new_tokens: int,
):
    """
    Log summary of experiment runtime and throughput.
    """

    logger.info("\n=== RUN SUMMARY ===")

    logger.info(f"Texts processed: {n_texts}")
    logger.info(f"Total runtime: {total_runtime:.2f} s ({total_runtime/60:.2f} min)")

    if total_inference_time > 0:
        logger.info(f"Avg time per text: {total_inference_time/n_texts:.3f} s")

        logger.info(
            f"Throughput (texts/s): {n_texts/total_inference_time:.2f}"
        )

        logger.info(
            f"Throughput (new tokens/s): {new_tokens/total_inference_time:.1f}"
        )

    # GPU memory usage
    if torch.cuda.is_available():

        peak_mem = torch.cuda.max_memory_allocated() / 1024**3
        logger.info(f"Peak GPU memory allocated: {peak_mem:.2f} GB")

    logger.info("===================\n")