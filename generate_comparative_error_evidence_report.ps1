$Root = "error_analysis_candidates_512"
$Out = Join-Path $Root "comparative_error_evidence.html"

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
        Title = "Llama 3.1 8B / Cochrane / ISO / few-random"
        Json = "llama/cochrane/predictions_llama3_1_8b_cochrane_iso_few_random_lowest_sari.json"
        Html = "llama/cochrane/predictions_llama3_1_8b_cochrane_iso_few_random_lowest_sari.html"
        Examples = @(
            @{ Id = "CD005255"; Issue = "Too brief"; Evidence = "76 generated words vs. 201 reference words; omits explanatory detail" },
            @{ Id = "CD009170"; Issue = "Insufficient simplification"; Evidence = "keeps numerical/statistical details such as 54%, 69%, and one in six operations" },
            @{ Id = "CD001302"; Issue = "Insufficient simplification"; Evidence = "keeps OHSS, HES, imprecision, blinding, adverse events" },
            @{ Id = "CD002022"; Issue = "Insufficient simplification"; Evidence = "keeps RR, 95% CI, antagonist-induced withdrawal, naltrexone, anaesthesia" }
        )
    },
    @{
        Title = "Mixtral 8x7B / Cochrane / ISO / few-random"
        Json = "mixtral/cochrane/predictions_mixtral_latest_cochrane_iso_few_random_lowest_sari.json"
        Html = "mixtral/cochrane/predictions_mixtral_latest_cochrane_iso_few_random_lowest_sari.html"
        Examples = @(
            @{ Id = "CD005122"; Issue = "Incomplete output"; Evidence = "prediction stops at 'over 13,00'" },
            @{ Id = "CD008720"; Issue = "Incomplete output"; Evidence = "prediction stops at '10,00'" },
            @{ Id = "CD009919"; Issue = "Incomplete output"; Evidence = "prediction stops at 'a total of 1'" },
            @{ Id = "CD003122"; Issue = "Incomplete output"; Evidence = "prediction stops at 'over 10,00'" },
            @{ Id = "CD005255"; Issue = "Too brief"; Evidence = "151 generated words vs. 201 reference words; compresses source and reference detail" }
        )
    },
    @{
        Title = "Llama 3.1 8B / PLABA / ISO / few-random"
        Json = "llama/plaba/predictions_llama3_1_8b_plaba_iso_few_random_lowest_sari.json"
        Html = "llama/plaba/predictions_llama3_1_8b_plaba_iso_few_random_lowest_sari.html"
        Examples = @(
            @{ Id = "25963653"; Issue = "Insufficient simplification"; Evidence = "keeps hCG, BMI, parity, hyperemesis gravidarum, reference ranges" },
            @{ Id = "27630909"; Issue = "Insufficient simplification"; Evidence = "keeps hCG, ectopic pregnancy, expectant management, medical management" },
            @{ Id = "33818024"; Issue = "Insufficient simplification"; Evidence = "keeps beta-hCG, molar pregnancy, chemo, plant names, IU/L" },
            @{ Id = "30422545"; Issue = "Too brief"; Evidence = "42 generated words vs. 81 reference words; compresses the explanation" }
        )
    },
    @{
        Title = "Mixtral 8x7B / PLABA / ISO+examples / few-random"
        Json = "mixtral/plaba/predictions_mixtral_latest_plaba_iso_examples_few_random_lowest_sari.json"
        Html = "mixtral/plaba/predictions_mixtral_latest_plaba_iso_examples_few_random_lowest_sari.html"
        Examples = @(
            @{ Id = "27630909"; Issue = "Incomplete output"; Evidence = "prediction stops at 'from 2006 to 2'; keeps Introduction and Aim labels" },
            @{ Id = "21636864"; Issue = "Incomplete output"; Evidence = "prediction stops at 'From July 2'" },
            @{ Id = "34960751"; Issue = "Incomplete output"; Evidence = "prediction stops at 'COVID-1'" },
            @{ Id = "33816325"; Issue = "Incomplete output"; Evidence = "prediction stops at 'Covid-1'" },
            @{ Id = "33224987"; Issue = "Incomplete output"; Evidence = "prediction stops at 'COVID-1'" }
        )
    },
    @{
        Title = "Llama 3.1 8B / TSAR 2025 / ISO / few-random"
        Json = "llama/tsar2025/predictions_llama3_1_8b_tsar2025_iso_few_random_lowest_sari.json"
        Html = "llama/tsar2025/predictions_llama3_1_8b_tsar2025_iso_few_random_lowest_sari.html"
        Examples = @(
            @{ Id = "52"; Issue = "Format-related error"; Evidence = "adds a note explaining that the text was rewritten" },
            @{ Id = "78"; Issue = "Format-related error"; Evidence = "adds a note explaining compliance with the instructions" },
            @{ Id = "76"; Issue = "Organization or presentation difference"; Evidence = "uses a bulleted list rather than prose similar to the references" },
            @{ Id = "111"; Issue = "Format-related error"; Evidence = "adds a note saying it followed the instructions" }
        )
    },
    @{
        Title = "Mixtral 8x7B / TSAR 2025 / ISO+examples / few-random"
        Json = "mixtral/tsar2025/predictions_mixtral_latest_tsar2025_iso_examples_few_random_lowest_sari.json"
        Html = "mixtral/tsar2025/predictions_mixtral_latest_tsar2025_iso_examples_few_random_lowest_sari.html"
        Examples = @(
            @{ Id = "66"; Issue = "Incomplete output"; Evidence = "prediction stops at 'over 40,00'" },
            @{ Id = "93"; Issue = "Incomplete output"; Evidence = "prediction stops at 'In 2'" },
            @{ Id = "41"; Issue = "Incomplete output"; Evidence = "prediction stops at 'in 199'" },
            @{ Id = "117"; Issue = "Incomplete output"; Evidence = "prediction stops at 'about 10,00'" },
            @{ Id = "119"; Issue = "Organization or presentation difference"; Evidence = "longer discursive output with an added transition paragraph" }
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
  <title>Comparative configuration error evidence</title>
  <style>
    body { font-family: Arial, Helvetica, sans-serif; margin: 32px; color: #222; line-height: 1.45; }
    h1 { margin-bottom: 0.2rem; }
    h2 { margin-top: 2rem; }
    .note { max-width: 980px; padding: 14px 16px; border-left: 4px solid #5f5f8f; background: #f5f5fb; }
    table { border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }
    th, td { border: 1px solid #cfcfcf; padding: 8px; vertical-align: top; }
    th { background: #eeeeee; text-align: left; }
    td:nth-child(8) { max-width: 460px; }
    a { color: #224f9c; }
  </style>
</head>
<body>
  <h1>Evidence of Error Patterns in Comparative Configurations</h1>
  <p class="note">
    This report summarizes concrete examples found during the qualitative error analysis of the selected
    comparative configurations. The table links point to the complete HTML reports for each configuration.
    <em>Stop reason</em> comes from the Ollama termination metadata: <code>stop</code> means that the model stopped
    naturally, while <code>length</code> means that it reached the configured generation limit.
  </p>
  $($Sections -join "`n")
</body>
</html>
"@

Set-Content -Path $Out -Value $Html -Encoding UTF8
Write-Host "Wrote $((Resolve-Path $Out).Path)"
