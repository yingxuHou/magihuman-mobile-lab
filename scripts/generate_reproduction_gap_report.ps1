param(
  [string]$LogDir = "logs",
  [string]$ResultDir = "outputs/experiment-results",
  [string]$P01ResultPath = "outputs/smoke-test/P01.mp4",
  [string]$P01Manifest = "docs/p01-smoke-manifest.json",
  [string]$QualityReview = "",
  [string]$CostReview = "",
  [switch]$Strict,
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ExtraArgs = @()
)

$PythonArgs = @(
  "-m", "backend.reproduction_gap_report",
  "--log-dir", $LogDir,
  "--result-dir", $ResultDir,
  "--p01-result-path", $P01ResultPath,
  "--p01-manifest", $P01Manifest
)
if ($QualityReview) { $PythonArgs += @("--quality-review", $QualityReview) }
if ($CostReview) { $PythonArgs += @("--cost-review", $CostReview) }
if ($Strict) { $PythonArgs += "--strict" }
if ($ExtraArgs) { $PythonArgs += $ExtraArgs }

python @PythonArgs
