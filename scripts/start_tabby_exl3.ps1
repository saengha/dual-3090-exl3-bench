# TabbyAPI(ExLlamaV3) 두 프로세스. GPU 0 -> 5000, GPU 1 -> 5001.
# 필요한 환경 변수:
#   TABBYAPI_DIR   main.py 가 있는 TabbyAPI 폴더
#   EXL_MODEL_DIR  EXL3 가중치 폴더의 부모
# 모델 이름 (둘 다 쓰거나, EXL_MODEL_NAME 하나로 둘 다):
#   EXL_MODEL_NAME_A  GPU0 (예: Qwen3.8-27B-Abliterated-EXL3-4.5bpw)
#   EXL_MODEL_NAME_B  GPU1 (같은 Qwen, 또는 EXL_MODEL_NAME 하나로 둘 다)
# 선택:
#   EXL_CONTEXT    기본 16384

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $env:TABBYAPI_DIR) { $env:TABBYAPI_DIR = "D:\tabbyAPI" }
if (-not $env:EXL_MODEL_DIR) { $env:EXL_MODEL_DIR = "D:\models\exl3" }
if (-not $env:EXL_MODEL_NAME_A) { $env:EXL_MODEL_NAME_A = "Qwen3.8-27B-Abliterated-EXL3-4.5bpw" }
if (-not $env:EXL_MODEL_NAME_B) { $env:EXL_MODEL_NAME_B = "Qwen3.8-27B-Abliterated-EXL3-4.5bpw" }
$Tabby = $env:TABBYAPI_DIR
$ModelDir = $env:EXL_MODEL_DIR
$Shared = $env:EXL_MODEL_NAME
$ModelA = $env:EXL_MODEL_NAME_A
if (-not $ModelA) { $ModelA = $Shared }
$ModelB = $env:EXL_MODEL_NAME_B
if (-not $ModelB) { $ModelB = $Shared }
$Context = if ($env:EXL_CONTEXT) { $env:EXL_CONTEXT } else { "16384" }
$Py = $env:TABBYAPI_PYTHON
if (-not $Py) {
    $venvPy = Join-Path $Tabby ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) { $Py = $venvPy } else { $Py = "python" }
}

if (-not $Tabby -or -not $ModelDir -or -not $ModelA -or -not $ModelB) {
    Write-Host "TABBYAPI_DIR, EXL_MODEL_DIR, EXL_MODEL_NAME_A, EXL_MODEL_NAME_B 를 설정한 뒤 다시 실행하세요."
    Write-Host "모델 없이 시스템을 보려면 scripts\start_system.ps1 -Mock"
    exit 1
}

$Main = Join-Path $Tabby "main.py"
if (-not (Test-Path $Main)) {
    Write-Host "TabbyAPI main.py 를 찾지 못했습니다: $Main"
    exit 1
}

$Instances = @(
    @{ Name = "a"; Gpu = "0"; Port = 5000; Model = $ModelA },
    @{ Name = "b"; Gpu = "1"; Port = 5001; Model = $ModelB }
)

foreach ($item in $Instances) {
    $Work = Join-Path $Root ("data\\tabby\\" + $item.Name)
    New-Item -ItemType Directory -Force -Path $Work | Out-Null
    $Config = @"
network:
  host: 127.0.0.1
  port: $($item.Port)
  disable_auth: true
model:
  model_dir: "$($ModelDir -replace '\\','/')"
  model_name: "$($item.Model)"
  max_seq_len: $Context
  cache_size: $Context
  gpu_split_auto: true
  cache_mode: Q4
  template_vars_default:
    enable_thinking: false
sampling:
  override_preset: safe_defaults
"@
    Set-Content -Path (Join-Path $Work "config.yml") -Value $Config -Encoding utf8
    $Presets = Join-Path $Tabby "sampler_overrides"
    $LocalPresets = Join-Path $Work "sampler_overrides"
    if ((Test-Path $Presets) -and -not (Test-Path $LocalPresets)) {
        Copy-Item -Recurse $Presets $LocalPresets
    }
    $Command = "`$env:CUDA_VISIBLE_DEVICES='$($item.Gpu)'; `$env:PYTHONUNBUFFERED='1'; Set-Location -LiteralPath '$Work'; & '$Py' '$Main'"
    Start-Process -FilePath "powershell" -ArgumentList @("-NoExit", "-Command", $Command) | Out-Null
    Write-Host "GPU $($item.Gpu) $($item.Model) -> http://127.0.0.1:$($item.Port)/v1"
}
exit 0
