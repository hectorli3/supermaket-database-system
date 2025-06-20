@echo off
echo 🧹 清理前端项目依赖...
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

echo ✅ Node.js版本: 
node --version

echo 🗑️ 删除现有的node_modules目录...
if exist "node_modules" (
    rmdir /s /q "node_modules" 2>nul
    if exist "node_modules" (
        echo ⚠️ 无法完全删除node_modules，尝试强制删除...
        rd /s /q "node_modules" 2>nul
    )
)

echo 🗑️ 删除package-lock.json...
if exist "package-lock.json" (
    del "package-lock.json"
)

echo 🧹 清理npm缓存...
npm cache clean --force

echo 📦 重新安装依赖...
npm install

if errorlevel 1 (
    echo ❌ 依赖安装失败，尝试使用yarn...
    npm install -g yarn
    yarn install
)

echo ✅ 依赖安装完成！
echo.
echo 现在可以运行 start-frontend.bat 启动前端服务

pause 