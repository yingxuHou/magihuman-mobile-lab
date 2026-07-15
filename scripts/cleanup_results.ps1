$ErrorActionPreference = "Stop"

param(
    [string] $DataDir = "api_data",
    [int] $TtlSeconds = 86400
)

python -m backend.retention --data-dir $DataDir --ttl-seconds $TtlSeconds

