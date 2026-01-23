"""
定时任务调度器
支持每日自动信号生成和交易
"""
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'futu_backtest_trader'))


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, data_manager, strategy_engine, trade_engine=None):
        """
        初始化调度器
        
        Parameters:
        -----------
        data_manager : DataManager
            数据管理器
        strategy_engine : StrategyEngine
            策略引擎
        trade_engine : TradeEngine, optional
            交易引擎
        """
        self.data_manager = data_manager
        self.strategy_engine = strategy_engine
        self.trade_engine = trade_engine
        
        # 任务列表
        self.tasks = {}
        
        # 运行标志
        self.running = False
        self.thread = None
        
        # 回调函数
        self.on_signal_callback = None
        self.on_trade_callback = None
        self.on_error_callback = None
        
        print("✅ 任务调度器已初始化")
    
    def add_daily_signal_task(
        self, 
        stock_code: str, 
        time_str: str, 
        strategy_name: str, 
        params: Dict,
        task_name: Optional[str] = None
    ):
        """
        添加每日信号生成任务
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        time_str : str
            执行时间，如 "16:10"（港股收盘）或 "04:10"（美股收盘）
        strategy_name : str
            策略名称
        params : dict
            策略参数
        task_name : str, optional
            任务名称（如果不提供，自动生成）
        """
        if task_name is None:
            task_name = f"signal_{stock_code}_{time_str.replace(':', '')}"
        
        def job():
            print(f"\n{'='*70}")
            print(f"📅 执行每日信号任务: {stock_code}")
            print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}\n")
            
            try:
                # 激活策略
                self.strategy_engine.activate_strategy(stock_code, strategy_name, params)
                
                # 获取数据（最近60天）
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
                
                df = self.data_manager.get_kline_data(
                    stock_code, start_date, end_date
                )
                
                if df is None:
                    print(f"❌ 获取数据失败")
                    if self.on_error_callback:
                        self.on_error_callback(task_name, "获取数据失败")
                    return
                
                # 生成信号
                signals = self.strategy_engine.generate_signal(stock_code, df)
                
                if signals:
                    for signal in signals:
                        print(f"\n🔔 {signal['type']} 信号")
                        print(f"   原因: {signal['reason']}")
                        print(f"   当前价: ${signal['current_price']:.2f}")
                        print(f"   建议价: ${signal['suggest_price_min']:.2f} - ${signal['suggest_price_max']:.2f}")
                        
                        # 回调
                        if self.on_signal_callback:
                            self.on_signal_callback(signal)
                else:
                    print(f"⚪ 无信号")
                
            except Exception as e:
                print(f"❌ 任务执行失败: {e}")
                if self.on_error_callback:
                    self.on_error_callback(task_name, str(e))
        
        # 添加定时任务
        schedule.every().day.at(time_str).do(job)
        
        # 保存任务信息
        self.tasks[task_name] = {
            'type': 'signal',
            'stock_code': stock_code,
            'time': time_str,
            'strategy': strategy_name,
            'params': params,
            'enabled': True
        }
        
        print(f"✅ 已添加每日信号任务: {task_name}")
        print(f"   股票: {stock_code}")
        print(f"   时间: {time_str}")
        print(f"   策略: {strategy_name}")
    
    def add_auto_trade_task(
        self, 
        stock_code: str, 
        time_str: str,
        task_name: Optional[str] = None,
        enable: bool = False
    ):
        """
        添加自动交易任务
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        time_str : str
            执行时间，如 "09:25"（开盘前）
        task_name : str, optional
            任务名称
        enable : bool
            是否启用（默认False，需要手动启用）
        """
        if task_name is None:
            task_name = f"trade_{stock_code}_{time_str.replace(':', '')}"
        
        def job():
            if not self.tasks[task_name]['enabled']:
                return
            
            print(f"\n{'='*70}")
            print(f"💰 执行自动交易任务: {stock_code}")
            print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}\n")
            
            try:
                # TODO: 实现自动交易逻辑
                # 1. 从数据库获取昨日信号
                # 2. 检查交易条件
                # 3. 执行交易
                # 4. 记录日志
                
                if self.trade_engine is None:
                    print(f"⚠️  交易引擎未初始化")
                    return
                
                print(f"⚠️  自动交易功能待实现")
                
            except Exception as e:
                print(f"❌ 任务执行失败: {e}")
                if self.on_error_callback:
                    self.on_error_callback(task_name, str(e))
        
        # 添加定时任务
        schedule.every().day.at(time_str).do(job)
        
        # 保存任务信息
        self.tasks[task_name] = {
            'type': 'trade',
            'stock_code': stock_code,
            'time': time_str,
            'enabled': enable
        }
        
        status = "已启用" if enable else "已禁用"
        print(f"✅ 已添加自动交易任务: {task_name} ({status})")
        print(f"   股票: {stock_code}")
        print(f"   时间: {time_str}")
    
    def add_custom_task(
        self, 
        task_name: str,
        time_str: str,
        callback: Callable,
        description: str = ""
    ):
        """
        添加自定义任务
        
        Parameters:
        -----------
        task_name : str
            任务名称
        time_str : str
            执行时间
        callback : callable
            回调函数
        description : str
            任务描述
        """
        # 添加定时任务
        schedule.every().day.at(time_str).do(callback)
        
        # 保存任务信息
        self.tasks[task_name] = {
            'type': 'custom',
            'time': time_str,
            'description': description,
            'enabled': True
        }
        
        print(f"✅ 已添加自定义任务: {task_name}")
        print(f"   时间: {time_str}")
        print(f"   描述: {description}")
    
    def remove_task(self, task_name: str):
        """
        移除任务
        
        Parameters:
        -----------
        task_name : str
            任务名称
        """
        if task_name in self.tasks:
            del self.tasks[task_name]
            print(f"✅ 已移除任务: {task_name}")
        else:
            print(f"⚠️  任务不存在: {task_name}")
    
    def enable_task(self, task_name: str):
        """启用任务"""
        if task_name in self.tasks:
            self.tasks[task_name]['enabled'] = True
            print(f"✅ 已启用任务: {task_name}")
        else:
            print(f"⚠️  任务不存在: {task_name}")
    
    def disable_task(self, task_name: str):
        """禁用任务"""
        if task_name in self.tasks:
            self.tasks[task_name]['enabled'] = False
            print(f"✅ 已禁用任务: {task_name}")
        else:
            print(f"⚠️  任务不存在: {task_name}")
    
    def start(self):
        """启动调度器"""
        if self.running:
            print("⚠️  调度器已在运行")
            return
        
        self.running = True
        
        def run_schedule():
            print(f"\n🚀 调度器已启动")
            print(f"   当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   已注册任务: {len(self.tasks)}")
            
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        
        self.thread = threading.Thread(target=run_schedule, daemon=True)
        self.thread.start()
        
        print("✅ 调度器线程已启动")
    
    def stop(self):
        """停止调度器"""
        if not self.running:
            print("⚠️  调度器未运行")
            return
        
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        print("✅ 调度器已停止")
    
    def list_tasks(self) -> Dict:
        """
        列出所有任务
        
        Returns:
        --------
        dict : 任务字典
        """
        return self.tasks.copy()
    
    def run_task_now(self, task_name: str):
        """
        立即执行任务
        
        Parameters:
        -----------
        task_name : str
            任务名称
        """
        if task_name not in self.tasks:
            print(f"⚠️  任务不存在: {task_name}")
            return
        
        task = self.tasks[task_name]
        
        if task['type'] == 'signal':
            # 执行信号任务
            stock_code = task['stock_code']
            strategy_name = task['strategy']
            params = task['params']
            
            print(f"\n🎯 手动执行信号任务: {task_name}")
            
            try:
                # 激活策略
                self.strategy_engine.activate_strategy(stock_code, strategy_name, params)
                
                # 获取数据
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
                
                df = self.data_manager.get_kline_data(
                    stock_code, start_date, end_date
                )
                
                if df is None:
                    print(f"❌ 获取数据失败")
                    return
                
                # 生成信号
                signals = self.strategy_engine.generate_signal(stock_code, df)
                
                if signals:
                    for signal in signals:
                        print(f"\n🔔 {signal['type']} 信号")
                        print(f"   原因: {signal['reason']}")
                        print(f"   当前价: ${signal['current_price']:.2f}")
                        
                        if self.on_signal_callback:
                            self.on_signal_callback(signal)
                else:
                    print(f"⚪ 无信号")
                
            except Exception as e:
                print(f"❌ 执行失败: {e}")
        
        else:
            print(f"⚠️  暂不支持手动执行此类型任务")
    
    def set_signal_callback(self, callback: Callable):
        """设置信号回调函数"""
        self.on_signal_callback = callback
    
    def set_trade_callback(self, callback: Callable):
        """设置交易回调函数"""
        self.on_trade_callback = callback
    
    def set_error_callback(self, callback: Callable):
        """设置错误回调函数"""
        self.on_error_callback = callback


# 使用示例
if __name__ == '__main__':
    from core.data_manager import DataManager
    from core.strategy_engine import StrategyEngine
    
    # 初始化
    data_manager = DataManager()
    strategy_engine = StrategyEngine()
    scheduler = TaskScheduler(data_manager, strategy_engine)
    
    # 设置回调
    def on_signal(signal):
        print(f"\n📬 收到信号回调:")
        print(f"   {signal['stock']} - {signal['type']}")
    
    scheduler.set_signal_callback(on_signal)
    
    # 添加任务
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
    
    # 立即测试
    print("\n=== 测试任务 ===")
    scheduler.run_task_now('signal_TSLA_0410')
    
    # 启动调度器（如果需要后台运行）
    # scheduler.start()
    # time.sleep(10)
    # scheduler.stop()
    
    data_manager.disconnect()
