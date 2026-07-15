param(
  [string]$LogDir = "logs",
  [string]$ResultDir = "outputs/experiment-results",
  [string]$P01ResultPath = "outputs/smoke-test/P01.mp4",
  [string]$P01Manifest = "docs/p01-smoke-manifest.json",
  [string]$QualityReview = "docs/quality-review.json",
  [string]$CostReview = "docs/cost-review.json",
  [switch]$Overwrite,
  [switch]$Strict,
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ExtraArgs = @()
)

$PythonArgs = @(
  "-m", "backend.review_readiness",
  "--log-dir", $LogDir,
  "--result-dir", $ResultDir,
  "--p01-result-path", $P01ResultPath,
  "--p01-manifest", $P01Manifest,
  "--quality-review", $QualityReview,
  "--cost-review", $CostReview,
  "--create-templates"
)
if ($Overwrite) { $PythonArgs += "--overwrite" }
if ($Strict) { $PythonArgs += "--strict" }
if ($ExtraArgs) { $PythonArgs += $ExtraArgs }

python @PythonArgs
