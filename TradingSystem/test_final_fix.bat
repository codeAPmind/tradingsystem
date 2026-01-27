@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   港股回测完整修复测试
echo ========================================
echo.
echo 请确保:
echo 1. Futu OpenD 已启动
echo 2. 已登录账户
echo 3. 有港股数据权限
echo.
pause

python test_final_fix.py

echo.
echo ========================================
echo   测试完成
echo ========================================
echo.
echo 提示: 如果测试通过，现在可以正常回测港股了！
echo       运行 python main.py 启动系统
echo.
pause
