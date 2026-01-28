#!/usr/bin/env python3
"""
自动集成动量情绪策略到系统
Auto-integrate Momentum Sentiment Strategy
"""
import os
import re

def integrate_strategy():
    """集成策略到回测界面"""
    
    file_path = 'ui/widgets/backtest_widget.py'
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    print("📝 读取回测界面文件...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经集成
    if '动量情绪' in content or 'MomentumSentimentStrategy' in content:
        print("✅ 策略已经集成，无需重复集成")
        return True
    
    # 备份原文件
    backup_path = file_path + '.backup_momentum'
    print(f"💾 备份原文件到: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # === 修改1: 在BacktestThread.run()中添加策略支持 ===
    
    # 查找导入策略的位置
    old_import = """            from core.backtest_engine import BacktestEngine
            from strategies.backtrader_tsf_lsma import TSFLSMAStrategy"""
    
    new_import = """            from core.backtest_engine import BacktestEngine
            from strategies.backtrader_tsf_lsma import TSFLSMAStrategy
            from strategies.momentum_sentiment_strategy import MomentumSentimentStrategy"""
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        print("✅ 步骤1: 添加策略导入")
    else:
        print("⚠️  步骤1: 未找到导入位置，跳过")
    
    # 查找添加数据的位置，在其后添加SPY数据获取
    old_add_data = """            # 添加数据
            engine.add_data_from_dataframe(df, stock_code)"""
    
    new_add_data = """            # 添加主标的数据
            engine.add_data_from_dataframe(df, stock_code)
            
            # 如果是动量情绪策略且是美股，添加SPY数据
            if self.params.get('strategy') == '动量情绪':
                # 判断市场
                market = 'HK' if stock_code.startswith('HK.') else 'US'
                
                if market == 'US':
                    try:
                        self.progress.emit("正在获取SPY基准数据...")
                        spy_df = self.data_manager.get_kline_data('SPY', start_date, end_date)
                        if spy_df is not None and len(spy_df) > 0:
                            engine.add_data_from_dataframe(spy_df, 'SPY')
                            self.progress.emit(f"已添加SPY基准数据 ({len(spy_df)}条)")
                        else:
                            self.progress.emit("⚠️  SPY数据获取失败，相对强度过滤将禁用")
                    except Exception as e:
                        self.progress.emit(f"⚠️  SPY数据获取失败: {e}")"""
    
    if old_add_data in content:
        content = content.replace(old_add_data, new_add_data)
        print("✅ 步骤2: 添加SPY数据获取逻辑")
    else:
        print("⚠️  步骤2: 未找到数据添加位置，跳过")
    
    # 查找添加策略的位置，修改为支持多策略
    old_add_strategy = """            # 添加策略
            engine.add_strategy(TSFLSMAStrategy, **strategy_params)"""
    
    new_add_strategy = """            # 根据选择的策略类型添加
            strategy_name = self.params.get('strategy', 'TSF-LSMA')
            
            if strategy_name == '动量情绪':
                # 动量情绪策略参数
                momentum_params = {
                    'rsi_period': self.params.get('rsi_period', 14),
                    'rsi_threshold': self.params.get('rsi_threshold', 45),
                    'use_relative_strength': self.params.get('use_relative_strength', True),
                    'use_kelly': self.params.get('use_kelly', True),
                    'kelly_fraction': self.params.get('kelly_fraction', 0.25),
                    'use_sentiment': self.params.get('use_sentiment', False),
                    'printlog': False
                }
                engine.add_strategy(MomentumSentimentStrategy, **momentum_params)
            else:
                # TSF-LSMA策略（默认）
                engine.add_strategy(TSFLSMAStrategy, **strategy_params)"""
    
    if old_add_strategy in content:
        content = content.replace(old_add_strategy, new_add_strategy)
        print("✅ 步骤3: 修改策略添加逻辑")
    else:
        print("⚠️  步骤3: 未找到策略添加位置，跳过")
    
    # === 修改2: 在create_parameter_panel中添加策略选择下拉框 ===
    
    # 查找基本参数组中市场选择的位置
    market_combo_code = """        # 市场选择（新增）
        self.market_combo = QComboBox()
        self.market_combo.addItems(['美股', '港股'])
        self.market_combo.currentTextChanged.connect(self.on_market_changed)
        basic_layout.addRow("市场:", self.market_combo)"""
    
    strategy_combo_code = """        # 市场选择
        self.market_combo = QComboBox()
        self.market_combo.addItems(['美股', '港股'])
        self.market_combo.currentTextChanged.connect(self.on_market_changed)
        basic_layout.addRow("市场:", self.market_combo)
        
        # 策略选择（新增）
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(['TSF-LSMA', '动量情绪'])
        self.strategy_combo.currentTextChanged.connect(self.on_strategy_changed)
        basic_layout.addRow("策略:", self.strategy_combo)"""
    
    if market_combo_code in content:
        content = content.replace(market_combo_code, strategy_combo_code)
        print("✅ 步骤4: 添加策略选择下拉框")
    else:
        print("⚠️  步骤4: 未找到市场选择位置，跳过")
    
    # === 修改3: 在start_backtest中添加策略参数 ===
    
    # 查找params收集位置
    old_params_collect = """        # 收集参数
        params = {
            'stock_code': stock_code,"""
    
    new_params_collect = """        # 收集参数
        params = {
            'strategy': self.strategy_combo.currentText(),  # 新增：策略类型
            'stock_code': stock_code,"""
    
    if old_params_collect in content:
        content = content.replace(old_params_collect, new_params_collect)
        print("✅ 步骤5: 添加策略类型参数")
    else:
        print("⚠️  步骤5: 未找到参数收集位置，跳过")
    
    # === 修改4: 添加策略切换回调函数 ===
    
    # 在文件末尾（stop_backtest方法后）添加新方法
    # 查找on_market_changed方法
    if 'def on_market_changed(self, market):' in content:
        # 在on_market_changed方法后添加on_strategy_changed
        on_market_method_end = content.find('def on_market_changed(self, market):')
        next_def = content.find('\n    def ', on_market_method_end + 1)
        
        new_method = """
    def on_strategy_changed(self, strategy):
        \"\"\"策略改变时的回调\"\"\"
        if strategy == '动量情绪':
            # 提示用户该策略的特点
            self.status_label.setText(
                "动量情绪策略: 结合RSI+MACD+ADX，支持相对强度过滤和凯利仓位"
            )
        elif strategy == 'TSF-LSMA':
            self.status_label.setText(
                "TSF-LSMA策略: 时间序列预测和最小二乘移动平均"
            )
    """
        
        if next_def > 0:
            content = content[:next_def] + new_method + content[next_def:]
            print("✅ 步骤6: 添加策略切换回调")
        else:
            print("⚠️  步骤6: 无法找到插入位置")
    
    # 写入修改后的文件
    print("✍️  写入修改后的文件...")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 集成完成！")
    return True


if __name__ == '__main__':
    print("\n" + "="*70)
    print("动量情绪策略集成工具".center(70))
    print("="*70 + "\n")
    
    print("功能: 自动将动量情绪策略集成到回测界面\n")
    print("修改内容:")
    print("  1. 添加策略导入")
    print("  2. 添加SPY数据获取逻辑")
    print("  3. 修改策略选择机制")
    print("  4. 添加策略选择下拉框")
    print("  5. 添加策略参数传递")
    print("  6. 添加策略切换回调")
    print("\n按Enter继续...")
    input()
    
    success = integrate_strategy()
    
    if success:
        print("\n" + "="*70)
        print("集成成功！".center(70))
        print("="*70)
        print("""
✅ 动量情绪策略已成功集成到系统

现在可以:
1. 重启程序: python main.py
2. 打开"回测"标签
3. 在"策略"下拉框中选择"动量情绪"
4. 设置参数并开始回测

策略特点:
✅ 技术指标三重确认 (RSI + MACD + ADX)
✅ 相对强度过滤 (自动获取SPY数据)
✅ 凯利公式动态仓位
✅ ATR动态跟踪止损

注意事项:
- 美股回测会自动获取SPY基准数据
- 港股回测不使用相对强度过滤
- 建议使用至少1年的历史数据
- 情绪分析功能默认关闭（需要API密钥）

原文件已备份到: ui/widgets/backtest_widget.py.backup_momentum
如有问题可以用备份文件恢复
""")
    else:
        print("\n" + "="*70)
        print("集成失败".center(70))
        print("="*70)
        print("""
❌ 集成未成功

可能原因:
1. 文件路径不正确
2. 文件已被修改，代码结构不匹配
3. 权限不足

建议:
1. 检查是否在正确的目录
2. 查看备份文件
3. 手动进行集成（参考文档）
""")
    
    print("\n")
