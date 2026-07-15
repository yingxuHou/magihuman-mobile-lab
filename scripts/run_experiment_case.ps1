$ErrorActionPreference = "Stop"

param(
    [Parameter(Mandatory = $true)]
    [string] $Case,
    [string] $Matrix = "",
    [string] $LogDir = "logs",
    [string] $ResultDir = "outputs/experiment-results",
    [switch] $Execute,
    [switch] $Force,
    [ValidateSet("shell", "json")]
    [string] $Format = "shell"
)

$argsList = @(
    "-m", "backend.experiment_runner",
    "--case", $Case,
    "--log-dir", $LogDir,
    "--result-dir", $ResultDir,
    "--format", $Format
)

if ($Matrix -ne "") {
    $argsList += @("--matrix", $Matrix)
}
if ($Execute) {
    $argsList += "--execute"
}
if ($Force) {
    $argsList += "--force"
}

python @argsList

