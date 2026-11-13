param(
    [Parameter(Mandatory=$true)][ValidateSet('llama','mixtral')][string]$Model,
    [Parameter(Mandatory=$true)][ValidateSet(44,46)][int]$Seed,
    [ValidateSet('cochrane','plaba','tsar2025')][string]$Dataset,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$runArgs = @('-u', (Join-Path $PSScriptRoot 'study.py'), 'run', '--model', $Model, '--seed', $Seed)
if ($Dataset) { $runArgs += @('--dataset', $Dataset) }
if (-not $DryRun) { $runArgs += '--execute' }
& $python @runArgs
if ($LASTEXITCODE -ne 0) { throw 'Study block stopped; inspect the error before resuming.' }
