$ErrorActionPreference = "Stop"

param(
    [string] $HostName = "127.0.0.1",
    [int] $Port = 8080,
    [string] $DataDir = "api_data"
)

python -m backend.api_server --host $HostName --port $Port --data-dir $DataDir

