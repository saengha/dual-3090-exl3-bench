# Dual RTX 3090 EXL3 benchmark launcher.
# Starts nothing itself: TabbyAPI must already be serving the selected model
# on 127.0.0.1:5000 (GPU 0) and, for dual-gpu, 127.0.0.1:5001 (GPU 1).
# Health checks run first. If an endpoint is down, this script exits non-zero
# and does not write benchmark rows.
#
# Results are pending until this script is executed on the Dual RTX 3090 host.
# The harness does not fill in TTFT, TPS, VRAM, power, or temperature.

[CmdletBinding()]
param(
    [ValidateSet(
        "auto",
        "Qwen3.8-27B-Abliterated-EXL3-4.5bpw",
        "gemma-4-31B-it-uncensored-EXL3-4.0bpw"
    )]
    [string]$Model = "auto",

    [ValidateSet("all", "single-gpu", "dual-gpu")]
    [string]$Mode = "all",

    [string]$OutDir = "bench_results",

    [int]$Warmup = 1,

    [int]$Requests = 0,

    [double]$TimeoutSec = 600,

    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

$Qwen = "Qwen3.8-27B-Abliterated-EXL3-4.5bpw"
$Gemma = "gemma-4-31B-it-uncensored-EXL3-4.0bpw"
$KnownPresets = @($Qwen, $Gemma)

if ($Mode -eq "all") {
    $Modes = @("single-gpu", "dual-gpu")
} else {
    $Modes = @($Mode)
}

function Get-TabbyModels {
    param([Parameter(Mandatory = $true)][int]$Port)
    $Uri = "http://127.0.0.1:$Port/v1/models"
    try {
        $Response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 5
    } catch {
        Write-Host "ERROR: TabbyAPI health check failed at $Uri"
        Write-Host $_.Exception.Message
        return $null
    }
    if ($Response.StatusCode -ne 200) {
        Write-Host "ERROR: $Uri returned HTTP $($Response.StatusCode)"
        return $null
    }
    Write-Host "TabbyAPI healthy at $Uri"
    $Parsed = $Response.Content | ConvertFrom-Json
    return @($Parsed.data | ForEach-Object { $_.id })
}

$NeedSecondGpu = $Modes -contains "dual-gpu"
$LoadedGpu0 = Get-TabbyModels -Port 5000
if ($null -eq $LoadedGpu0) {
    exit 1
}
if ($NeedSecondGpu) {
    $LoadedGpu1 = Get-TabbyModels -Port 5001
    if ($null -eq $LoadedGpu1) {
        exit 1
    }
}

if ($Model -eq "auto") {
    $Matched = @($KnownPresets | Where-Object { $LoadedGpu0 -contains $_ })
    if ($Matched.Count -eq 0) {
        Write-Host "ERROR: Neither configured EXL3 preset ($($KnownPresets -join ', ')) is loaded on :5000 (loaded: $($LoadedGpu0 -join ', '))."
        exit 1
    }
    $Models = @($Matched[0])
    Write-Host "Auto-detected loaded EXL3 preset on GPU 0: $($Models[0])"
} else {
    $Models = @($Model)
}

Push-Location $RepoRoot
try {
    foreach ($ModelName in $Models) {
        foreach ($ModeName in $Modes) {
            if ($ModeName -eq "dual-gpu") {
                $Endpoints = "http://127.0.0.1:5000/v1,http://127.0.0.1:5001/v1"
            } else {
                $Endpoints = "http://127.0.0.1:5000/v1"
            }
            $Dest = Join-Path (Join-Path $OutDir $ModelName) $ModeName
            Write-Host "RUN model=$ModelName mode=$ModeName out=$Dest"
            $CliArgs = @(
                "-m", "bench_exl3", "run",
                "--model", $ModelName,
                "--endpoints", "$Endpoints",
                "--mode", $ModeName,
                "--prompt-lengths", "512,2048,8192",
                "--output-lengths", "128,512",
                "--concurrencies", "1,2,4,8",
                "--warmup", "$Warmup",
                "--timeout", "$TimeoutSec",
                "--out-dir", "$Dest"
            )
            if ($Requests -gt 0) {
                $CliArgs += @("--requests", "$Requests")
            }
            & $Python @CliArgs
            if ($LASTEXITCODE -ne 0) {
                Write-Host "ERROR: benchmark run failed for $ModelName ($ModeName) with exit $LASTEXITCODE"
                exit $LASTEXITCODE
            }
            $Matrix = Join-Path $Dest "matrix.json"
            & $Python -m bench_exl3 report --input "$Matrix" --out-dir "$Dest"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "ERROR: report generation failed for $ModelName ($ModeName) with exit $LASTEXITCODE"
                exit $LASTEXITCODE
            }
        }
    }
} finally {
    Pop-Location
}

Write-Host "Benchmark files are under $OutDir"
exit 0
