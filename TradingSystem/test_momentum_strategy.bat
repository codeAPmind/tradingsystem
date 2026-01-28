@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   动量情绪策略完整测试
echo ========================================
echo.
echo 测试内容:
echo 1. 模块导入检查
echo 2. 数据获取测试
echo 3. TSLA单独回测
echo 4. TSLA vs SPY回测（相对强度）
echo 5. 参数敏感性分析
echo.
echo 注意:
echo - 需要网络连接（获取数据）
echo - 需要Futu OpenD运行（港股）
echo - 需要API密钥（美股）
echo.
pause

python test_momentum_strategy.py

echo.
echo ========================================
echo   测试完成
echo ========================================
echo.
pause
