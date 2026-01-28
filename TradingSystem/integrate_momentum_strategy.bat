@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   动量情绪策略集成工具
echo ========================================
echo.
echo 功能: 自动将动量情绪策略集成到系统
echo.
echo 将要执行的修改:
echo 1. 添加策略导入和选择
echo 2. 添加SPY基准数据获取
echo 3. 修改回测逻辑支持多策略
echo 4. 添加策略切换界面
echo.
echo 注意: 会自动备份原文件
echo.
pause

python integrate_momentum_strategy.py

echo.
echo ========================================
echo   集成完成
echo ========================================
echo.
pause
