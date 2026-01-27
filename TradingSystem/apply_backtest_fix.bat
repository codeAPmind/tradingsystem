@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   回测引擎修复工具
echo ========================================
echo.
echo 功能: 修复 backtest_engine.py 中的 date 处理问题
echo.
echo 问题: 'str' object has no attribute 'to_pydatetime'
echo 修复: 自动将date列转换为datetime类型
echo.
echo 按任意键开始修复...
pause >nul

python apply_backtest_fix.py

echo.
echo ========================================
echo   修复完成
echo ========================================
echo.
pause
