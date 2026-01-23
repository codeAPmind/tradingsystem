@echo off
REM TradingSystem 测试脚本
REM 快速测试系统核心功能

echo =====================================================
echo TradingSystem 核心功能测试
echo =====================================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python
    pause
    exit /b 1
)

REM 运行测试
echo 正在运行测试...
echo.
python test_core.py

echo.
echo =====================================================
echo 测试完成
echo =====================================================
echo.

REM 检查测试结果
if %errorlevel%==0 (
    echo [成功] 所有测试通过！
    echo.
    echo 下一步：
    echo   - 运行演示: python main.py
    echo   - 交互模式: python main.py --interactive
    echo   - 查看文档: README.md
) else (
    echo [失败] 部分测试未通过
    echo.
    echo 请检查：
    echo   1. .env 文件是否正确配置
    echo   2. API密钥是否有效
    echo   3. 依赖是否完整安装
    echo.
    echo 详细说明: QUICKSTART.md
)

echo.
pause
