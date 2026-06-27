# distribution_tier: starter_kit
param(
  [Parameter(Mandatory=$true)][string]$ReportId
)

$root = "docs/superpowers/plans/brainstorming/$ReportId"
$dirs = @(
  $root,
  "$root/context",
  "$root/evidence/inputs"
)

foreach ($d in $dirs) {
  New-Item -ItemType Directory -Path $d -Force | Out-Null
}

$template = "docs/operating_system/templates/brainstorming-detailed-report-template.md"
$report = "$root/report.md"
if (Test-Path $template) {
  Copy-Item $template $report -Force
} else {
  "# Brainstorming Detailed Report`n" | Out-File -FilePath $report -Encoding utf8
}

$manifest = @"
report_id: $ReportId
created_at: $(Get-Date -Format o)
artifacts: []
"@
$manifest | Out-File -FilePath "$root/manifest.yaml" -Encoding utf8

"# Context Summary" | Out-File -FilePath "$root/context/summary.md" -Encoding utf8

Write-Host "Created brainstorming report bundle at $root"
