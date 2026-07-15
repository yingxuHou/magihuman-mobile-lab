param(
  [string]$ProjectRoot = ".",
  [string]$RepoUrl = "",
  [string]$Branch = "main",
  [string]$DockerImage = "sandai/magi-human:latest",
  [switch]$IncludeOptional,
  [switch]$Strict,
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ExtraArgs = @()
)

$PythonArgs = @(
  "-m", "backend.gpu_execution_packet",
  "--project-root", $ProjectRoot,
  "--branch", $Branch,
  "--docker-image", $DockerImage
)
if ($RepoUrl) { $PythonArgs += @("--repo-url", $RepoUrl) }
if ($IncludeOptional) { $PythonArgs += "--include-optional" }
if ($Strict) { $PythonArgs += "--strict" }
if ($ExtraArgs) { $PythonArgs += $ExtraArgs }

python @PythonArgs
