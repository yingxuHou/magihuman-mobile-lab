param(
  [Parameter(Mandatory = $true)]
  [string]$Archive,
  [string]$ProjectRoot = ".",
  [switch]$Strict,
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ExtraArgs = @()
)

$PythonArgs = @(
  "-m", "backend.gpu_evidence_import_workflow",
  "--archive", $Archive,
  "--project-root", $ProjectRoot
)
if ($Strict) { $PythonArgs += "--strict" }
if ($ExtraArgs) { $PythonArgs += $ExtraArgs }

python @PythonArgs
