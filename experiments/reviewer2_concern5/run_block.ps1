param(
    [Parameter(Mandatory=$true)][ValidateSet('llama','mixtral')][string]$Model,
    [ValidateSet('cochrane','plaba','tsar2025')][string]$Dataset,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$runArgs = @('-u', (Join-Path $PSScriptRoot 'study.py'), 'run', '--model', $Model)
if ($Dataset) { $runArgs += @('--dataset', $Dataset) }
if (-not $DryRun) { $runArgs += '--execute' }
& $python @runArgs
if ($LASTEXITCODE -ne 0) { throw 'Retrieval block stopped; inspect the error before resuming.' }
