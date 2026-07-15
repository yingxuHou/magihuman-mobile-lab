param(
  [string]$LogDir = "logs",
  [string]$QualityReview = "",
  [string]$CostReview = "",
  [string]$FinalReportOutput = "docs/mobile-feasibility-report.md",
  [string]$Output = "",
  [ValidateSet("markdown", "json")]
  [string]$Format = "markdown"
)

$PythonArgs = @("-m", "backend.evidence_import", "--log-dir", $LogDir, "--format", $Format)
if ($QualityReview) { $PythonArgs += @("--quality-review", $QualityReview) }
if ($CostReview) { $PythonArgs += @("--cost-review", $CostReview) }
if ($FinalReportOutput) { $PythonArgs += @("--final-report-output", $FinalReportOutput) }
if ($Output) { $PythonArgs += @("--output", $Output) }

python @PythonArgs
