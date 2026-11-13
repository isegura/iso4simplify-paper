# Six Mixtral full runs. Execute manually only when ready; no automatic launch.
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
$launcher = Join-Path $projectRoot 'run_focused_ablation.py'
& $pythonExe $launcher --model mixtral:latest --dataset cochrane --prompt iso --execute
if ($LASTEXITCODE -ne 0) { throw 'Mixtral ablation failed; stopping batch.' }
& $pythonExe $launcher --model mixtral:latest --dataset cochrane --prompt iso_examples --execute
if ($LASTEXITCODE -ne 0) { throw 'Mixtral ablation failed; stopping batch.' }
& $pythonExe $launcher --model mixtral:latest --dataset plaba --prompt iso --execute
if ($LASTEXITCODE -ne 0) { throw 'Mixtral ablation failed; stopping batch.' }
& $pythonExe $launcher --model mixtral:latest --dataset plaba --prompt iso_examples --execute
if ($LASTEXITCODE -ne 0) { throw 'Mixtral ablation failed; stopping batch.' }
& $pythonExe $launcher --model mixtral:latest --dataset tsar2025 --prompt iso --execute
if ($LASTEXITCODE -ne 0) { throw 'Mixtral ablation failed; stopping batch.' }
& $pythonExe $launcher --model mixtral:latest --dataset tsar2025 --prompt iso_examples --execute
if ($LASTEXITCODE -ne 0) { throw 'Mixtral ablation failed; stopping batch.' }
Write-Host 'All six Mixtral ablations finished. Verify completeness before evaluation.'
