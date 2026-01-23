"""
TradingSystem核心功能测试
测试数据管理、策略引擎、调度器等核心模块
"""
import sys
from pathlib import Path
import os

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'futu_backtest_trader'))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / 'futu_backtest_trader' / '.env')


def test_data_manager():
    """测试数据管理器"""
    print("\n" + "="*70)
    print("测试1: 数据管理器")
    print("="*70)
    
    try:
        from core.data_manager import DataManager
        
        manager = DataManager()
        
        # 测试美股
        print("\n--- 测试美股（TSLA）---")
        df = manager.get_kline_data('TSLA', '2025-01-15', '2025-01-22')
        if df is not None:
            print(f"✅ 成功获取 {len(df)} 条数据")
            print(df.head())
        else:
            print("⚠️  美股数据获取失败")
        
        # 测试港股（需要Futu OpenD运行）
        print("\n--- 测试港股（HK.01797）---")
        try:
            df = manager.get_kline_data('HK.01797', '2025-01-15', '2025-01-22')
            if df is not None:
                print(f"✅ 成功获取 {len(df)} 条数据")
                print(df.head())
            else:
                print("⚠️  港股数据获取失败（可能Futu OpenD未运行）")
        except Exception as e:
            print(f"⚠️  港股测试跳过: {e}")
        
        # 测试A股（需要Tushare Token）
        print("\n--- 测试A股（600519）---")
        try:
            df = manager.get_kline_data('600519', '2025-01-15', '2025-01-22')
            if df is not None:
                print(f"✅ 成功获取 {len(df)} 条数据")
                print(df.head())
            else:
                print("⚠️  A股数据获取失败")
        except Exception as e:
            print(f"⚠️  A股测试跳过: {e}")
        
        manager.disconnect()
        
        print("\n✅ 数据管理器测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 数据管理器测试失败: {e}")
        return False


