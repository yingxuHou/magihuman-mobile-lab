param(
  [string]$LogDir = "logs",
  [string]$ResultDir = "outputs/experiment-results",
  [ValidateSet("shell", "json", "markdown")]
  [string]$Format = "shell",
  [switch]$IncludeOptional,
  [switch]$Rerun,
  [switch]$Execute,
  [switch]$Force
)

$PythonArgs = @(
  "-m", "backend.experiment_suite",
  "--log-dir", $LogDir,
  "--result-dir", $ResultDir,
  "--format", $Format
)

if ($IncludeOptional) { $PythonArgs += "--include-optional" }
if ($Rerun) { $PythonArgs += "--rerun" }
if ($Execute) { $PythonArgs += "--execute" }
if ($Force) { $PythonArgs += "--force" }

python @PythonArgs
