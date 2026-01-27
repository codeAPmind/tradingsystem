@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   美股+港股数据测试
echo ========================================
echo.
echo 功能: 测试美股和港股数据获取
echo.
echo 要求:
echo 1. 美股: 需要 FINANCIAL_DATASETS_API_KEY
echo 2. 港股: 需要 Futu OpenD 已启动
echo.
pause

python test_us_hk_data.py

echo.
echo ========================================
echo   测试完成
echo ========================================
echo.
pause
