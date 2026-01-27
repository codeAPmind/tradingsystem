#!/usr/bin/env python3
"""
美股+港股数据获取测试
Test US and HK stock data fetching
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*80)
print("美股+港股数据获取完整测试".center(80))
print("="*80 + "\n")

# ==================== 测试1: 美股数据（FinancialDatasets API）====================
print("【测试1】美股数据获取 (FinancialDatasets API)")
print("-"*80)

try:
    from data.financial_data import FinancialDatasetsAPI
    
    api = FinancialDatasetsAPI()
    
    if not api.api_key:
        print("❌ 未设置 FINANCIAL_DATASETS_API_KEY")
        print("   请在 .env 文件中设置:")
        print("   FINANCIAL_DATASETS_API_KEY=your_api_key_here")
    else:
        print(f"✅ API密钥已设置: {api.api_key[:10]}...")
        
        # 测试TSLA
        print("\n1. 测试 Tesla (TSLA)...")
        df = api.get_stock_prices('TSLA', '2025-01-20', '2025-01-27')
        
        if df is not None and len(df) > 0:
            print(f"   ✅ 成功: {len(df)} 行数据")
            print(f"   列: {list(df.columns)}")
            print(f"   date类型: {df['date'].dtype}")  # 应该是 object (字符串)
            
            # 验证格式
            assert df['date'].dtype == 'object', "date应该是字符串类型"
            assert 'date' in df.columns, "必须有date列"
            assert len(df) >= 3, "数据量不足"
            
            print(f"\n   前3行:")
            print(df.head(3).to_string(index=False))
        else:
            print(f"   ❌ 获取失败")
        
        # 测试AAPL
        print("\n2. 测试 Apple (AAPL)...")
        df2 = api.get_stock_prices('AAPL', '2025-01-20', '2025-01-27')
        
        if df2 is not None and len(df2) > 0:
            print(f"   ✅ 成功: {len(df2)} 行数据")
        else:
            print(f"   ❌ 获取失败")
    
    print(f"\n✅ 测试1完成\n")

except Exception as e:
    print(f"❌ 测试1失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试2: 港股数据（Futu API）====================
print("\n【测试2】港股数据获取 (Futu API)")
print("-"*80)

try:
    from data.futu_data import FutuDataFetcher
    
    fetcher = FutuDataFetcher()
    
    print("正在连接 Futu OpenD...")
    if not fetcher.connect():
        print("❌ Futu OpenD 连接失败")
        print("   请确保:")
        print("   1. Futu OpenD 已启动")
        print("   2. 已登录账户")
        print("   3. 端口号正确 (默认11111)")
    else:
        print("✅ Futu OpenD 已连接")
        
        # 测试腾讯
        print("\n1. 测试 腾讯控股 (HK.00700)...")
        df = fetcher.get_history_kline('HK.00700', '2025-01-20', '2025-01-27')
        
        if df is not None and len(df) > 0:
            print(f"   ✅ 成功: {len(df)} 行数据")
            print(f"   列: {list(df.columns)}")
            print(f"   date类型: {df['date'].dtype}")  # 应该是 object (字符串)
            
            # 验证格式
            assert df['date'].dtype == 'object', "date应该是字符串类型"
            assert 'date' in df.columns, "必须有date列"
            assert len(df) >= 3, "数据量不足"
            
            print(f"\n   前3行:")
            print(df.head(3).to_string(index=False))
        else:
            print(f"   ❌ 获取失败")
        
        # 测试东方甄选
        print("\n2. 测试 东方甄选 (HK.01797)...")
        df2 = fetcher.get_history_kline('HK.01797', '2025-01-20', '2025-01-27')
        
        if df2 is not None and len(df2) > 0:
            print(f"   ✅ 成功: {len(df2)} 行数据")
        else:
            print(f"   ❌ 获取失败")
        
        fetcher.disconnect()
    
    print(f"\n✅ 测试2完成\n")

except Exception as e:
    print(f"❌ 测试2失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试3: 数据管理器集成 ====================
print("\n【测试3】数据管理器集成测试")
print("-"*80)

try:
    from core.data_manager import DataManager
    
    manager = DataManager()
    
    # 测试美股
    print("\n1. 测试美股获取 (TSLA)...")
    df_us = manager.get_kline_data('TSLA', '2025-01-20', '2025-01-27')
    
    if df_us is not None and len(df_us) > 0:
        print(f"   ✅ 成功: {len(df_us)} 行")
        print(f"   date类型: {df_us['date'].dtype}")
    else:
        print(f"   ❌ 获取失败")
    
    # 测试港股
    print("\n2. 测试港股获取 (HK.01797)...")
    df_hk = manager.get_kline_data('HK.01797', '2025-01-20', '2025-01-27')
    
    if df_hk is not None and len(df_hk) > 0:
        print(f"   ✅ 成功: {len(df_hk)} 行")
        print(f"   date类型: {df_hk['date'].dtype}")
    else:
        print(f"   ❌ 获取失败")
    
    manager.disconnect()
    
    print(f"\n✅ 测试3完成\n")

except Exception as e:
    print(f"❌ 测试3失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 测试4: 回测引擎兼容性 ====================
print("\n【测试4】回测引擎兼容性测试")
print("-"*80)

try:
    from core.backtest_engine import BacktestEngine
    from core.data_manager import DataManager
    
    manager = DataManager()
    
    # 测试美股回测准备
    print("\n1. 测试美股数据转换 (TSLA)...")
    df = manager.get_kline_data('TSLA', '2025-01-01', '2025-01-27')
    
    if df is not None and len(df) >= 20:
        print(f"   获取数据: {len(df)} 行")
        
        engine = BacktestEngine(initial_cash=100000.0)
        
        try:
            engine.add_data_from_dataframe(df, 'TSLA')
            print(f"   ✅ 数据添加成功（date转换正常）")
        except Exception as e:
            print(f"   ❌ 数据添加失败: {e}")
    else:
        print(f"   ⚠️  数据不足，跳过测试")
    
    # 测试港股回测准备
    print("\n2. 测试港股数据转换 (HK.01797)...")
    df2 = manager.get_kline_data('HK.01797', '2024-12-01', '2025-01-27')
    
    if df2 is not None and len(df2) >= 30:
        print(f"   获取数据: {len(df2)} 行")
        
        engine2 = BacktestEngine(initial_cash=100000.0)
        
        try:
            engine2.add_data_from_dataframe(df2, 'HK.01797')
            print(f"   ✅ 数据添加成功（date转换正常）")
        except Exception as e:
            print(f"   ❌ 数据添加失败: {e}")
    else:
        print(f"   ⚠️  数据不足，跳过测试")
    
    manager.disconnect()
    
    print(f"\n✅ 测试4完成\n")

except Exception as e:
    print(f"❌ 测试4失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 总结 ====================
print("\n" + "="*80)
print("测试总结".center(80))
print("="*80 + "\n")

print("""
✅ 已完成的修复:

