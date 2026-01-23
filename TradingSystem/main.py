"""
TradingSystem 主程序
量化交易系统入口
"""
import sys
from pathlib import Path
import os
import io

# 设置UTF-8编码（Windows控制台支持）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加路径（确保当前项目优先）
_current_dir = Path(__file__).parent
sys.path.insert(0, str(_current_dir))
# 添加参考项目路径（用于导入策略等）
sys.path.append(str(_current_dir.parent / 'futu_backtest_trader'))

# 加载环境变量
from dotenv import load_dotenv
# 优先加载当前目录的.env文件
env_path = Path(__file__).parent / '.env'
if not env_path.exists():
    # 如果当前目录没有，尝试加载父目录的.env
    env_path = Path(__file__).parent.parent / 'futu_backtest_trader' / '.env'
load_dotenv(env_path)

from core.data_manager import DataManager
from core.strategy_engine import StrategyEngine
from core.scheduler import TaskScheduler
from core.ai_analyzer import AIAnalyzer
from core.trade_engine import TradeEngine


class TradingSystem:
    """交易系统主类"""
    
    def __init__(self):
        """初始化系统"""
        print("\n" + "="*70)
        print("🚀 TradingSystem 量化交易系统")
        print("="*70)
        
        # 初始化核心模块
        print("\n正在初始化核心模块...")
        
        self.data_manager = DataManager()
        self.strategy_engine = StrategyEngine()
        self.scheduler = TaskScheduler(self.data_manager, self.strategy_engine)
        self.ai_analyzer = AIAnalyzer(primary_model='deepseek')
        
        # 设置回调
        self.scheduler.set_signal_callback(self.on_signal_generated)
        
        print("\n✅ 系统初始化完成")
    
    def on_signal_generated(self, signal):
        """信号生成回调"""
        print(f"\n📬 收到新信号:")
        print(f"   股票: {signal['stock']}")
        print(f"   类型: {signal['type']}")
        print(f"   原因: {signal['reason']}")
        print(f"   当前价: ${signal['current_price']:.2f}")
        
        # 如果有AI，可以进行信号确认
        if self.ai_analyzer.is_available() and signal['type'] != 'HOLD':
            print(f"\n🤖 AI分析中...")
            ai_result = self.ai_analyzer.analyze('signal_confirm', f"""
股票: {signal['stock']}
信号: {signal['type']}
原因: {signal['reason']}
当前价: ${signal['current_price']:.2f}
""")
            if ai_result:
                print(f"AI建议: {ai_result[:200]}...")
    
    def demo_data_fetching(self):
        """演示数据获取"""
        print("\n" + "="*70)
        print("演示1: 数据获取")
        print("="*70)
        
        # 美股
        print("\n--- 美股（TSLA）---")
        df = self.data_manager.get_kline_data('TSLA', '2025-01-15', '2025-01-22')
        if df is not None:
            print(f"✅ 获取到 {len(df)} 条数据")
            print(df.tail(3))
        
        # A股
        print("\n--- A股（贵州茅台 600519）---")
        try:
            df = self.data_manager.get_kline_data('600519', '2025-01-15', '2025-01-22')
            if df is not None:
                print(f"✅ 获取到 {len(df)} 条数据")
                print(df.tail(3))
        except Exception as e:
            print(f"⚠️  A股数据获取失败: {e}")
            print("   提示: 需要配置TUSHARE_TOKEN")
    
    def demo_strategy_analysis(self):
        """演示策略分析"""
        print("\n" + "="*70)
        print("演示2: 策略分析")
        print("="*70)
        
        # 激活策略
        print("\n激活TSF-LSMA策略...")
        self.strategy_engine.activate_strategy('TSLA', 'TSF-LSMA', {
            'tsf_period': 9,
            'lsma_period': 20,
            'buy_threshold_pct': 0.5,
            'sell_threshold_pct': 0.5,
            'use_percent': True
        })
        
        # 获取数据
        print("获取TSLA数据...")
        df = self.data_manager.get_kline_data('TSLA', '2024-12-01', '2025-01-22')
        
        if df is not None:
            # 生成信号
            print("生成交易信号...")
            signals = self.strategy_engine.generate_signal('TSLA', df)
            
            if signals:
                for signal in signals:
                    print(f"\n📊 信号详情:")
                    print(f"   类型: {signal['type']}")
                    print(f"   策略: {signal['strategy']}")
                    print(f"   原因: {signal['reason']}")
                    print(f"   当前价: ${signal['current_price']:.2f}")
                    print(f"   建议价: ${signal['suggest_price_min']:.2f} - ${signal['suggest_price_max']:.2f}")
                    
                    if 'indicators' in signal:
                        print(f"   指标:")
                        for key, value in signal['indicators'].items():
                            print(f"     {key}: {value:.2f}")
            else:
                print("\n⚪ 当前无交易信号")
    
    def demo_scheduler(self):
        """演示任务调度"""
        print("\n" + "="*70)
        print("演示3: 任务调度")
        print("="*70)
        
        # 添加任务
        print("\n添加每日信号任务...")
        self.scheduler.add_daily_signal_task(
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
        print("\n已注册任务:")
        tasks = self.scheduler.list_tasks()
        for task_name, task_info in tasks.items():
            print(f"  - {task_name}")
            print(f"    股票: {task_info['stock_code']}")
            print(f"    时间: {task_info['time']}")
            print(f"    策略: {task_info['strategy']}")
        
        # 手动执行任务（测试）
        print("\n手动执行任务（测试）...")
        self.scheduler.run_task_now('signal_TSLA_0410')
    
    def demo_ai_analysis(self):
        """演示AI分析"""
        print("\n" + "="*70)
        print("演示4: AI分析")
        print("="*70)
        
        if not self.ai_analyzer.is_available():
            print("\n⚠️  AI功能不可用")
            print("   请在.env文件中配置至少一个AI API密钥")
            print("\n支持的AI模型:")
            for model_id, config in AIAnalyzer.SUPPORTED_MODELS.items():
                print(f"  - {config['name']}: {config['api_key_env']}")
            return
        
        # 技术分析
        print("\n--- 技术分析 ---")
        result = self.ai_analyzer.analyze('technical', """
股票: TSLA
当前价: $420.0
TSF(9): $425.0
LSMA(20): $415.0
差值: +$10.0
趋势: 上涨
成交量: 放大
""")
        
        if result:
            print("✅ AI分析结果:")
            print(result[:500] + "..." if len(result) > 500 else result)
        else:
            print("❌ AI分析失败")
    
    def run_demo(self):
        """运行完整演示"""
        try:
            # 1. 数据获取
            self.demo_data_fetching()
            
            # 2. 策略分析
            self.demo_strategy_analysis()
            
            # 3. 任务调度
            self.demo_scheduler()
            
            # 4. AI分析
            self.demo_ai_analysis()
            
            print("\n" + "="*70)
            print("✅ 演示完成")
            print("="*70)
            
            print("\n提示:")
            print("  - 运行 'python test_core.py' 进行完整测试")
            print("  - 查看 README.md 了解更多使用方法")
            print("  - UI界面正在开发中...")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断")
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 清理
            self.data_manager.disconnect()
    
    def interactive_mode(self):
        """交互模式"""
        print("\n" + "="*70)
        print("交互模式")
        print("="*70)
        print("\n可用命令:")
        print("  1 - 获取股票数据")
        print("  2 - 生成交易信号")
        print("  3 - AI分析")
        print("  4 - 列出任务")
        print("  5 - 执行任务")
        print("  0 - 退出")
        
        while True:
            try:
                choice = input("\n请选择 (0-5): ").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    stock = input("股票代码 (如TSLA/600519): ").strip()
                    df = self.data_manager.get_kline_data(
                        stock, '2025-01-15', '2025-01-22'
                    )
                    if df is not None:
                        print(f"\n最新数据:")
                        print(df.tail())
                
                elif choice == '2':
                    stock = input("股票代码: ").strip()
                    self.strategy_engine.activate_strategy(stock, 'TSF-LSMA')
                    df = self.data_manager.get_kline_data(
                        stock, '2024-12-01', '2025-01-22'
                    )
                    if df is not None:
                        signals = self.strategy_engine.generate_signal(stock, df)
                        for signal in signals:
                            print(f"\n信号: {signal['type']}")
                            print(f"原因: {signal['reason']}")
                
                elif choice == '3':
                    if self.ai_analyzer.is_available():
                        content = input("分析内容: ").strip()
                        result = self.ai_analyzer.analyze('technical', content)
                        if result:
                            print(f"\nAI分析:\n{result}")
                    else:
                        print("AI功能不可用")
                
                elif choice == '4':
                    tasks = self.scheduler.list_tasks()
                    for name, info in tasks.items():
                        print(f"\n{name}: {info['stock_code']} @ {info['time']}")
                
                elif choice == '5':
                    task_name = input("任务名称: ").strip()
                    self.scheduler.run_task_now(task_name)
                
                else:
                    print("无效选择")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"错误: {e}")
        
        print("\n再见！")
        self.data_manager.disconnect()


