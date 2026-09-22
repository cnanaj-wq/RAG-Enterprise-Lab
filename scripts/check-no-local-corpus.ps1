$forbidden = @("data\raw", "data\processed", "documents", "embeddings", "vectorstore")
$found = @()

foreach ($path in $forbidden) {
    if (Test-Path $path) {
        $items = Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue
        if ($items.Count -gt 0) { $found += $path }
    }
}

if ($found.Count -gt 0) {
    Write-Error "Local corpus detected in: $($found -join ', ')"
    exit 1
}

Write-Host "OK - no local corpus detected."
