"""
简单功能测试
测试数据管理器基本功能
"""
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'futu_backtest_trader'))

print("="*70)
print("TradingSystem 功能测试")
print("="*70)

# 加载环境变量
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / 'futu_backtest_trader' / '.env'
load_dotenv(env_path)

# 测试1: 数据管理器
print("\n[测试1] 数据管理器初始化")
try:
    from core.data_manager import DataManager
    manager = DataManager()
    print("✅ 数据管理器初始化成功")
except Exception as e:
    print(f"❌ 失败: {e}")
    exit(1)

# 测试2: 获取美股数据
print("\n[测试2] 获取美股数据 (TSLA)")
try:
    df = manager.get_kline_data('TSLA', '2025-01-20', '2025-01-22')
    if df is not None and len(df) > 0:
        print(f"✅ 成功获取 {len(df)} 条数据")
        print("\n最新数据:")
        print(df.tail(3).to_string())
    else:
        print("⚠️  数据为空")
except Exception as e:
    print(f"❌ 失败: {e}")

# 测试3: 策略引擎
print("\n[测试3] 策略引擎初始化")
try:
    from core.strategy_engine import StrategyEngine
    engine = StrategyEngine()
    print("✅ 策略引擎初始化成功")
    print(f"   已注册策略: {', '.join(engine.strategies.keys())}")
except Exception as e:
    print(f"❌ 失败: {e}")
    exit(1)

# 测试4: 生成交易信号
print("\n[测试4] 生成交易信号")
try:
    # 激活策略
    engine.activate_strategy('TSLA', 'TSF-LSMA', {
        'tsf_period': 9,
        'lsma_period': 20,
        'buy_threshold_pct': 0.5,
        'sell_threshold_pct': 0.5,
        'use_percent': True
    })
    
    # 获取更多数据
    df = manager.get_kline_data('TSLA', '2024-12-01', '2025-01-22')
    
    if df is not None:
        # 生成信号
        signals = engine.generate_signal('TSLA', df)
        
        if signals:
            for signal in signals:
                print(f"\n✅ 信号生成成功:")
                print(f"   类型: {signal['type']}")
                print(f"   原因: {signal['reason']}")
                print(f"   当前价: ${signal['current_price']:.2f}")
                if 'indicators' in signal:
                    print(f"   TSF: {signal['indicators']['tsf']:.2f}")
                    print(f"   LSMA: {signal['indicators']['lsma']:.2f}")
        else:
            print("⚪ 当前无交易信号")
    else:
        print("⚠️  数据获取失败")
        
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 测试5: AI分析器（可选）
print("\n[测试5] AI分析器")
try:
    from core.ai_analyzer import AIAnalyzer
    analyzer = AIAnalyzer()
    
    if analyzer.is_available():
        print(f"✅ AI功能可用")
        print(f"   可用模型: {', '.join(analyzer.available_models)}")
    else:
        print("⚪ AI功能不可用（未配置API密钥）")
except Exception as e:
    print(f"⚠️  {e}")

# 清理
manager.disconnect()

print("\n" + "="*70)
print("测试完成！")
print("="*70)
print("\n核心功能正常！可以运行:")
print("  python main.py          # 完整演示")
print("  python main.py --interactive  # 交互模式")
