# distribution_tier: starter_kit
param(
  [Parameter(Mandatory=$true)][string]$AuditId
)

$root = "docs/superpowers/plans/audit/$AuditId"
$dirs = @(
  $root,
  "$root/evidence/images",
  "$root/evidence/results",
  "$root/repro/inputs"
)

foreach ($d in $dirs) {
  New-Item -ItemType Directory -Path $d -Force | Out-Null
}

$template = "docs/operating_system/templates/audit-report-with-evidence-template.md"
$report = "$root/report.md"
if (Test-Path $template) {
  Copy-Item $template $report -Force
} else {
  "# Audit Report`n" | Out-File -FilePath $report -Encoding utf8
}

$manifest = @"
audit_id: $AuditId
created_at: $(Get-Date -Format o)
artifacts: []
"@
$manifest | Out-File -FilePath "$root/manifest.yaml" -Encoding utf8

"# Reproduction Steps" | Out-File -FilePath "$root/repro/steps.md" -Encoding utf8
"# Repro commands" | Out-File -FilePath "$root/repro/commands.ps1" -Encoding utf8

Write-Host "Created audit bundle at $root"
