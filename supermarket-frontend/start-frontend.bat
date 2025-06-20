@echo off
echo 🚀 启动超市管理系统前端...
echo.

REM 设置Node.js路径
set PATH=D:\nodejs;%PATH%

REM 检查Node.js是否可用
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未找到，请检查安装路径
    pause
    exit /b 1
)

echo ✅ Node.js版本检查通过
node --version
npm.cmd --version

REM 检查是否安装了依赖
if not exist "node_modules" (
    echo 📦 正在安装依赖...
    npm.cmd install
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

echo 🔥 启动开发服务器...
echo 前端地址将是: http://localhost:3000
echo 请等待服务器启动完成...
echo.

npm.cmd run dev

pause 