@echo off
chcp 65001 >nul
echo ========================================
echo 量化交易系统 - 演示模式
echo ========================================
echo.

REM 激活conda环境
call conda activate trading_system

REM 运行演示
python main.py --demo

pause
