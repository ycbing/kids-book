@echo off
REM 监控服务快速启动脚本 (Windows)

echo ==================================
echo     启动AI绘本平台监控服务栈
echo ==================================
echo.

REM 检查Docker是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未运行，请先启动Docker Desktop
    exit /b 1
)

REM 创建必要的目录
echo 📁 创建监控数据目录...
if not exist "monitoring\prometheus\alerts" mkdir "monitoring\prometheus\alerts"
if not exist "monitoring\grafana\provisioning" mkdir "monitoring\grafana\provisioning"
if not exist "monitoring\grafana\dashboards" mkdir "monitoring\grafana\dashboards"
if not exist "monitoring\alertmanager" mkdir "monitoring\alertmanager"

REM 启动监控服务栈
echo 🚀 启动监控服务栈...
docker-compose -f docker-compose.monitoring.yml up -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo ✅ 检查服务状态...
docker-compose -f docker-compose.monitoring.yml ps

echo.
echo ==================================
echo ✅ 监控服务栈启动成功！
echo ==================================
echo.
echo 📊 访问地址：
echo   - Prometheus: http://localhost:9090
echo   - Grafana:    http://localhost:3001 (admin/admin)
echo   - Alertmanager: http://localhost:9093
echo.
echo 📖 查看文档：
echo   - 监控指南: MONITORING_AND_ALERTING.md
echo.
echo 🔧 常用命令：
echo   - 查看日志: docker-compose -f docker-compose.monitoring.yml logs -f
echo   - 停止服务: docker-compose -f docker-compose.monitoring.yml down
echo   - 重启服务: docker-compose -f docker-compose.monitoring.yml restart
echo.
pause
