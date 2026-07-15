param(
  [string]$Review = "",
  [string]$Output = "",
  [ValidateSet("markdown", "json")]
  [string]$Format = "markdown",
  [switch]$CreateTemplate
)

$PythonArgs = @("-m", "backend.quality_review", "--format", $Format)
if ($Review) { $PythonArgs += @("--review", $Review) }
if ($Output) { $PythonArgs += @("--output", $Output) }
if ($CreateTemplate) { $PythonArgs += "--create-template" }

python @PythonArgs
