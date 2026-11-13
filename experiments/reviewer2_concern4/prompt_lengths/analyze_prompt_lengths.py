"""Read-only audit of original 72 runs. No inference or model downloads."""
from pathlib import Path
import ast
import hashlib
import itertools
import json
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    if (HERE / 'complete.json').exists():
        raise FileExistsError('Completed analysis exists; refusing overwrite')
    # Extract the actual f-string from the Ollama function, rather than duplicate it.
    tree = ast.parse((ROOT / 'model_utils.py').read_text(encoding='utf-8-sig'))
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name == 'simplify_one_ollama']
    assert len(functions) == 1
    expr = next(n.value for n in functions[0].body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'prompt' for t in n.targets))
    prompt_code = compile(ast.Expression(expr), '<original Ollama prompt>', 'eval')
    hashes = {'model_utils.py': sha(ROOT / 'model_utils.py')}
    rows = []
    for model, dataset, prompt, strategy in itertools.product(
            ['llama', 'mixtral'], ['cochrane', 'plaba', 'tsar2025'],
            ['minimal', 'iso', 'iso_examples'], ['zero', 'one', 'few_random', 'few_metric']):
        short = 'llama3_1_8b' if model == 'llama' else 'mixtral_latest'
        pred = ROOT / 'outputs' / (model + '_512') / f'predictions_{short}_{dataset}_{prompt}_{strategy}.csv'
        name = (f'{prompt}_zero.md' if strategy == 'zero' else f'{dataset}_{prompt}_{strategy}.md')
        path = ROOT / 'prompts' / name
        for source in [pred, path]:
            hashes[str(source.relative_to(ROOT))] = sha(source)
        instructions = path.read_text(encoding='utf-8')
        frame = pd.read_csv(pred, keep_default_na=False, dtype={'text_id': str})
        expected = pd.read_csv(ROOT / 'data' / dataset / f'{dataset}_test.csv',
                               keep_default_na=False, dtype={'text_id': str})
        assert frame[['text_id', 'original']].equals(expected[['text_id', 'original']])
        for index, row in frame.iterrows():
            full = eval(prompt_code, {'__builtins__': {}},
                        {'instrucciones': instructions, 'texto': row['original']})
            tokens = int(row['prompt_eval_count'])
            ctx, output = int(row['num_ctx']), int(row['num_predict'])
            assert tokens > 0 and ctx == 8192 and output == 512
            rows.append(dict(model=model, dataset=dataset, prompt=prompt, strategy=strategy,
                row_index=index, text_id=row['text_id'], prompt_file=name,
                instruction_characters=len(instructions), full_user_message_characters=len(full),
                full_user_message_whitespace_words=len(full.split()),
                full_user_message_sha256=hashlib.sha256(full.encode()).hexdigest(),
                observed_prompt_eval_count=tokens, context_tokens=ctx, max_output_tokens=output,
                observed_context_headroom_after_512=ctx-output-tokens,
                observed_input_over_context=tokens > ctx,
                observed_input_plus_512_over_context=tokens+output > ctx,
                done_reason=row['done_reason']))
    items = pd.DataFrame(rows)
    assert len(items) == 8952
    items.to_csv(HERE / 'per_input_lengths.csv', index=False)
    summaries = []
    for keys, group in items.groupby(['model', 'dataset', 'prompt', 'strategy'], sort=False):
        x = group.observed_prompt_eval_count
        summaries.append(dict(zip(['model', 'dataset', 'prompt', 'strategy'], keys),
            n=len(group), observed_tokens_min=int(x.min()), observed_tokens_median=float(x.median()),
            observed_tokens_mean=float(x.mean()), observed_tokens_p95=float(x.quantile(.95)),
            observed_tokens_max=int(x.max()),
            min_observed_headroom_after_512=int(group.observed_context_headroom_after_512.min()),
            observed_input_over_context=int(group.observed_input_over_context.sum()),
            observed_input_plus_512_over_context=int(group.observed_input_plus_512_over_context.sum())))
    summary = pd.DataFrame(summaries)
    assert len(summary) == 72
    summary.to_csv(HERE / 'summary.csv', index=False)
    focus = summary[(summary.dataset == 'cochrane') & (summary.prompt == 'iso_examples')
                    & summary.strategy.str.startswith('few')]
    focus.to_csv(HERE / 'cochrane_iso_examples_three_demonstrations.csv', index=False)
    methods = dict(scope='Original 72 configurations only; no ablation outputs',
        token_measure='Historical Ollama prompt_eval_count, not independent untruncated tokenization',
        reconstruction='Current prompt files and exact f-string extracted from simplify_one_ollama; user-message characters and whitespace words exclude model chat-template overhead',
        limitations=['Historical prompt-file identity is not certified by current hashes alone.',
          'Processed token counts cannot exclude pre-processing truncation or establish complete raw input length.',
          'No new model inference, tokenization API calls, downloads or manuscript edits.',
          '8192-512=7680 is a conservative input budget for a full 512-token response; exceeding it is not proof of input truncation.'],
        context=8192, output_allowance=512, source_sha256=hashes)
    (HERE / 'methodology.json').write_text(json.dumps(methods, indent=2), encoding='utf-8')
    table = '| Model | Selection | Min | Median | Max | Headroom after 512 |\n|---|---|---:|---:|---:|---:|\n'
    for r in focus.itertuples():
        table += f'| {r.model} | {r.strategy} | {r.observed_tokens_min} | {r.observed_tokens_median:g} | {r.observed_tokens_max} | {r.min_observed_headroom_after_512} |\n'
    over = int(items.observed_input_plus_512_over_context.sum())
    report = f'''# Longitud de entradas: Reviewer 2, Concern 4

Se analizaron las 72 configuraciones originales (8952 entradas). Los CSV originales contienen el contador de tokens procesados por Ollama. No se generaron nuevas simplificaciones ni se modificaron resultados ni archivos LaTeX.

## Cochrane, ISO+examples, few-shot (tres demostraciones)

{table}
Los valores son `prompt_eval_count` de las ejecuciones originales. La columna final resta entrada observada y 512 tokens de salida al contexto de 8192.

En las 8952 entradas hay **{over}** casos cuyo contador observado más 512 supera 8192. El máximo global observado es **{items.observed_prompt_eval_count.max()}** tokens.

## Alcance e interpretación

Estos registros no muestran un exceso del presupuesto si el número de casos anterior es cero. Sin embargo, no permiten certificar que ninguna entrada original fuera recortada antes de procesarse. No confundir ausencia de evidencia de exceso con prueba de ausencia de truncamiento de entrada.

Se reconstruyó el mensaje de usuario completo con la misma expresión de `model_utils.py`: instrucciones (incluidas las demostraciones del archivo), TARGET TEXT y ANSWER. Se guardan caracteres, palabras por espacios y hash por entrada; estas medidas NO se presentan como tokens. La plantilla de chat del modelo no está incluida en esos caracteres. Los hashes actuales no certifican por sí solos que los prompts históricos no cambiaran.

Para cerrar una verificación independiente haría falta tokenizar las entradas completas con el tokenizador y plantilla de chat exactos de cada modelo. No se ha sustituido esa comprobación por un tokenizador de otro modelo ni por estimaciones de caracteres.

## Ubicación propuesta en los documentos

Paper: V.A, Models and Inference Environment, después del párrafo que fija 512 tokens y contexto 8192. Suplemento: S2, nuevo apartado sobre longitud de entrada y presupuesto de contexto, con `summary.csv` como tabla completa. Los .tex originales permanecen sin editar. La redacción final debe conservar la distinción entre tokens procesados y longitud independiente de la entrada completa.
'''
    (HERE / 'REPORT.md').write_text(report, encoding='utf-8')
    for relative, digest in hashes.items():
        assert sha(ROOT / relative) == digest, relative
    (HERE / 'complete.json').write_text(json.dumps(dict(status='completed_observed_count_audit',
        configurations=72, rows=len(items), source_hashes_verified_unchanged=True,
        independent_untruncated_tokenization_completed=False), indent=2), encoding='utf-8')
    print(report)

if __name__ == '__main__':
    main()
