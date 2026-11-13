$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$InputRoot = Join-Path $Root "outputs"
$OutputRoot = Join-Path $Root "error_analysis_candidates_512"
$TsarReferencesPath = Join-Path $Root "data\tsar2025\tsar2025_test_200.csv"
$TopN = 15
$Metric = "SARI"

$DatasetOrder = @("cochrane", "plaba", "tsar2025")
$PromptOrder = @("minimal", "iso", "iso_examples")
$StrategyOrder = @("zero", "one", "few")
$SamplingOrder = @("", "random", "metric")

function HtmlEncode($value) {
    if ($null -eq $value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$value)
}

function ToNumber($value) {
    if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) { return [double]::NaN }
    $text = ([string]$value).Replace(",", ".")
    $number = 0.0
    if ([double]::TryParse($text, [System.Globalization.NumberStyles]::Any, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$number)) {
        return $number
    }
    return [double]::NaN
}

function FormatNumber($value, $digits = 2) {
    $number = ToNumber $value
    if ([double]::IsNaN($number)) { return "NA" }
    return $number.ToString("F$digits", [System.Globalization.CultureInfo]::InvariantCulture)
}

function DisplayMetricLabel($label) {
    switch ($label) {
        "text_id" { return "Text ID" }
        "LEN_COMPLEX" { return "Original words" }
        "LEN_PRED" { return "Generated words" }
        "LEN_REF" { return "Reference words" }
        "done_reason" { return "Stop reason" }
        default { return $label }
    }
}

function Get-Value($row, $name) {
    if ($row.PSObject.Properties.Name -contains $name) { return $row.$name }
    return ""
}

function PrettyModel($modelDir) {
    if ($modelDir -eq "llama_512") { return "Llama 3.1 8B" }
    if ($modelDir -eq "mixtral_512") { return "Mixtral 8x7B" }
    return $modelDir
}

function ShortModelDir($modelDir) {
    if ($modelDir -eq "llama_512") { return "llama" }
    if ($modelDir -eq "mixtral_512") { return "mixtral" }
    return $modelDir
}

function PrettyTitleFromStem($stem) {
    return ($stem -replace "^predictions_", "" -replace "_latest", "" -replace "_", " ")
}

function ParseMetadataFromFilename($fileName) {
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($fileName)
    $lower = $stem.ToLowerInvariant()

    $dataset = ""
    foreach ($candidate in $DatasetOrder) {
        if ($lower.Contains("_$candidate`_")) { $dataset = $candidate; break }
    }

    $prompt = ""
    foreach ($candidate in @("iso_examples", "minimal", "iso")) {
        if ($lower.Contains("_$candidate`_")) { $prompt = $candidate; break }
    }

    $strategy = ""
    foreach ($candidate in $StrategyOrder) {
        if ($lower.Contains("_$candidate")) { $strategy = $candidate; break }
    }

    $sampling = ""
    if ($lower.Contains("_few_random")) { $sampling = "random" }
    elseif ($lower.Contains("_few_metric")) { $sampling = "metric" }

    return [pscustomobject]@{
        Dataset = $dataset
        Prompt = $prompt
        Strategy = $strategy
        Sampling = $sampling
    }
}

function OrderValue($items, $value) {
    $index = [array]::IndexOf($items, $value)
    if ($index -lt 0) { return 999 }
    return $index
}

function LoadTsarReferenceMap() {
    $map = @{}
    if (-not (Test-Path $TsarReferencesPath)) { return $map }

    $rows = Import-Csv -Path $TsarReferencesPath
    foreach ($row in $rows) {
        $base = ([string]$row.text_id).Split("-")[0]
        if (-not $map.ContainsKey($base)) {
            $map[$base] = [ordered]@{
                original = $row.original
                reference_a2 = ""
                reference_b1 = ""
            }
        }
        $level = ([string]$row.target_cefr).ToUpperInvariant()
        if ($level -eq "A2") { $map[$base].reference_a2 = $row.reference }
        if ($level -eq "B1") { $map[$base].reference_b1 = $row.reference }
    }
    return $map
}

