@echo off
REM 前端依赖管理脚本 (Windows)

setlocal enabledelayedexpansion

REM 颜色设置（Windows 10+）
set "INFO=[94m"
set "SUCCESS=[92m"
set "WARNING=[93m"
set "ERROR=[91m"
set "NC=[0m"

if "%1"=="" goto :menu
if "%1"=="check-versions" goto :check_versions
if "%1"=="check-outdated" goto :check_outdated
if "%1"=="audit" goto :audit_deps
if "%1"=="update" goto :update_deps
if "%1"=="clean" goto :clean_deps
if "%1"=="all" goto :run_all
goto :usage

:check_versions
echo %INFO%检查Node和npm版本...%NC%
node -v
npm -v
echo %SUCCESS%版本检查完成%NC%
goto :end

:check_outdated
echo %INFO%检查过时的依赖...%NC%
npm outdated
goto :end

:audit_deps
echo %INFO%运行安全审计...%NC%
echo %INFO%尝试自动修复安全漏洞...%NC%
call npm audit fix
echo %INFO%检查剩余的安全漏洞...%NC%
call npm audit --audit-level=high
echo %SUCCESS%安全审计完成%NC%
goto :end

:update_deps
echo %INFO%更新依赖...%NC%
echo %INFO%执行npm update...%NC%
call npm update
echo %INFO%再次尝试修复安全漏洞...%NC%
call npm audit fix
echo %SUCCESS%依赖更新完成%NC%
echo %INFO%请检查package.json的变化并测试应用%NC%
goto :end

:clean_deps
echo %INFO%清理node_modules和package-lock.json...%NC%
set /p confirm="确定要删除node_modules和package-lock.json吗？(y/N): "
if /i "%confirm%"=="y" (
    if exist node_modules rmdir /s /q node_modules
    if exist package-lock.json del package-lock.json
    echo %SUCCESS%清理完成%NC%
    echo %INFO%运行 'npm install' 重新安装依赖%NC%
) else (
    echo %INFO%取消清理%NC%
)
goto :end

:run_all
call :check_versions
echo.
call :check_outdated
echo.
call :audit_deps
goto :end

:menu
:menu_loop
cls
echo ==================================
echo    前端依赖管理工具
echo ==================================
echo 1. 检查Node和npm版本
echo 2. 检查过时的依赖
echo 3. 运行安全审计
echo 4. 更新依赖
echo 5. 清理依赖
echo 6. 全部检查（版本+过时+审计）
echo 0. 退出
echo ==================================
set /p choice="请选择操作 [0-6]: "

if "%choice%"=="1" call :check_versions
if "%choice%"=="2" call :check_outdated
if "%choice%"=="3" call :audit_deps
if "%choice%"=="4" call :update_deps
if "%choice%"=="5" call :clean_deps
if "%choice%"=="6" call :run_all
if "%choice%"=="0" goto :end

echo.
pause
goto :menu_loop

:usage
echo 用法: %~nx0 [check-versions^|check-outdated^|audit^|update^|clean^|all]
echo.
echo 选项:
echo   check-versions  - 检查Node和npm版本
echo   check-outdated  - 检查过时的依赖
echo   audit           - 运行安全审计
echo   update          - 更新依赖
echo   clean           - 清理依赖
echo   all             - 运行所有检查
exit /b 1

:end
