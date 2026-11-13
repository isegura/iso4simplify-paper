$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
& (Join-Path $projectRoot '.venv\Scripts\python.exe') -u (Join-Path $PSScriptRoot 'study.py') run --strategy zero
if ($LASTEXITCODE -ne 0) { throw 'Zero-shot run stopped; inspect the error before resuming.' }
