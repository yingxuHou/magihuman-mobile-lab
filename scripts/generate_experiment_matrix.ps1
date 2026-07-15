$ErrorActionPreference = "Stop"

param(
    [string] $Output = "run_configs/experiment_matrix.json",
    [ValidateSet("json", "markdown")]
    [string] $Format = "json"
)

python -m backend.experiment_matrix --output $Output --format $Format