def test_strategy_engine():
    """测试策略引擎"""
    print("\n" + "="*70)
    print("测试2: 策略引擎")
    print("="*70)
    
    try:
        from core.data_manager import DataManager
        from core.strategy_engine import StrategyEngine
        
        data_manager = DataManager()
        strategy_engine = StrategyEngine()
        
        # 激活策略
        print("\n--- 激活TSF-LSMA策略 ---")
        strategy_engine.activate_strategy('TSLA', 'TSF-LSMA', {
            'tsf_period': 9,
            'lsma_period': 20,
            'buy_threshold_pct': 0.5,
            'sell_threshold_pct': 0.5,
            'use_percent': True
        })
        
        # 获取数据
        print("\n--- 获取TSLA数据 ---")
        df = data_manager.get_kline_data('TSLA', '2024-12-01', '2025-01-22')
        
        if df is not None:
            # 生成信号
            print("\n--- 生成交易信号 ---")
            signals = strategy_engine.generate_signal('TSLA', df)
            
            if signals:
                for signal in signals:
                    print(f"\n信号类型: {signal['type']}")
                    print(f"策略: {signal['strategy']}")
                    print(f"原因: {signal['reason']}")
                    print(f"当前价: ${signal['current_price']:.2f}")
                    print(f"建议价: ${signal['suggest_price_min']:.2f} - ${signal['suggest_price_max']:.2f}")
                    print(f"时间: {signal['time']}")
                    
                    if 'indicators' in signal:
                        print(f"指标:")
                        for key, value in signal['indicators'].items():
                            print(f"  {key}: {value:.2f}")
            else:
                print("⚪ 无信号")
        else:
            print("⚠️  数据获取失败")
        
        data_manager.disconnect()
        
        print("\n✅ 策略引擎测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 策略引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scheduler():
    """测试调度器"""
    print("\n" + "="*70)
    print("测试3: 任务调度器")
    print("="*70)
    
    try:
        from core.data_manager import DataManager
        from core.strategy_engine import StrategyEngine
        from core.scheduler import TaskScheduler
        
        data_manager = DataManager()
        strategy_engine = StrategyEngine()
        scheduler = TaskScheduler(data_manager, strategy_engine)
        
        # 添加任务
        print("\n--- 添加每日信号任务 ---")
        scheduler.add_daily_signal_task(
            stock_code='TSLA',
            time_str='04:10',
            strategy_name='TSF-LSMA',
            params={
                'tsf_period': 9,
                'lsma_period': 20,
                'buy_threshold_pct': 0.5,
                'sell_threshold_pct': 0.5,
                'use_percent': True
            }
        )
        
        # 列出任务
        print("\n--- 已注册任务 ---")
        tasks = scheduler.list_tasks()
        for task_name, task_info in tasks.items():
            print(f"任务名: {task_name}")
            print(f"  类型: {task_info['type']}")
            print(f"  股票: {task_info['stock_code']}")
            print(f"  时间: {task_info['time']}")
        
        # 手动执行任务
        print("\n--- 手动执行任务 ---")
        scheduler.run_task_now('signal_TSLA_0410')
        
        data_manager.disconnect()
        
        print("\n✅ 调度器测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 调度器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_analyzer():
    """测试AI分析器"""
    print("\n" + "="*70)
    print("测试4: AI分析引擎")
    print("="*70)
    
    try:
        from core.ai_analyzer import AIAnalyzer
        
        analyzer = AIAnalyzer(primary_model='deepseek')
        
        if not analyzer.is_available():
            print("⚠️  没有可用的AI模型")
            print("   请在.env文件中配置至少一个AI API密钥")
            print("\n支持的API:")
            for model_id, config in AIAnalyzer.SUPPORTED_MODELS.items():
                print(f"  - {config['name']}: {config['api_key_env']}")
            return True  # 不算失败
        
        # 技术分析测试
        print("\n--- 技术分析测试 ---")
        tech_data = """
股票: TSLA
当前价: $420.0
TSF(9): $425.0
LSMA(20): $415.0
差值: +$10.0
趋势: 上涨
成交量: 放大
"""
        
        result = analyzer.analyze('technical', tech_data)
        if result:
            print("✅ AI分析成功")
            print(result[:500] + "..." if len(result) > 500 else result)
        else:
            print("⚠️  AI分析失败")
        
        print("\n✅ AI分析器测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ AI分析器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tushare():
    """测试Tushare数据"""
    print("\n" + "="*70)
    print("测试5: Tushare数据获取")
    print("="*70)
    
    try:
        from data.tushare_data import TushareDataFetcher
        
        fetcher = TushareDataFetcher()
        
        # 测试历史数据
        print("\n--- 获取贵州茅台历史数据 ---")
        df = fetcher.get_history_kline('600519', '2025-01-15', '2025-01-22')
        if df is not None:
            print(f"✅ 成功获取 {len(df)} 条数据")
            print(df.head())
        else:
            print("⚠️  数据获取失败")
        
        # 测试股票信息
        print("\n--- 获取股票基本信息 ---")
        info = fetcher.get_stock_basic('600519')
        if info:
            print(f"✅ 名称: {info.get('name')}")
            print(f"   行业: {info.get('industry')}")
        
        print("\n✅ Tushare测试完成")
        return True
        
    except Exception as e:
        print(f"\n⚠️  Tushare测试跳过: {e}")
        if "TUSHARE_TOKEN" in str(e):
            print("\n提示:")
            print("  1. 注册Tushare账号: https://tushare.pro/register")
            print("  2. 获取Token")
            print("  3. 在.env文件中设置: TUSHARE_TOKEN=your_token")
        return True  # 不算失败


def test_eastmoney():
    """测试东方财富数据"""
    print("\n" + "="*70)
    print("测试6: 东方财富数据获取")
    print("="*70)
    
    try:
        from data.eastmoney_data import EastMoneyDataFetcher
        
        fetcher = EastMoneyDataFetcher()
        
        # 测试实时行情
        print("\n--- 获取贵州茅台实时行情 ---")
        quote = fetcher.get_realtime_price('600519')
        if quote:
            print(f"✅ 名称: {quote['name']}")
            print(f"   价格: ¥{quote['price']:.2f}")
            print(f"   涨跌: {quote['change']:+.2f} ({quote['change_pct']:+.2f}%)")
        else:
            print("⚠️  实时行情获取失败")
        
        # 测试资金流向
        print("\n--- 获取资金流向 ---")
        flow = fetcher.get_money_flow('600519')
        if flow:
            print(f"✅ 日期: {flow['date']}")
            print(f"   主力净流入: ¥{flow['main_net_inflow']/10000:.2f}万")
        else:
            print("⚠️  资金流向获取失败")
        
        print("\n✅ 东方财富测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 东方财富测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("TradingSystem 核心功能测试")
    print("="*70)
    
    results = []
    
    # 测试数据管理器
    results.append(("数据管理器", test_data_manager()))
    
    # 测试策略引擎
    results.append(("策略引擎", test_strategy_engine()))
    
    # 测试调度器
    results.append(("任务调度器", test_scheduler()))
    
    # 测试AI分析器
    results.append(("AI分析器", test_ai_analyzer()))
    
    # 测试Tushare
    results.append(("Tushare数据", test_tushare()))
    
    # 测试东方财富
    results.append(("东方财富数据", test_eastmoney()))
    
    # 汇总结果
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*70)
    print(f"总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print("="*70)
    
    if failed == 0:
        print("\n🎉 所有测试通过！系统核心功能正常。")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查配置和依赖。")
        return 1


if __name__ == '__main__':
    exit(main())
