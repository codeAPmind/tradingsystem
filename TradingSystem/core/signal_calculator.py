"""
基于配置的信号计算器
Config-based Signal Calculator

根据策略配置文件自动计算买卖信号
"""
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from core.strategy_config import StrategyConfig, config_manager
from core.data_manager import DataManager
from core.strategy_engine import StrategyEngine


class SignalCalculator:
    """信号计算器"""
    
    def __init__(self, data_manager: DataManager = None, strategy_engine: StrategyEngine = None):
        """
        初始化信号计算器
        
        Parameters:
        -----------
        data_manager : DataManager, optional
            数据管理器
        strategy_engine : StrategyEngine, optional
            策略引擎
        """
        self.data_manager = data_manager or DataManager()
        self.strategy_engine = strategy_engine or StrategyEngine()
        
        print("✅ 信号计算器已初始化")
    
    def calculate_signal(self, config: StrategyConfig, days: int = 60) -> Optional[Dict]:
        """
        根据配置计算信号
        
        Parameters:
        -----------
        config : StrategyConfig
            策略配置
        days : int
            数据天数
        
        Returns:
        --------
        dict or None : 信号信息
        """
        stock_code = config.stock_code
        strategy_name = config.strategy
        parameters = config.parameters
        
        print(f"\n📊 计算信号: {config.name}")
        print(f"   股票: {stock_code}")
        print(f"   策略: {strategy_name}")
        
        # 获取数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - pd.Timedelta(days=days)).strftime('%Y-%m-%d')
        
        print(f"   获取数据: {start_date} ~ {end_date}")
        
        df = self.data_manager.get_kline_data(stock_code, start_date, end_date)
        
        if df is None or len(df) < 30:
            print(f"   ❌ 数据不足")
            return None
        
        print(f"   ✅ 获取 {len(df)} 条数据")
        
        # 激活策略
        self.strategy_engine.activate_strategy(
            stock_code,
            strategy_name,
            parameters
        )
        
        # 生成信号
        signals = self.strategy_engine.generate_signal(stock_code, df)
        
        if not signals:
            print(f"   ⚪ 无信号")
            return None
        
        # 获取最新信号
        signal = signals[0]
        
        print(f"   🎯 信号: {signal['type']}")
        print(f"   原因: {signal['reason']}")
        print(f"   当前价: ${signal['current_price']:.2f}")
        
        # 添加配置信息
        signal['config_name'] = config.name
        signal['config_id'] = config.config_file
        signal['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return signal
    
    def calculate_all_signals(self) -> List[Dict]:
        """
        计算所有启用配置的信号
        
        Returns:
        --------
        list : 信号列表
        """
        print("\n" + "="*70)
        print("批量计算信号".center(70))
        print("="*70)
        
        enabled_configs = config_manager.get_enabled_configs()
        
        if not enabled_configs:
            print("\n⚠️  无启用的配置")
            return []
        
        print(f"\n发现 {len(enabled_configs)} 个启用的配置\n")
        
        signals = []
        
        for config in enabled_configs:
            try:
                signal = self.calculate_signal(config)
                if signal:
                    signals.append(signal)
            except Exception as e:
                print(f"   ❌ 计算失败: {e}")
        
        print(f"\n" + "="*70)
        print(f"完成: 生成 {len(signals)} 个信号")
        print("="*70 + "\n")
        
        return signals
    
    def calculate_signal_by_id(self, config_id: str, days: int = 60) -> Optional[Dict]:
        """
        根据配置ID计算信号
        
        Parameters:
        -----------
        config_id : str
            配置ID
        days : int
            数据天数
        
        Returns:
        --------
        dict or None : 信号信息
        """
        config = config_manager.get_config(config_id)
        
        if config is None:
            print(f"❌ 配置不存在: {config_id}")
            return None
        
        if not config.enabled:
            print(f"⚠️  配置已禁用: {config_id}")
            return None
        
        return self.calculate_signal(config, days)
    
    def format_signal_report(self, signals: List[Dict]) -> str:
        """
        格式化信号报告
        
        Parameters:
        -----------
        signals : list
            信号列表
        
        Returns:
        --------
        str : 格式化的报告
        """
        if not signals:
            return "📋 交易信号报告\n\n⚪ 无交易信号"
        
        report = []
        report.append("📋 交易信号报告")
        report.append("=" * 70)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"信号数量: {len(signals)}")
        report.append("")
        
        # 按信号类型分组
        buy_signals = [s for s in signals if s['type'] == 'BUY']
        sell_signals = [s for s in signals if s['type'] == 'SELL']
        hold_signals = [s for s in signals if s['type'] == 'HOLD']
        
        if buy_signals:
            report.append("🟢 买入信号:")
            report.append("-" * 70)
            for signal in buy_signals:
                report.append(f"  股票: {signal['stock']}")
                report.append(f"  策略: {signal['strategy']}")
                report.append(f"  当前价: ${signal['current_price']:.2f}")
                report.append(f"  建议价: ${signal['suggest_price_min']:.2f} - ${signal['suggest_price_max']:.2f}")
                report.append(f"  原因: {signal['reason']}")
                report.append("")
        
        if sell_signals:
            report.append("🔴 卖出信号:")
            report.append("-" * 70)
            for signal in sell_signals:
                report.append(f"  股票: {signal['stock']}")
                report.append(f"  策略: {signal['strategy']}")
                report.append(f"  当前价: ${signal['current_price']:.2f}")
                report.append(f"  建议价: ${signal['suggest_price_min']:.2f} - ${signal['suggest_price_max']:.2f}")
                report.append(f"  原因: {signal['reason']}")
                report.append("")
        
        if hold_signals:
            report.append("⚪ 持有信号:")
            report.append("-" * 70)
            for signal in hold_signals:
                report.append(f"  股票: {signal['stock']}")
                report.append(f"  策略: {signal['strategy']}")
                report.append("")
        
        report.append("=" * 70)
        
        return "\n".join(report)


# 全局信号计算器实例
signal_calculator = SignalCalculator()


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*70)
    print("信号计算器测试")
    print("="*70)
    
    # 初始化
    calculator = SignalCalculator()
    
    # 测试1: 计算单个信号
    print("\n【测试1】计算TSLA信号")
    print("="*70)
    
    signal = calculator.calculate_signal_by_id('strategy_TSLA')
    
    if signal:
        print(f"\n✅ 信号生成成功:")
        print(f"   类型: {signal['type']}")
        print(f"   股票: {signal['stock']}")
        print(f"   策略: {signal['strategy']}")
        print(f"   当前价: ${signal['current_price']:.2f}")
        print(f"   原因: {signal['reason']}")
    
    # 测试2: 批量计算信号
    print("\n【测试2】批量计算所有启用配置的信号")
    print("="*70)
    
    signals = calculator.calculate_all_signals()
    
    # 测试3: 生成报告
    print("\n【测试3】生成信号报告")
    print("="*70)
    
    report = calculator.format_signal_report(signals)
    print(report)
    
    print("\n✅ 测试完成\n")
