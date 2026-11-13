$Root = "error_analysis_candidates_512"
$Out = Join-Path $Root "lower_performing_error_evidence.html"

function EncodeHtml($value) {
    return [System.Net.WebUtility]::HtmlEncode([string]$value)
}

function ShortText($value, $chars = 420) {
    $text = ([string]$value) -replace "\s+", " "
    $text = $text.Trim()
    if ($text.Length -le $chars) { return $text }
    return $text.Substring(0, $chars - 1).TrimEnd() + "..."
}

$Reports = @(
    @{
        Title = "Llama 3.1 8B / Cochrane / minimal / one"
        Json = "llama/cochrane/predictions_llama3_1_8b_cochrane_minimal_one_lowest_sari.json"
        Html = "llama/cochrane/predictions_llama3_1_8b_cochrane_minimal_one_lowest_sari.html"
        Examples = @(
            @{ Id = "CD005255"; Issue = "Too brief"; Evidence = "87 generated words vs. 201 reference words; omits explanatory detail" },
            @{ Id = "CD006383"; Issue = "Too brief"; Evidence = "97 generated words vs. 269 reference words; compresses several findings" },
            @{ Id = "CD007744"; Issue = "Too brief"; Evidence = "73 generated words vs. 384 reference words; keeps IBD but omits much of the reference detail" },
            @{ Id = "CD007196"; Issue = "Too brief"; Evidence = "85 generated words vs. 352 reference words; summarizes the main finding but removes detail" }
        )
    },
    @{
        Title = "Llama 3.1 8B / PLABA / minimal / one"
        Json = "llama/plaba/predictions_llama3_1_8b_plaba_minimal_one_lowest_sari.json"
        Html = "llama/plaba/predictions_llama3_1_8b_plaba_minimal_one_lowest_sari.html"
        Examples = @(
            @{ Id = "32443304"; Issue = "Too brief"; Evidence = "110 generated words vs. 305 reference words; omits explanatory detail" },
            @{ Id = "25963653"; Issue = "Too brief"; Evidence = "108 generated words vs. 251 reference words; keeps hCG acronym and compresses explanations" },
            @{ Id = "32631287"; Issue = "Too brief"; Evidence = "91 generated words vs. 309 reference words; compresses treatment details" },
            @{ Id = "27630909"; Issue = "Too brief"; Evidence = "115 generated words vs. 275 reference words; summarizes diagnosis details" },
            @{ Id = "34924800"; Issue = "Insufficient simplification"; Evidence = "keeps ferritin, deferiprone, deferasirox, deferoxamine, ng/mL" }
        )
    },
    @{
        Title = "Llama 3.1 8B / TSAR 2025 / ISO / zero"
        Json = "llama/tsar2025/predictions_llama3_1_8b_tsar2025_iso_zero_lowest_sari.json"
        Html = "llama/tsar2025/predictions_llama3_1_8b_tsar2025_iso_zero_lowest_sari.html"
        Examples = @(
            @{ Id = "78"; Issue = "Organization or presentation difference"; Evidence = "converts part of the source text into numbered and bulleted lists" },
            @{ Id = "76"; Issue = "Organization or presentation difference"; Evidence = "uses a list of examples rather than prose similar to the references" },
            @{ Id = "99"; Issue = "Format-related error"; Evidence = "starts with 'Here is the simplified text'" },
            @{ Id = "98"; Issue = "Format-related error"; Evidence = "adds a note explaining the rewriting process" }
        )
    },
    @{
        Title = "Mixtral 8x7B / Cochrane / ISO / zero"
        Json = "mixtral/cochrane/predictions_mixtral_latest_cochrane_iso_zero_lowest_sari.json"
        Html = "mixtral/cochrane/predictions_mixtral_latest_cochrane_iso_zero_lowest_sari.html"
        Examples = @(
            @{ Id = "CD007196"; Issue = "Incomplete output"; Evidence = "prediction stops at 'average age: 4'" },
            @{ Id = "CD011627"; Issue = "Incomplete output"; Evidence = "prediction stops at '13 trials with 1'" },
            @{ Id = "CD010876"; Issue = "Incomplete output"; Evidence = "prediction stops at '1987 and 2'" },
            @{ Id = "CD009953"; Issue = "Incomplete output"; Evidence = "prediction stops at '984 participants from 1'" },
            @{ Id = "CD008720"; Issue = "Incomplete output"; Evidence = "prediction stops at '20,00'" }
        )
    },
    @{
        Title = "Mixtral 8x7B / PLABA / ISO / zero"
        Json = "mixtral/plaba/predictions_mixtral_latest_plaba_iso_zero_lowest_sari.json"
        Html = "mixtral/plaba/predictions_mixtral_latest_plaba_iso_zero_lowest_sari.html"
        Examples = @(
            @{ Id = "35136706"; Issue = "Incomplete output"; Evidence = "prediction stops at 'non-Covid-1'" },
            @{ Id = "27630909"; Issue = "Incomplete output"; Evidence = "prediction stops at 'Jan 2006 - Dec 2'" },
            @{ Id = "35240553"; Issue = "Incomplete output"; Evidence = "prediction stops at 'COVID-1'" },
            @{ Id = "34960751"; Issue = "Incomplete output"; Evidence = "prediction stops at 'November 2'" },
            @{ Id = "34924800"; Issue = "Organization or presentation difference"; Evidence = "uses numbered/list structure and keeps technical expressions" }
        )
    },
    @{
        Title = "Mixtral 8x7B / TSAR 2025 / ISO / zero"
        Json = "mixtral/tsar2025/predictions_mixtral_latest_tsar2025_iso_zero_lowest_sari.json"
        Html = "mixtral/tsar2025/predictions_mixtral_latest_tsar2025_iso_zero_lowest_sari.html"
        Examples = @(
            @{ Id = "69"; Issue = "Incomplete output"; Evidence = "prediction stops at 'Pi and Richard Parker spend 2'" },
            @{ Id = "89"; Issue = "Incomplete output"; Evidence = "prediction stops at 'It was published in 2'" },
            @{ Id = "54"; Issue = "Too brief"; Evidence = "46 generated words vs. 74.5 reference words; compresses the content" },
            @{ Id = "72"; Issue = "Too brief"; Evidence = "59 generated words vs. 118 reference words; omits reference detail" },
            @{ Id = "96"; Issue = "Organization or presentation difference"; Evidence = "adds an explicit summary sentence" }
        )
    }
)

