param(
  [string]$LogDir = "logs",
  [string]$Matrix = "",
  [ValidateSet("markdown", "json")]
  [string]$Format = "markdown"
)

$PythonArgs = @("-m", "backend.feasibility_decision", "--log-dir", $LogDir, "--format", $Format)
if ($Matrix) {
  $PythonArgs += @("--matrix", $Matrix)
}

python @PythonArgs
