param(
    [Parameter(Mandatory=$true)][ValidateSet('llama','mixtral')][string]$Model,
    [ValidateSet('cochrane','plaba','tsar2025')][string]$Dataset,
    [switch]$Pilot,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
if ($Pilot -and -not $Dataset) { throw 'Pilot requires -Dataset.' }
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$runArgs = @('-u', (Join-Path $PSScriptRoot 'prepared_study.py'), 'run', '--model', $Model)
if ($Dataset) { $runArgs += @('--dataset', $Dataset) }
if ($Pilot) { $runArgs += @('--limit', '3') }
if (-not $DryRun) { $runArgs += '--execute' }
& $python @runArgs
if ($LASTEXITCODE -ne 0) { throw 'Prepared retrieval stopped; inspect the error before resuming.' }
