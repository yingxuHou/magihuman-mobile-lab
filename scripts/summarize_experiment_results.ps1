$ErrorActionPreference = "Stop"

param(
    [string] $Matrix = "",
    [string] $LogDir = "logs",
    [string] $Output = "",
    [ValidateSet("json", "markdown")]
    [string] $Format = "markdown"
)

$argsList = @("-m", "backend.experiment_results", "--log-dir", $LogDir, "--format", $Format)
if ($Matrix -ne "") {
    $argsList += @("--matrix", $Matrix)
}
if ($Output -ne "") {
    $argsList += @("--output", $Output)
}

python @argsList

