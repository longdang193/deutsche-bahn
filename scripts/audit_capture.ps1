# distribution_tier: starter_kit
param(
  [Parameter(Mandatory=$true)][string]$AuditId,
  [Parameter(Mandatory=$true)][string]$SourceFile,
  [Parameter(Mandatory=$true)][ValidateSet('image','result','log','other')][string]$Type
)

$root = "docs/superpowers/plans/audit/$AuditId"
$manifestPath = "$root/manifest.yaml"
if (-not (Test-Path $root)) { throw "Audit bundle not found: $root" }
if (-not (Test-Path $SourceFile)) { throw "Source file not found: $SourceFile" }

switch ($Type) {
  'image' { $destDir = "$root/evidence/images" }
  default { $destDir = "$root/evidence/results" }
}

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
  "audit_id: $AuditId`ncreated_at: $timestamp`nartifacts:`n" | Out-File -FilePath $manifestPath -Encoding utf8
}

Add-Content -Path $manifestPath -Value $entry
Write-Host "Captured $SourceFile -> $dest"