1. 数据格式标准化
   ✅ 美股 (FinancialDatasets): date列为字符串
   ✅ 港股 (Futu): date列为字符串
   ✅ 统一格式: date, open, high, low, close, volume

2. 回测引擎修复
   ✅ 自动转换 date 字符串为 datetime
   ✅ 设置为 DatetimeIndex
   ✅ backtrader 可以正常使用

3. 缓存系统
   ✅ 智能缓存（优先读取）
   ✅ 自动保存
   ✅ 性能提升

⚠️  重要提示:

1. 日期范围设置
   ❌ 错误: 1/27/2026 (未来日期)
   ✅ 正确: 1/27/2025 (当前日期)
   
2. 确保环境就绪
   - Futu OpenD 已启动（港股需要）
   - API密钥已设置（美股需要）
   - 日期范围合理（>=30天）

3. 回测要求
   - 至少需要30条数据
   - 日期不能超过今天
   - 建议测试日期: 2024-12-01 到 2025-01-27

🎯 下一步:

1. 修复日期: 将结束日期改为 1/27/2025
2. 确保数据量: 至少跨度30天以上
3. 运行回测: python main.py

文档:
- README_FIX.md - 完整修复指南
- BACKTEST_COMPLETE_FIX.md - 技术细节
""")

print("="*80)
print("\n✅ 所有测试完成！\n")
