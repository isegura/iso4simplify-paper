"""Source-only retrieval helpers. No Ollama access."""
import re
import unicodedata
import numpy as np


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', str(text)).casefold().strip().strip('"').split())


def document_id(value, dataset):
    text = str(value)
    return re.sub(r'-(?:a2|b1)$', '', text, flags=re.I) if dataset == 'tsar2025' else text


def select_three(scores, pool, source, text_id, dataset):
    if not np.isfinite(scores).all():
        raise ValueError('Nonfinite retrieval scores')
    order = np.lexsort((pool.training_row_index.to_numpy(), -np.asarray(scores)))
    selected, seen_sources, seen_ids = [], set(), set()
    for index in order:
        row = pool.iloc[int(index)]
        key, doc = normalized(row.original), document_id(row.text_id, dataset)
        if key == normalized(source) or doc == document_id(text_id, dataset) or key in seen_sources or doc in seen_ids:
            continue
        selected.append((int(index), float(scores[index])))
        seen_sources.add(key); seen_ids.add(doc)
        if len(selected) == 3:
            return selected
    raise ValueError('Fewer than three distinct eligible training documents')


def encode_full_sources(model, texts):
    """Token chunks -> unit chunk embeddings -> length-weighted mean -> unit vector.

    Chunk decoding is confined to retrieval; generation uses original texts unchanged.
    """
    import torch
    chunks, owners, weights, lengths, numbers = [], [], [], [], []
    for index, text in enumerate(texts):
        ids = model.tokenizer.encode(str(text), add_special_tokens=False, truncation=False, verbose=False)
        if not ids:
            raise ValueError('Empty source for semantic retrieval')
        pieces = [ids[start:start+224] for start in range(0,len(ids),224)]
        lengths.append(len(ids)); numbers.append(len(pieces))
        for piece in pieces:
            chunk = model.tokenizer.decode(piece, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            encoded_length = len(model.tokenizer.encode(chunk, add_special_tokens=True, truncation=False, verbose=False))
            if encoded_length > model.max_seq_length:
                raise ValueError('Chunk would be truncated by embedding model')
            chunks.append(chunk); owners.append(index); weights.append(len(piece))
    with torch.inference_mode():
        vectors = model.encode(chunks, batch_size=16, show_progress_bar=True, convert_to_numpy=True,
                               normalize_embeddings=True, device='cpu')
    pooled = np.zeros((len(texts), vectors.shape[1]), dtype=np.float64)
    for owner, weight, vector in zip(owners, weights, vectors):
        pooled[owner] += weight * vector
    norms = np.linalg.norm(pooled, axis=1, keepdims=True)
    if (norms <= 0).any() or not np.isfinite(pooled).all():
        raise ValueError('Invalid embedding vectors')
    return (pooled/norms).astype(np.float32), np.asarray(lengths), np.asarray(numbers)