$Sections = New-Object System.Collections.Generic.List[string]

foreach ($report in $Reports) {
    $jsonPath = Join-Path $Root $report.Json
    $records = Get-Content $jsonPath -Raw | ConvertFrom-Json
    $byId = @{}
    foreach ($record in $records) {
        $byId[[string]$record.text_id] = $record
    }

    $Rows = New-Object System.Collections.Generic.List[string]
    foreach ($example in $report.Examples) {
        $record = $byId[[string]$example.Id]
        if ($null -eq $record) { continue }
        $Rows.Add(@"
<tr>
  <td>$(EncodeHtml $example.Id)</td>
  <td>$(EncodeHtml $record.LEN_PRED)</td>
  <td>$(EncodeHtml $record.LEN_REF)</td>
  <td>$(EncodeHtml $record.SARI)</td>
  <td>$(EncodeHtml $record.done_reason)</td>
  <td>$(EncodeHtml $example.Issue)</td>
  <td>$(EncodeHtml $example.Evidence)</td>
  <td>$(EncodeHtml (ShortText $record.prediction))</td>
</tr>
"@)
    }

    $Sections.Add(@"
<section>
  <h2>$(EncodeHtml $report.Title)</h2>
  <p><a href="$(EncodeHtml $report.Html)">Open complete HTML report</a></p>
  <table>
    <thead>
      <tr>
        <th>Text ID</th>
        <th>Generated words</th>
        <th>Reference words</th>
        <th>SARI</th>
        <th>Stop reason</th>
        <th>Error pattern</th>
        <th>Evidence</th>
        <th>Generated simplification excerpt</th>
      </tr>
    </thead>
    <tbody>
      $($Rows -join "`n")
    </tbody>
  </table>
</section>
"@)
}

$Html = @"
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Low-performing configuration error evidence</title>
  <style>
    body { font-family: Arial, Helvetica, sans-serif; margin: 32px; color: #222; line-height: 1.45; }
    h1 { margin-bottom: 0.2rem; }
    h2 { margin-top: 2rem; }
    .note { max-width: 980px; padding: 14px 16px; border-left: 4px solid #8a4a12; background: #fff7ed; }
    table { border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }
    th, td { border: 1px solid #cfcfcf; padding: 8px; vertical-align: top; }
    th { background: #eeeeee; text-align: left; }
    td:nth-child(8) { max-width: 460px; }
    a { color: #224f9c; }
  </style>
</head>
<body>
  <h1>Evidence of Error Patterns in Low-performing Configurations</h1>
  <p class="note">
    This report summarizes concrete examples found during the qualitative error analysis of the selected
    low-performing configurations. The table links point to the complete HTML reports for each configuration.
    <em>Stop reason</em> comes from the Ollama termination metadata: <code>stop</code> means that the model stopped
    naturally, while <code>length</code> means that it reached the configured generation limit.
  </p>
  $($Sections -join "`n")
</body>
</html>
"@

Set-Content -Path $Out -Value $Html -Encoding UTF8
Write-Host "Wrote $((Resolve-Path $Out).Path)"
