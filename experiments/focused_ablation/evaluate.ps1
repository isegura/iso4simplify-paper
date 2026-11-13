# Run manually after the MeaningBERT historical validation has passed.
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$pythonExe = Join-Path $projectRoot '.venv-eval\Scripts\python.exe'
$evaluator = Join-Path $projectRoot 'evaluate_focused_ablation.py'
$logFile = Join-Path $PSScriptRoot ('evaluation_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
& $pythonExe -u $evaluator 2>&1 | Tee-Object -FilePath $logFile
if ($LASTEXITCODE -ne 0) { throw "Evaluation failed. Check $logFile before rerunning." }
Write-Host "Evaluation complete. Log: $logFile"
