param(
  [string]$ProjectRoot = ".",
  [string]$RepoUrl = "",
  [string]$Branch = "main",
  [string]$DockerImage = "sandai/magi-human:latest",
  [string]$BudgetConfig = "docs/gpu-session-budget.json",
  [switch]$IncludeOptional,
  [switch]$Strict,
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ExtraArgs = @()
)

$PythonArgs = @(
  "-m", "backend.gpu_execution_packet",
  "--project-root", $ProjectRoot,
  "--branch", $Branch,
  "--docker-image", $DockerImage,
  "--budget-config", $BudgetConfig
)
if ($RepoUrl) { $PythonArgs += @("--repo-url", $RepoUrl) }
if ($IncludeOptional) { $PythonArgs += "--include-optional" }
if ($Strict) { $PythonArgs += "--strict" }
if ($ExtraArgs) { $PythonArgs += $ExtraArgs }

python @PythonArgs
