<#
============================================================
 趣配音 × GitHub Copilot Demo — 一键启动全部 3 个 demo (PowerShell 原生)

   Demo 1 打标签    -> http://localhost:8501  (Streamlit)
   Demo 2 班级看板  -> http://localhost:8000  (FastAPI)
   Demo 3 审核服务  -> http://localhost:3000  (Node / Express)

 用法 (PowerShell):
   .\start-all.ps1              # 在线模式
   .\start-all.ps1 -Offline     # Demo1 走离线兜底 (现场断网可用)
   Ctrl+C                       # 一次性停止全部

 首次若被执行策略拦截:
   powershell -ExecutionPolicy Bypass -File .\start-all.ps1

 依赖:
   - Python: 优先用 repo 内 .venv，其次 PATH 上能 import streamlit 的 python
           首次若都没有，会用 uv 自动建 .venv 并装依赖 (需先装 uv)
 - Node 18+: demo3 首次会自动 npm install
============================================================
#>
[CmdletBinding()]
param(
    [switch]$Offline
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
Set-Location $Root

# 离线开关: -Offline 参数 或 环境变量 OFFLINE=1
$OfflineMode = $Offline -or ($env:OFFLINE -eq '1')

# ------------------------------------------------------------
# 选择 Python 解释器
# ------------------------------------------------------------
function Find-Python {
    $candidates = @()
    $venvWin = Join-Path $Root '.venv\Scripts\python.exe'
    if (Test-Path $venvWin) { $candidates += $venvWin }
    $candidates += 'python', 'py'

    $firstOk = $null
    foreach ($c in $candidates) {
        $resolved = (Get-Command $c -ErrorAction SilentlyContinue)
        if (-not $resolved -and -not (Test-Path $c)) { continue }
        # 能正常运行?
        & $c -c "import sys" 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { continue }
        # 能 import streamlit?
        & $c -c "import streamlit" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { return $c }
        if (-not $firstOk) { $firstOk = $c }
    }
    return $firstOk
}

$PY = Find-Python
if (-not $PY) {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "❌ 未装 streamlit 且未找到 uv，无法自动建环境。" -ForegroundColor Red
        Write-Host "   方案A: 安装 uv (https://docs.astral.sh/uv/) 后重跑本脚本"
        Write-Host "   方案B: 手动 python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt"
        exit 1
    }
    Write-Host "🧰 首次运行：创建 .venv 并安装 Python 依赖 (uv, 约 1-2 分钟) ..." -ForegroundColor Yellow
    uv venv .venv --python 3.14
    if ($LASTEXITCODE -ne 0) { uv venv .venv }
    if ($LASTEXITCODE -ne 0) { Write-Host "❌ uv venv 失败" -ForegroundColor Red; exit 1 }
    $venvPy = Join-Path $Root '.venv\Scripts\python.exe'
    uv pip install --python $venvPy -r (Join-Path $Root 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { Write-Host "❌ 依赖安装失败" -ForegroundColor Red; exit 1 }
    $PY = Find-Python
}
if (-not $PY) {
    Write-Host "❌ Python 环境就绪失败，请检查上面的报错。" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ 未找到 node (需要 Node 18+)" -ForegroundColor Red
    exit 1
}

$LogDir = Join-Path $Root '.run-logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# ------------------------------------------------------------
# 递归结束进程树 (streamlit / uvicorn 会派生子进程)
# ------------------------------------------------------------
function Stop-Tree([int]$procId) {
    Get-CimInstance Win32_Process -Filter "ParentProcessId=$procId" -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Tree $_.ProcessId }
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
}

$procs = @()

function Start-Demo([string]$name, [string]$workdir, [string]$file, [string[]]$cmdArgs) {
    $out = Join-Path $LogDir "$name.log"
    $err = Join-Path $LogDir "$name.err.log"
    $p = Start-Process -FilePath $file -ArgumentList $cmdArgs `
        -WorkingDirectory $workdir -NoNewWindow -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
    return $p
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " 🎬 趣配音 × GitHub Copilot — 一键启动 (PowerShell)"
Write-Host "    Python: $PY"
if ($OfflineMode) {
    Write-Host "    模式:   🛟 OFFLINE (Demo1 读 ideal_tags.json, 不联网)"
} else {
    Write-Host "    模式:   🌐 在线 (Demo1 调 GitHub Copilot; 断网请加 -Offline)"
}
Write-Host "============================================================" -ForegroundColor Cyan

try {
    # ---- Demo 1: Streamlit (8501) ----
    Write-Host "▶ [1/3] Demo1 打标签 (8501) ..."
    $env:OFFLINE = if ($OfflineMode) { '1' } else { '0' }
    $procs += Start-Demo 'demo1' (Join-Path $Root 'demo1-auto-tagging') $PY @(
        '-m', 'streamlit', 'run', 'app.py',
        '--server.port', '8501', '--server.address', '0.0.0.0',
        '--server.headless', 'true', '--browser.gatherUsageStats', 'false'
    )

    # ---- Demo 2: FastAPI (8000) ----
    Write-Host "▶ [2/3] Demo2 班级看板 (8000) ..."
    $demo2Dir = Join-Path $Root 'demo2-classroom-dashboard'
    if (-not (Test-Path (Join-Path $demo2Dir 'data\classroom.db'))) {
        Write-Host "  ↳ 首次运行，生成 mock 数据 (seed.py) ..."
        Push-Location $demo2Dir; & $PY seed.py; Pop-Location
    }
    $procs += Start-Demo 'demo2' $demo2Dir $PY @(
        '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'
    )

    # ---- Demo 3: Node / Express (3000) ----
    Write-Host "▶ [3/3] Demo3 审核服务 (3000) ..."
    $demo3Dir = Join-Path $Root 'demo3-review-pipeline'
    if (-not (Test-Path (Join-Path $demo3Dir 'node_modules'))) {
        Write-Host "  ↳ 首次运行，npm install ..."
        Push-Location $demo3Dir; npm install; Pop-Location
    }
    $nodeExe = (Get-Command node).Source
    $procs += Start-Demo 'demo3' $demo3Dir $nodeExe @('src/server.js')

    Write-Host ""
    Write-Host "⏳ 等待服务就绪 (~8s) ..."
    Start-Sleep -Seconds 8

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "✅ 全部启动完成！浏览器打开:" -ForegroundColor Green
    Write-Host "   Demo 1 打标签    -> http://localhost:8501"
    Write-Host "   Demo 2 班级看板  -> http://localhost:8000"
    Write-Host "   Demo 3 审核服务  -> http://localhost:3000"
    Write-Host ""
    Write-Host "📜 日志: $LogDir\demo{1,2,3}.log"
    Write-Host "🛑 停止: 在本窗口按 Ctrl+C (一次性停止全部)"
    Write-Host "============================================================" -ForegroundColor Green

    # 阻塞直到 Ctrl+C
    while ($true) { Start-Sleep -Seconds 1 }
}
finally {
    Write-Host ""
    Write-Host "🛑 停止全部 demo ..." -ForegroundColor Yellow
    foreach ($p in $procs) {
        if ($p -and -not $p.HasExited) { Stop-Tree $p.Id }
    }
    Write-Host "✅ 已全部停止" -ForegroundColor Yellow
}
