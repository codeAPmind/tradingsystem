@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   港股代码格式化测试
echo ========================================
echo.

python test_backtest_hk.py

echo.
echo ========================================
echo   测试完成
echo ========================================
echo.
echo 提示: 运行 python main.py 启动系统测试回测功能
echo.
pause
