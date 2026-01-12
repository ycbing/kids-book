@echo off
REM ========================================
REM AI绘本创作平台 - Windows部署脚本
REM 文件: scripts/deploy.bat
REM ========================================

SETLOCAL EnableDelayedExpansion

echo ========================================
echo    AI绘本创作平台 - Windows部署
echo ========================================
echo.

REM 检查Docker是否安装
echo [1/6] 检查Docker环境...
docker --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [错误] Docker未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [错误] Docker Compose未安装
    pause
    exit /b 1
)
echo [完成] Docker环境检查通过 ✓
echo.

REM 备份数据
echo [2/6] 备份数据...
SET BACKUP_DIR=./backups/pre-deploy-%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
SET BACKUP_DIR=%BACKUP_DIR: =0%
mkdir "%BACKUP_DIR%" 2>nul

IF EXIST ".\data\picturebook.db" (
    copy ".\data\picturebook.db" "%BACKUP_DIR%\" >nul
    echo [完成] 数据库备份: %BACKUP_DIR%\picturebook.db
)

IF EXIST ".\.env" (
    copy ".\.env" "%BACKUP_DIR%\" >nul
    echo [完成] 环境变量备份: %BACKUP_DIR%\.env
)
echo [完成] 数据备份完成 ✓
echo.

REM 检查环境变量
echo [3/6] 检查环境变量...
IF NOT EXIST ".\.env" (
    echo [警告] .env文件不存在，从模板创建...
    copy .env.example .env >nul
    echo [错误] 请编辑.env文件配置必要的环境变量后重新运行
    pause
    exit /b 1
)
echo [完成] 环境变量检查通过 ✓
echo.

REM 构建镜像
echo [4/6] 构建Docker镜像...
docker-compose build
IF %ERRORLEVEL% NEQ 0 (
    echo [错误] 镜像构建失败
    pause
    exit /b 1
)
echo [完成] 镜像构建完成 ✓
echo.

REM 停止旧服务
echo [5/6] 停止旧服务...
docker-compose down
echo [完成] 服务已停止 ✓
echo.

REM 启动新服务
echo [6/6] 启动新服务...
docker-compose up -d
IF %ERRORLEVEL% NEQ 0 (
    echo [错误] 服务启动失败
    pause
    exit /b 1
)
echo [完成] 服务启动完成 ✓
echo.

REM 等待服务健康
echo 等待服务启动...
timeout /t 10 /nobreak >nul

REM 显示服务状态
echo.
echo ========================================
echo 服务状态:
echo ========================================
docker-compose ps
echo.

echo ========================================
echo    部署完成！
echo ========================================
echo 访问地址:
echo   - 后端API: http://localhost:8000
echo   - API文档: http://localhost:8000/docs
echo   - 前端:   http://localhost:3000
echo   - Flower: http://localhost:5555
echo.
echo 查看日志: docker-compose logs -f
echo.

pause
