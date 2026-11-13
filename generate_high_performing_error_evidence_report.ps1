$Root = "error_analysis_candidates_512"
$Out = Join-Path $Root "high_performing_error_evidence.html"

function EncodeHtml($value) {
    return [System.Net.WebUtility]::HtmlEncode([string]$value)
}

function ShortText($value, $chars = 360) {
    $text = ([string]$value) -replace "\s+", " "
    $text = $text.Trim()
    if ($text.Length -le $chars) { return $text }
    return $text.Substring(0, $chars - 1).TrimEnd() + "..."
}

$Reports = @(
    @{
        Title = "Llama 3.1 8B / Cochrane / ISO+examples / few-metric"
        Json = "llama/cochrane/predictions_llama3_1_8b_cochrane_iso_examples_few_metric_lowest_sari.json"
        Html = "llama/cochrane/predictions_llama3_1_8b_cochrane_iso_examples_few_metric_lowest_sari.html"
        Examples = @(
            @{ Id = "CD009170"; Issue = "Insufficient simplification"; Evidence = "RR 0.46; RR 0.31" },
            @{ Id = "CD010814"; Issue = "Insufficient simplification"; Evidence = "OR; 95% CI; MD" },
            @{ Id = "CD006301"; Issue = "Incomplete output"; Evidence = "RCTs; myeloablative therapy; HR; CI; interstitial pneumonitis; veno-occlusive disease; ends with 'after'" },
            @{ Id = "CD007744"; Issue = "Possible over-compression"; Evidence = "rofecoxib; valdecoxib; lumiracoxib; etoricoxib; celecoxib; IBD" }
        )
    },
    @{
        Title = "Llama 3.1 8B / PLABA / ISO+examples / few-random"
        Json = "llama/plaba/predictions_llama3_1_8b_plaba_iso_examples_few_random_lowest_sari.json"
        Html = "llama/plaba/predictions_llama3_1_8b_plaba_iso_examples_few_random_lowest_sari.html"
        Examples = @(
            @{ Id = "35240553"; Issue = "Format-related error"; Evidence = "Here is the simplified text; final explanatory note" },
            @{ Id = "34883281"; Issue = "Format-related error"; Evidence = "Note explaining how the text had been rewritten" },
            @{ Id = "15552918"; Issue = "Format-related error"; Evidence = "Note explaining how the text had been rewritten" },
            @{ Id = "34619975"; Issue = "Format-related error"; Evidence = "Here is the simplified text; redox; metformin; lupus; biomarkers" },
            @{ Id = "34605394"; Issue = "Format-related error"; Evidence = "belimumab; anifrolumab" },
            @{ Id = "34924800"; Issue = "Insufficient simplification"; Evidence = "ferritin; deferiprone; deferasirox; deferoxamine" }
        )
    },
    @{
        Title = "Mixtral 8x7B / Cochrane / minimal / one"
        Json = "mixtral/cochrane/predictions_mixtral_latest_cochrane_minimal_one_lowest_sari.json"
        Html = "mixtral/cochrane/predictions_mixtral_latest_cochrane_minimal_one_lowest_sari.html"
        Examples = @(
            @{ Id = "CD008720"; Issue = "Incomplete output"; Evidence = "ends with '10,00'" },
            @{ Id = "CD006301"; Issue = "Incomplete output"; Evidence = "64 words vs. 272 reference words; ends with 'after'" },
            @{ Id = "CD013137"; Issue = "Incomplete output"; Evidence = "18 words vs. 344 reference words" },
            @{ Id = "CD010166"; Issue = "Insufficient simplification"; Evidence = "I2; subgroup analysis; risk of bias" }
        )
    },
    @{
        Title = "Mixtral 8x7B / PLABA / ISO / few-random"
        Json = "mixtral/plaba/predictions_mixtral_latest_plaba_iso_few_random_lowest_sari.json"
        Html = "mixtral/plaba/predictions_mixtral_latest_plaba_iso_few_random_lowest_sari.html"
        Examples = @(
            @{ Id = "27630909"; Issue = "Incomplete output"; Evidence = "49 words vs. 275 reference words; Introduction; Aim" },
            @{ Id = "29169352"; Issue = "Incomplete output"; Evidence = "ends with 'March 2'" },
            @{ Id = "30088053"; Issue = "Incomplete output"; Evidence = "ends with '2013 to 2'" },
            @{ Id = "32840002"; Issue = "Incomplete output"; Evidence = "4 words vs. 275 reference words" },
            @{ Id = "34924800"; Issue = "Insufficient simplification"; Evidence = "hyperferritinemia; deferiprone; deferasirox; deferoxamine; FDA; microgram/L" },
            @{ Id = "32631287"; Issue = "Insufficient simplification"; Evidence = "AI; AICR; arthroscopic terminology" }
        )
    },
    @{
        Title = "Mixtral 8x7B / TSAR 2025 / minimal / few-metric"
        Json = "mixtral/tsar2025/predictions_mixtral_latest_tsar2025_minimal_few_metric_lowest_sari.json"
        Html = "mixtral/tsar2025/predictions_mixtral_latest_tsar2025_minimal_few_metric_lowest_sari.html"
        Examples = @(
            @{ Id = "71"; Issue = "Incomplete output"; Evidence = "prediction: 'In 2'" },
            @{ Id = "89"; Issue = "Incomplete output"; Evidence = "ends with 'It was published in 2'" },
            @{ Id = "93"; Issue = "Incomplete output"; Evidence = "ends with 'and in 2'" },
            @{ Id = "22"; Issue = "Incomplete output"; Evidence = "ends with 'In 2'" },
            @{ Id = "35"; Issue = "Incomplete output"; Evidence = "ends with 'In 2'" }
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
  <title>High-performing configuration error evidence</title>
  <style>
    body { font-family: Arial, Helvetica, sans-serif; margin: 32px; color: #222; line-height: 1.45; }
    h1 { margin-bottom: 0.2rem; }
    h2 { margin-top: 2rem; }
    .note { max-width: 980px; padding: 14px 16px; border-left: 4px solid #4067b2; background: #f3f6fc; }
    table { border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }
    th, td { border: 1px solid #cfcfcf; padding: 8px; vertical-align: top; }
    th { background: #eeeeee; text-align: left; }
    td:nth-child(8) { max-width: 460px; }
    a { color: #224f9c; }
  </style>
</head>
<body>
  <h1>Evidence of Error Patterns in High-performing Configurations</h1>
  <p class="note">
    This report summarizes concrete examples found during the qualitative error analysis of the selected
    high-performing configurations. The table links point to the complete HTML reports for each configuration.
    <em>Stop reason</em> comes from the Ollama termination
    metadata: <code>stop</code> means that the model stopped naturally, while <code>length</code> means that it
    reached the configured generation limit.
  </p>
  $($Sections -join "`n")
</body>
</html>
"@

Set-Content -Path $Out -Value $Html -Encoding UTF8
Write-Host "Wrote $((Resolve-Path $Out).Path)"