def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--ui':
            # UI模式
            run_ui()
        elif sys.argv[1] == '--demo':
            # 运行演示
            system = TradingSystem()
            system.run_demo()
        elif sys.argv[1] == '--interactive':
            # 交互模式
            system = TradingSystem()
            system.interactive_mode()
        else:
            print(f"未知参数: {sys.argv[1]}")
            print("\n用法:")
            print("  python main.py          # UI模式（默认）")
            print("  python main.py --ui     # UI模式")
            print("  python main.py --demo   # 运行演示")
            print("  python main.py --interactive  # 交互模式")
    else:
        # 默认运行UI
        run_ui()


def run_ui():
    """运行UI模式"""
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("量化交易系统")
        app.setOrganizationName("TradingSystem")
        
        # 初始化核心模块
        print("\n" + "="*70)
        print("🚀 TradingSystem 量化交易系统 - UI模式")
        print("="*70)
        
        data_manager = DataManager()
        strategy_engine = StrategyEngine()
        trade_engine = TradeEngine()
        scheduler = TaskScheduler(data_manager, strategy_engine, trade_engine)
        ai_analyzer = AIAnalyzer(primary_model='deepseek')
        
        # 创建主窗口
        window = MainWindow(data_manager, strategy_engine, scheduler, ai_analyzer)
        window.show()
        
        # 运行应用
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        print("\n请安装UI依赖:")
        print("  pip install PyQt6")
        print("\n或使用命令行模式:")
        print("  python main.py --demo")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 启动UI失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
