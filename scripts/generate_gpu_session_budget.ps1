param(
  [string]$Config = "",
  [ValidateSet("p01", "required_suite", "complete")]
  [string]$Profile = "p01",
  [string]$Output = "",
  [ValidateSet("markdown", "json")]
  [string]$Format = "markdown",
  [switch]$CreateTemplate,
  [switch]$Strict,
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ExtraArgs = @()
)

$PythonArgs = @("-m", "backend.gpu_session_budget", "--profile", $Profile, "--format", $Format)
if ($Config) { $PythonArgs += @("--config", $Config) }
if ($Output) { $PythonArgs += @("--output", $Output) }
if ($CreateTemplate) { $PythonArgs += "--create-template" }
if ($Strict) { $PythonArgs += "--strict" }
if ($ExtraArgs) { $PythonArgs += $ExtraArgs }

python @PythonArgs
