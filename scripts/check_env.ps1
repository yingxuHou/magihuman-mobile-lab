$ErrorActionPreference = "Continue"

function Run-Check {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Name,

        [Parameter(Mandatory = $true)]
        [scriptblock] $Command
    )

    Write-Host "## $Name"
    try {
        & $Command
    }
    catch {
        Write-Host "FAILED: $($_.Exception.Message)"
    }
    Write-Host ""
}

Run-Check "nvidia-smi" { nvidia-smi }
Run-Check "nvcc" { nvcc --version }
Run-Check "git" { git --version }
Run-Check "git-lfs" { git lfs version }
Run-Check "conda" { conda --version }
Run-Check "docker" { docker --version }
Run-Check "ffmpeg" { ffmpeg -version }
Run-Check "python" { python --version }
Run-Check "torch" { python -c "import torch; print(torch.__version__)" }

Run-Check "os" {
    Get-CimInstance Win32_OperatingSystem |
        Select-Object Caption,Version,OSArchitecture,BuildNumber |
        Format-List
}

Run-Check "video-controller" {
    Get-CimInstance Win32_VideoController |
        Select-Object Name,AdapterRAM,DriverVersion,VideoProcessor |
        Format-List
}

Run-Check "disk-d" {
    Get-PSDrive -Name D |
        Select-Object Name,Used,Free,Root |
        Format-List
}
