$ErrorActionPreference = 'Stop'
Write-Host 'Current design: Mixtral + Cochrane + ISO zero-shot, 31 texts; only repeat_penalty=1.0.'
& (Join-Path $PSScriptRoot 'cochrane_iso_shared_subset\run_zero.ps1')
