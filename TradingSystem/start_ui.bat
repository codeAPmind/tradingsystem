@echo off
chcp 65001 >nul
echo ========================================
echo 量化交易系统 - UI模式启动
echo ========================================
echo.

REM 激活conda环境
call conda activate trading_system

REM 启动UI
python main.py --ui

pause