$TsarReferenceMap = LoadTsarReferenceMap

$ReportCss = @"
:root{--ink:#1f2937;--muted:#667085;--line:#d0d5dd;--bg:#ffffff;--original:#eff6ff;--reference:#eefaf1;--reference2:#f1efff;--prediction:#fff4e5}
*{box-sizing:border-box}body{font-family:Arial,Helvetica,sans-serif;margin:0;background:var(--bg);color:var(--ink);line-height:1.42}main{width:min(1500px,calc(100% - 32px));margin:22px auto 44px}.page-summary{background:#f8fafc;border-left:4px solid #0f766e;padding:12px 16px;margin:14px 0 28px;color:#344054}h1{font-size:30px;margin:0 0 8px}h2{font-size:30px;margin:28px 0 12px}.rule{height:1px;background:var(--line);margin:0 0 24px}.metadata-title{font-size:24px;margin:0 0 20px}.metrics-grid{display:grid;grid-template-columns:repeat(4,minmax(170px,1fr));gap:14px 44px;margin:0 0 28px}.metric{display:flex;gap:10px;align-items:baseline;min-width:0}.metric-label{font-weight:700;color:var(--muted);font-size:17px}.metric-value{font-size:18px;color:#111827}.text-stack{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;align-items:start}.text-card{border:1px solid #d0d5dd;border-radius:8px;padding:16px 22px}.text-card h3{font-size:21px;margin:0 0 10px}.text-card p{font-size:18px;margin:0;line-height:1.45}.original{background:var(--original)}.reference{background:var(--reference)}.reference-a2{background:var(--reference)}.reference-b1{background:var(--reference2)}.prediction{background:var(--prediction)}.record{margin:0 0 42px}@media(max-width:900px){main{width:min(100% - 20px,1500px)}.metrics-grid{grid-template-columns:repeat(2,minmax(150px,1fr));gap:10px 24px}.text-stack{grid-template-columns:1fr}.text-card p{font-size:18px}h1,h2{font-size:25px}.metadata-title{font-size:21px}}@media(max-width:560px){.metrics-grid{grid-template-columns:1fr}.text-card{padding:14px}.text-card p{font-size:16px}}
"@

$IndexCss = @"
:root {
  color-scheme: light;
  --bg: #f7f7f4;
  --ink: #1f2933;
  --muted: #667085;
  --line: #d9ded7;
  --panel: #ffffff;
  --head: #eef1ec;
  --band: #f1f4ef;
  --accent: #245c7a;
  --high: #e9f5ee;
  --compare: #eef3fb;
  --low: #fbefe8;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font-family: Arial, Helvetica, sans-serif; line-height: 1.5; }
main { width: min(1440px, calc(100% - 32px)); margin: 32px auto 56px; }
.intro, .dataset-section { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 24px; margin-bottom: 24px; }
h1 { margin: 0 0 8px; font-size: 32px; }
h2 { margin: 0 0 18px; padding: 12px 14px; background: var(--band); border-radius: 6px; }
h3 { margin: 24px 0 12px; font-size: 20px; }
p { color: var(--muted); margin: 0 0 14px; }
a { color: var(--accent); font-weight: 700; text-decoration: none; }
a:hover { text-decoration: underline; }
code { background: #ecefeb; padding: 2px 5px; border-radius: 4px; }
table { width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 10px; }
th, td { border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: var(--head); position: sticky; top: 0; z-index: 1; }
tbody tr:nth-child(even) { background: #fbfbf8; }
.model-section + .model-section { margin-top: 28px; }
.role-high { background: var(--high); font-weight: 700; }
.role-compare { background: var(--compare); font-weight: 700; }
.role-low { background: var(--low); font-weight: 700; }
.note { margin-top: 14px; }
"@

$Reports = New-Object System.Collections.Generic.List[object]
$PredictionFiles = Get-ChildItem -Path $InputRoot -Recurse -File -Filter "predictions_*.csv" |
    Where-Object { $_.Directory.Name -in @("llama_512", "mixtral_512") }

foreach ($file in $PredictionFiles) {
    $meta = ParseMetadataFromFilename $file.Name
    $rows = Import-Csv -Path $file.FullName
    $selected = $rows |
        ForEach-Object {
            $_ | Add-Member -NotePropertyName "__metric_num" -NotePropertyValue (ToNumber (Get-Value $_ $Metric)) -Force
            $_
        } |
        Where-Object { -not [double]::IsNaN($_.__metric_num) } |
        Sort-Object __metric_num |
        Select-Object -First $TopN

    if (-not $selected) {
        Write-Warning "No valid $Metric values in $($file.FullName)"
        continue
    }

    $shortModel = ShortModelDir $file.Directory.Name
    $outDir = Join-Path (Join-Path $OutputRoot $shortModel) $meta.Dataset
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null

    $outStem = "$($file.BaseName)_lowest_sari"
    $jsonPath = Join-Path $outDir "$outStem.json"
    $htmlPath = Join-Path $outDir "$outStem.html"

    $selected |
        Select-Object -Property * -ExcludeProperty __metric_num |
        ConvertTo-Json -Depth 4 |
        Set-Content -Path $jsonPath -Encoding UTF8

    $sariValues = @($selected | ForEach-Object { ToNumber (Get-Value $_ "SARI") })
    $sariMin = ($sariValues | Measure-Object -Minimum).Minimum
    $sariMax = ($sariValues | Measure-Object -Maximum).Maximum
    $sariMean = ($sariValues | Measure-Object -Average).Average
    $pageTitle = "$(PrettyTitleFromStem $file.BaseName) - lowest SARI"

    $records = New-Object System.Collections.Generic.List[string]
    $recordNumber = 1
    foreach ($row in $selected) {
        $metrics = @(
            @("text_id", (Get-Value $row "text_id"), 0),
            @("LEN_COMPLEX", (Get-Value $row "LEN_COMPLEX"), 0),
            @("LEN_PRED", (Get-Value $row "LEN_PRED"), 0),
            @("LEN_REF", (Get-Value $row "LEN_REF"), 0),
            @("SARI", (FormatNumber (Get-Value $row "SARI") 2), 0),
            @("BLEU", (FormatNumber (Get-Value $row "BLEU") 2), 0),
            @("FKGL", (FormatNumber (Get-Value $row "FKGL") 2), 0),
            @("FRE", (FormatNumber (Get-Value $row "FRE") 2), 0),
            @("BERTScore-F1", (FormatNumber (Get-Value $row "BERTScore-F1") 2), 0),
            @("MeaningBERT", (FormatNumber (Get-Value $row "MeaningBERT") 2), 0)
        )
        if (Get-Value $row "done_reason") {
            $metrics += ,@("done_reason", (Get-Value $row "done_reason"), 0)
        }

        $metricHtml = ($metrics | ForEach-Object {
            "<div class=""metric""><span class=""metric-label"">$(HtmlEncode (DisplayMetricLabel $_[0]))</span><span class=""metric-value"">$(HtmlEncode $_[1])</span></div>"
        }) -join "`n"

        $textCards = New-Object System.Collections.Generic.List[string]
        if ($meta.Dataset -eq "tsar2025" -and $TsarReferenceMap.ContainsKey([string](Get-Value $row "text_id"))) {
            $ref = $TsarReferenceMap[[string](Get-Value $row "text_id")]
            $textCards.Add("<section class=""text-card original""><h3>Original text</h3><p>$(HtmlEncode $ref.original)</p></section>") | Out-Null
            $textCards.Add("<section class=""text-card reference-a2""><h3>Reference simplification (A2)</h3><p>$(HtmlEncode $ref.reference_a2)</p></section>") | Out-Null
            $textCards.Add("<section class=""text-card reference-b1""><h3>Reference simplification (B1)</h3><p>$(HtmlEncode $ref.reference_b1)</p></section>") | Out-Null
        }
        else {
            $textCards.Add("<section class=""text-card original""><h3>Original text</h3><p>$(HtmlEncode (Get-Value $row "original"))</p></section>") | Out-Null
            $textCards.Add("<section class=""text-card reference""><h3>Reference simplification</h3><p>$(HtmlEncode (Get-Value $row "reference"))</p></section>") | Out-Null
        }
        $prediction = HtmlEncode (Get-Value $row "prediction")
        if ([string]::IsNullOrWhiteSpace((Get-Value $row "prediction"))) { $prediction = "<em>Empty prediction</em>" }
        $textCards.Add("<section class=""text-card prediction""><h3>Generated simplification</h3><p>$prediction</p></section>") | Out-Null

        $records.Add(@"
<article class="record">
<h2>Record $recordNumber</h2>
<div class="rule"></div>
<h3 class="metadata-title">Metadata</h3>
<div class="metrics-grid">$metricHtml</div>
<div class="text-stack">
$($textCards -join "`n")
</div>
</article>
"@) | Out-Null
        $recordNumber += 1
    }

    $reportHtml = @"
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$(HtmlEncode $pageTitle)</title>
<style>
$ReportCss
</style>
</head>
<body><main>
<h1>$(HtmlEncode (PrettyTitleFromStem $file.BaseName)): $TopN lowest-SARI cases</h1>
<div class="page-summary">Selected from the current prediction CSV using the per-instance SARI column. SARI range: $(FormatNumber $sariMin 2)-$(FormatNumber $sariMax 2); mean: $(FormatNumber $sariMean 2).</div>
<div class="page-summary">The field <strong>Stop reason</strong> indicates why the model stopped generating the output. A value of <code>stop</code> means that generation ended naturally, whereas <code>length</code> means that the maximum generation limit was reached. Outputs with <code>length</code> were considered truncated.</div>
$($records -join "`n")
</main></body>
</html>
"@
    Set-Content -Path $htmlPath -Value $reportHtml -Encoding UTF8

    $relative = $htmlPath.Substring($OutputRoot.Length + 1).Replace("\", "/")
    $Reports.Add([pscustomobject]@{
        Dataset = $meta.Dataset
        DatasetOrder = OrderValue $DatasetOrder $meta.Dataset
        Model = PrettyModel $file.Directory.Name
        ModelDir = $shortModel
        ModelOrder = if ($shortModel -eq "llama") { 0 } else { 1 }
        Prompt = $meta.Prompt
        PromptOrder = OrderValue $PromptOrder $meta.Prompt
        Strategy = $meta.Strategy
        StrategyOrder = OrderValue $StrategyOrder $meta.Strategy
        Sampling = $meta.Sampling
        SamplingOrder = OrderValue $SamplingOrder $meta.Sampling
        File = Split-Path -Leaf $htmlPath
        Relative = $relative
    }) | Out-Null

    Write-Host "$($file.Name): generated $TopN-case HTML report"
}

$indexSections = New-Object System.Collections.Generic.List[string]
$orderedReports = $Reports | Sort-Object DatasetOrder, ModelOrder, PromptOrder, StrategyOrder, SamplingOrder, File
foreach ($datasetGroup in ($orderedReports | Group-Object Dataset)) {
    $datasetName = if ($datasetGroup.Name -eq "tsar2025") { "TSAR 2025" } else { (Get-Culture).TextInfo.ToTitleCase($datasetGroup.Name) }
    $datasetHtml = "<section class=""dataset-section""><h2>$(HtmlEncode $datasetName)</h2>"
    foreach ($modelGroup in ($datasetGroup.Group | Sort-Object ModelOrder | Group-Object Model)) {
        $rowsHtml = New-Object System.Collections.Generic.List[string]
        $n = 1
        foreach ($report in ($modelGroup.Group | Sort-Object PromptOrder, StrategyOrder, SamplingOrder, File)) {
            $samplingText = if ($report.Sampling) { $report.Sampling } else { "--" }
            $description = "Prompt type $($report.Prompt), $($report.Strategy)-shot strategy"
            if ($report.Sampling) { $description += " with $($report.Sampling) example selection" }
            $description += "."
            $rowsHtml.Add(@"
<tr>
  <td>$n</td>
  <td><code>$(HtmlEncode $report.Prompt)</code></td>
  <td>$(HtmlEncode $report.Strategy)</td>
  <td>$(HtmlEncode $samplingText)</td>
  <td><a href="$(HtmlEncode $report.Relative)">$(HtmlEncode $report.File)</a></td>
  <td>$(HtmlEncode $description)</td>
</tr>
"@) | Out-Null
            $n += 1
        }
        $datasetHtml += @"
<section class="model-section">
<h3>$(HtmlEncode $modelGroup.Name)</h3>
<table>
<thead>
<tr><th>#</th><th>Prompt type</th><th>Strategy</th><th>Sampling</th><th>File</th><th>Description</th></tr>
</thead>
<tbody>
$($rowsHtml -join "`n")
</tbody>
</table>
</section>
"@
    }
    $datasetHtml += "</section>"
    $indexSections.Add($datasetHtml) | Out-Null
}

$indexHtml = @"
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>All Error Analysis Reports</title>
  <style>
$IndexCss
  </style>
</head>
<body>
  <main>
    <section class="intro">
      <h1>All Error Analysis Reports</h1>
      <p>Index of all 72 HTML reports with the 15 records with the lowest SARI for each experiment.</p>
      <p>Reports are grouped by dataset, then by model. Within each model they are ordered as: minimal, iso, iso+examples; zero, one, few; and for few-shot, random before metric.</p>
    </section>
    $($indexSections -join "`n")
  </main>
</body>
</html>
"@

Set-Content -Path (Join-Path $OutputRoot "all_error_analysis_reports.html") -Value $indexHtml -Encoding UTF8

$SelectedConfigs = @(
    [pscustomobject]@{ Dataset = "cochrane"; Model = "llama"; ModelLabel = "Llama 3.1 8B"; Prompt = "iso_examples"; PromptLabel = "iso+examples"; Strategy = "few"; Sampling = "metric"; Role = "High-performing"; Reason = "Best SARI configuration for Llama on Cochrane." },
    [pscustomobject]@{ Dataset = "cochrane"; Model = "llama"; ModelLabel = "Llama 3.1 8B"; Prompt = "minimal"; PromptLabel = "minimal"; Strategy = "one"; Sampling = ""; Role = "Lower-performing / diagnostic"; Reason = "Useful for inspecting a lower-performing Llama configuration on Cochrane." },
    [pscustomobject]@{ Dataset = "cochrane"; Model = "llama"; ModelLabel = "Llama 3.1 8B"; Prompt = "iso"; PromptLabel = "iso"; Strategy = "few"; Sampling = "random"; Role = "Comparative"; Reason = "Allows comparison with structured ISO instructions under few-shot prompting." },

    [pscustomobject]@{ Dataset = "cochrane"; Model = "mixtral"; ModelLabel = "Mixtral 8x7B"; Prompt = "minimal"; PromptLabel = "minimal"; Strategy = "one"; Sampling = ""; Role = "High-performing"; Reason = "Best SARI configuration for Mixtral on Cochrane." },
    [pscustomobject]@{ Dataset = "cochrane"; Model = "mixtral"; ModelLabel = "Mixtral 8x7B"; Prompt = "iso"; PromptLabel = "iso"; Strategy = "zero"; Sampling = ""; Role = "Lower-performing / diagnostic"; Reason = "Useful for inspecting a lower-performing ISO configuration." },
    [pscustomobject]@{ Dataset = "cochrane"; Model = "mixtral"; ModelLabel = "Mixtral 8x7B"; Prompt = "iso"; PromptLabel = "iso"; Strategy = "few"; Sampling = "random"; Role = "Comparative"; Reason = "Allows comparison between zero-shot and few-shot ISO prompting." },

    [pscustomobject]@{ Dataset = "plaba"; Model = "llama"; ModelLabel = "Llama 3.1 8B"; Prompt = "iso_examples"; PromptLabel = "iso+examples"; Strategy = "few"; Sampling = "random"; Role = "High-performing"; Reason = "Best SARI configuration for Llama on PLABA." },
    [pscustomobject]@{ Dataset = "plaba"; Model = "llama"; ModelLabel = "Llama 3.1 8B"; Prompt = "minimal"; PromptLabel = "minimal"; Strategy = "one"; Sampling = ""; Role = "Lower-performing / diagnostic"; Reason = "Useful for inspecting a lower-performing Llama configuration on PLABA." },
    [pscustomobject]@{ Dataset = "plaba"; Model = "llama"; ModelLabel = "Llama 3.1 8B"; Prompt = "iso"; PromptLabel = "iso"; Strategy = "few"; Sampling = "random"; Role = "Comparative"; Reason = "Allows comparison with ISO few-shot prompting." },

    [pscustomobject]@{ Dataset = "plaba"; Model = "mixtral"; ModelLabel = "Mixtral 8x7B"; Prompt = "iso"; PromptLabel = "iso"; Strategy = "few"; Sampling = "random"; Role = "High-performing"; Reason = "Best SARI configuration for Mixtral on PLABA." },
    [pscustomobject]@{ Dataset = "plaba"; Model = "mixtral"; ModelLabel = "Mixtral 8x7B"; Prompt = "iso"; PromptLabel = "iso"; Strategy = "zero"; Sampling = ""; Role = "Lower-performing / diagnostic"; Reason = "Useful for inspecting the zero-shot ISO baseline." },
    [pscustomobject]@{ Dataset = "plaba"; Model = "mixtral"; ModelLabel = "Mixtral 8x7B"; Prompt = "iso_examples"; PromptLabel = "iso+examples"; Strategy = "few"; Sampling = "random"; Role = "Comparative"; Reason = "Allows comparison between ISO and ISO+examples under few-shot prompting." },

    [pscustomobject]@{ Dataset = "tsar2025"; Model = "llama"; ModelLabel = "Llama 3.1 8B"; Prompt = "minimal"; PromptLabel = "minimal"; Strategy = "few"; Sampling = "random"; Role = "High-performing"; Reason = "Best SARI configuration for Llama on TSAR 2025." },
    [pscustomobject]@{ Dataset = "tsar2025"; Model = "llama"; ModelLabel = "Llama 3.1 8B"; Prompt = "iso"; PromptLabel = "iso"; Strategy = "zero"; Sampling = ""; Role = "Lower-performing / diagnostic"; Reason = "Useful for inspecting a lower-performing ISO configuration." },
    [pscustomobject]@{ Dataset = "tsar2025"; Model = "llama"; ModelLabel = "Llama 3.1 8B"; Prompt = "iso"; PromptLabel = "iso"; Strategy = "few"; Sampling = "random"; Role = "Comparative"; Reason = "Allows comparison between zero-shot and few-shot ISO prompting." },

    [pscustomobject]@{ Dataset = "tsar2025"; Model = "mixtral"; ModelLabel = "Mixtral 8x7B"; Prompt = "minimal"; PromptLabel = "minimal"; Strategy = "few"; Sampling = "metric"; Role = "High-performing"; Reason = "Best SARI configuration for Mixtral on TSAR 2025." },
    [pscustomobject]@{ Dataset = "tsar2025"; Model = "mixtral"; ModelLabel = "Mixtral 8x7B"; Prompt = "iso"; PromptLabel = "iso"; Strategy = "zero"; Sampling = ""; Role = "Lower-performing / diagnostic"; Reason = "Useful for inspecting a lower-performing ISO configuration." },
    [pscustomobject]@{ Dataset = "tsar2025"; Model = "mixtral"; ModelLabel = "Mixtral 8x7B"; Prompt = "iso_examples"; PromptLabel = "iso+examples"; Strategy = "few"; Sampling = "random"; Role = "Comparative"; Reason = "Representative ISO+examples few-shot configuration for comparison." }
)

function SelectedReportHref($config) {
    $modelPrefix = if ($config.Model -eq "llama") { "predictions_llama3_1_8b" } else { "predictions_mixtral_latest" }
    $stem = "$modelPrefix`_$($config.Dataset)_$($config.Prompt)_$($config.Strategy)"
    if ($config.Strategy -eq "few" -and $config.Sampling) {
        $stem += "_$($config.Sampling)"
    }
    return "$($config.Model)/$($config.Dataset)/$stem`_lowest_sari.html"
}

function RoleClass($role) {
    $roleText = [string]$role
    if ($roleText.StartsWith("High")) { return "role-high" }
    if ($roleText.StartsWith("Comparative")) { return "role-compare" }
    return "role-low"
}

$selectionSections = New-Object System.Collections.Generic.List[string]
foreach ($dataset in $DatasetOrder) {
    $configsForDataset = @($SelectedConfigs | Where-Object { $_.Dataset -eq $dataset })
    if ($configsForDataset.Count -eq 0) { continue }
    $datasetName = if ($dataset -eq "tsar2025") { "TSAR 2025" } else { (Get-Culture).TextInfo.ToTitleCase($dataset) }
    $rowsHtml = New-Object System.Collections.Generic.List[string]
    foreach ($config in $configsForDataset) {
        $href = SelectedReportHref $config
        $samplingText = if ($config.Sampling) { $config.Sampling } else { "--" }
        $rowsHtml.Add(@"
<tr>
  <td>$(HtmlEncode $config.ModelLabel)</td>
  <td><code>$(HtmlEncode $config.PromptLabel)</code></td>
  <td>$(HtmlEncode $config.Strategy)</td>
  <td>$(HtmlEncode $samplingText)</td>
  <td class="$(RoleClass $config.Role)">$(HtmlEncode $config.Role)</td>
  <td>$(HtmlEncode $config.Reason)</td>
  <td><a href="$(HtmlEncode $href)">Open report</a></td>
</tr>
"@) | Out-Null
    }
    $selectionSections.Add(@"
<section>
<h2>$(HtmlEncode $datasetName)</h2>
<table>
<thead>
<tr><th>Model</th><th>Prompt</th><th>Strategy</th><th>Sampling</th><th>Role</th><th>Main reason</th><th>HTML report</th></tr>
</thead>
<tbody>
$($rowsHtml -join "`n")
</tbody>
</table>
</section>
"@) | Out-Null
}

$selectionHtml = @"
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Experiment Selection for Error Analysis</title>
  <style>
$IndexCss
  </style>
</head>
<body>
  <main>
    <section>
      <h1>Experiment Selection for Error Analysis</h1>
      <p>This document summarizes the 18 configurations selected for the qualitative error analysis: six configurations per dataset, with three configurations for Llama 3.1 8B and three for Mixtral 8x7B.</p>
      <p>For each model and dataset, the selection includes a high-performing configuration, a lower-performing or diagnostically relevant configuration, and an additional comparative configuration chosen to examine prompt design or example selection effects.</p>
      <p>Each linked report contains the 15 examples with the lowest SARI scores for that configuration.</p>
      <p><a href="all_error_analysis_reports.html">Open the full report index</a></p>
    </section>
    $($selectionSections -join "`n")
  </main>
</body>
</html>
"@

Set-Content -Path (Join-Path $OutputRoot "error_analysis_experiment_selection.html") -Value $selectionHtml -Encoding UTF8

Write-Host "Generated $($Reports.Count) reports in old-style format under $OutputRoot"
