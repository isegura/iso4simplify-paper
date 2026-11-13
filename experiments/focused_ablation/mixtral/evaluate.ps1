# Manual Mixtral evaluation: six ablations and nine original comparators.
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$pythonExe = Join-Path $projectRoot '.venv-eval\Scripts\python.exe'
$evaluator = Join-Path $projectRoot 'evaluate_mixtral_ablation.py'
$logFile = Join-Path $PSScriptRoot ('evaluation_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
& $pythonExe -u $evaluator 2>&1 | Tee-Object -FilePath $logFile
if ($LASTEXITCODE -ne 0) { throw "Mixtral evaluation failed. Check $logFile before rerunning." }
Write-Host "Mixtral evaluation complete. Log: $logFile"
