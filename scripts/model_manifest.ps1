$ErrorActionPreference = "Stop"

$models = @(
    "GAIR/daVinci-MagiHuman",
    "google/t5gemma-9b-9b-ul2",
    "stabilityai/stable-audio-open-1.0",
    "Wan-AI/Wan2.2-TI2V-5B"
)

foreach ($modelId in $models) {
    $uri = "https://huggingface.co/api/models/$modelId?blobs=true"
    $model = Invoke-RestMethod -Uri $uri -TimeoutSec 120
    $siblings = @($model.siblings)
    $total = ($siblings | Measure-Object -Property size -Sum).Sum
    $largest = $siblings | Sort-Object size -Descending | Select-Object -First 1

    [pscustomobject]@{
        id = $model.id
        sha = $model.sha
        lastModified = $model.lastModified
        gated = $model.gated
        private = $model.private
        fileCount = $siblings.Count
        totalGiB = "{0:N2}" -f ($total / 1GB)
        largest = $largest.rfilename
        largestGiB = "{0:N2}" -f ($largest.size / 1GB)
    }
}
