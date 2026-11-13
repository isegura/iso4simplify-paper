# Await explicit user approval before execution. Run from repository root.
.\.venv\Scripts\python.exe .\run_focused_ablation.py --dataset cochrane --prompt iso --execute
if ($LASTEXITCODE -ne 0) { throw "Ablation failed; stopping batch" }
.\.venv\Scripts\python.exe .\run_focused_ablation.py --dataset cochrane --prompt iso_examples --execute
if ($LASTEXITCODE -ne 0) { throw "Ablation failed; stopping batch" }
.\.venv\Scripts\python.exe .\run_focused_ablation.py --dataset plaba --prompt iso --execute
if ($LASTEXITCODE -ne 0) { throw "Ablation failed; stopping batch" }
.\.venv\Scripts\python.exe .\run_focused_ablation.py --dataset plaba --prompt iso_examples --execute
if ($LASTEXITCODE -ne 0) { throw "Ablation failed; stopping batch" }
.\.venv\Scripts\python.exe .\run_focused_ablation.py --dataset tsar2025 --prompt iso --execute
if ($LASTEXITCODE -ne 0) { throw "Ablation failed; stopping batch" }
.\.venv\Scripts\python.exe .\run_focused_ablation.py --dataset tsar2025 --prompt iso_examples --execute
if ($LASTEXITCODE -ne 0) { throw "Ablation failed; stopping batch" }
