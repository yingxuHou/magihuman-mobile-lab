param(
  [string]$LogDir = "logs",
  [string]$QualityReview = "",
  [string]$CostReview = "",
  [string]$Output = "",
  [ValidateSet("markdown", "json")]
  [string]$Format = "markdown"
)

$PythonArgs = @("-m", "backend.final_report", "--log-dir", $LogDir, "--format", $Format)
if ($QualityReview) { $PythonArgs += @("--quality-review", $QualityReview) }
if ($CostReview) { $PythonArgs += @("--cost-review", $CostReview) }
if ($Output) { $PythonArgs += @("--output", $Output) }

python @PythonArgs
