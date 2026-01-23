@echo off
REM TradingSystem 安装脚本
REM 用于Windows系统快速安装依赖

echo =====================================================
echo TradingSystem 依赖安装程序
echo =====================================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] 正在检查Python版本...
python --version
echo.

REM 升级pip
echo [2/5] 正在升级pip...
python -m pip install --upgrade pip
echo.

REM 安装核心依赖
echo [3/5] 正在安装核心依赖...
pip install pandas numpy requests python-dotenv schedule
if %errorlevel% neq 0 (
    echo [错误] 核心依赖安装失败
    pause
    exit /b 1
)
echo.

REM 询问是否安装A股支持
echo [4/5] 是否安装A股数据支持（Tushare）？
choice /C YN /M "输入 Y 安装，N 跳过"
if %errorlevel%==1 (
    echo 正在安装Tushare...
    pip install tushare
)
echo.

REM 询问是否安装AI支持
echo [5/5] 是否安装AI分析支持？
echo   推荐安装DeepSeek（便宜、好用）
choice /C YN /M "输入 Y 安装，N 跳过"
if %errorlevel%==1 (
    echo 正在安装OpenAI SDK（支持DeepSeek和ChatGPT）...
    pip install openai
    echo.
    echo 如需其他AI模型，请手动安装：
    echo   - Claude:    pip install anthropic
    echo   - 通义千问: pip install dashscope
)
echo.

echo =====================================================
echo 安装完成！
echo =====================================================
echo.
echo 下一步：
echo   1. 配置 .env 文件（参考父目录的.env）
echo   2. 运行测试: python test_core.py
echo   3. 运行演示: python main.py
echo.
echo 详细说明请查看 QUICKSTART.md
echo.
pause
