@echo off
REM 一键安装所有推荐依赖

echo =====================================================
echo TradingSystem - 一键安装
echo =====================================================
echo.

python install_all.py

if %errorlevel%==0 (
    echo.
    echo =====================================================
    echo 安装成功！
    echo =====================================================
    echo.
    echo 下一步：
    echo   1. 配置 .env 文件
    echo   2. 运行检查: python check_system.py
    echo   3. 运行测试: python test_core.py
) else (
    echo.
    echo 安装失败，请检查错误信息
)

echo.
pause
