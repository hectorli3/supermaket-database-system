# 超市管理系统前端启动脚本 (PowerShell版本)

Write-Host "🚀 启动超市管理系统前端..." -ForegroundColor Green
Write-Host ""

# 设置Node.js路径
$env:PATH = "D:\nodejs;" + $env:PATH

# 检查Node.js是否可用
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js版本: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js未找到，请检查安装路径" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 检查npm是否可用
try {
    $npmVersion = npm.cmd --version
    Write-Host "✅ npm版本: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ npm未找到" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 检查是否安装了依赖
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 正在安装依赖..." -ForegroundColor Yellow
    npm.cmd install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 依赖安装失败" -ForegroundColor Red
        Read-Host "按任意键退出"
        exit 1
    }
    Write-Host "✅ 依赖安装完成" -ForegroundColor Green
}

Write-Host ""
Write-Host "🔥 启动开发服务器..." -ForegroundColor Cyan
Write-Host "前端地址: http://localhost:3000" -ForegroundColor Yellow
Write-Host "请等待服务器启动完成..." -ForegroundColor Yellow
Write-Host ""

# 启动开发服务器
npm.cmd run dev 