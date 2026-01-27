@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   港股数据获取和缓存测试
echo ========================================
echo.
echo 请确保:
echo 1. Futu OpenD 已启动
echo 2. 已登录账户
echo 3. 有港股数据权限
echo.
pause

python test_hk_data_cache.py

echo.
echo ========================================
echo   测试完成
echo ========================================
echo.
pause
