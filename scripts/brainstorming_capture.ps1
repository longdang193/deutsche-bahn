# distribution_tier: starter_kit
param(
  [Parameter(Mandatory=$true)][string]$ReportId,
  [Parameter(Mandatory=$true)][string]$SourceFile,
  [Parameter(Mandatory=$true)][ValidateSet('input','result','other')][string]$Type
)

$root = "docs/superpowers/plans/brainstorming/$ReportId"
$manifestPath = "$root/manifest.yaml"
if (-not (Test-Path $root)) { throw "Brainstorming report bundle not found: $root" }
if (-not (Test-Path $SourceFile)) { throw "Source file not found: $SourceFile" }

$destDir = "$root/evidence/inputs"
New-Item -ItemType Directory -Path $destDir -Force | Out-Null
$filename = Split-Path $SourceFile -Leaf
$dest = Join-Path $destDir $filename
Copy-Item $SourceFile $dest -Force

$hash = (Get-FileHash -Path $dest -Algorithm SHA256).Hash.ToLower()
$timestamp = Get-Date -Format o
$rel = $dest.Replace('\\','/')

$entry = @"
  - path: $rel
    type: $Type
    captured_at: $timestamp
    sha256: $hash
"@

if (-not (Test-Path $manifestPath)) {
  "report_id: $ReportId`ncreated_at: $timestamp`nartifacts:`n" | Out-File -FilePath $manifestPath -Encoding utf8
}

Add-Content -Path $manifestPath -Value $entry
Write-Host "Captured $SourceFile -> $dest"
