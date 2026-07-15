$ErrorActionPreference = "Stop"

param(
    [string] $DataDir = "api_data",
    [string] $OutputDir = "outputs/api-results",
    [Parameter(Mandatory = $true)]
    [string] $Command
)

python -m backend.worker --data-dir $DataDir --output-dir $OutputDir --command $Command

