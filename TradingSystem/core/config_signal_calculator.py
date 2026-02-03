"""
配置驱动的信号计算引擎
Config-driven Signal Calculator

根据JSON配置文件自动计算交易信号
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

from core.strategy_config_loader import StrategyConfig, config_loader
from core.data_manager import DataManager
from core.strategy_engine import StrategyEngine


class ConfigSignalCalculator:
    """配置驱动的信号计算器"""
    
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
        
        print("✅ 配置信号计算器已初始化")
    
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
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        print(f"   数据: {start_date} ~ {end_date}")
        
        df = self.data_manager.get_kline_data(stock_code, start_date, end_date)
        
        if df is None or len(df) < 30:
            print(f"   ❌ 数据不足 ({len(df) if df is not None else 0} 条)")
            return None
        
        print(f"   ✅ 数据: {len(df)} 条")
        
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
        
        print(f"   🎯 {signal['type']} - {stock_code}")
        print(f"   原因: {signal['reason']}")
        print(f"   价格: ${signal['current_price']:.2f}")
        
        # 添加配置信息
        signal['config_name'] = config.name
        signal['config_file'] = config.config_file
        signal['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return signal
    
    def calculate_all(self, days: int = 60) -> List[Dict]:
        """
        计算所有启用配置的信号
        
        Parameters:
        -----------
        days : int
            数据天数
        
        Returns:
        --------
        list : 信号列表
        """
        print("\n" + "="*70)
        print("批量计算交易信号".center(70))
        print("="*70)
        
        enabled = config_loader.get_enabled()
        
        if not enabled:
            print("\n⚠️  无启用的配置\n")
            return []
        
        print(f"\n发现 {len(enabled)} 个启用的配置\n")
        
        signals = []
        
        for config in enabled:
            try:
                signal = self.calculate_signal(config, days)
                if signal:
                    signals.append(signal)
            except Exception as e:
                print(f"   ❌ 计算失败: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n" + "="*70)
        print(f"完成: 生成 {len(signals)} 个信号".center(70))
        print("="*70 + "\n")
        
        return signals
    
    def calculate_by_id(self, config_id: str, days: int = 60) -> Optional[Dict]:
        """
        根据配置ID计算信号
        
        Parameters:
        -----------
        config_id : str
            配置ID（文件名不含扩展名）
        days : int
            数据天数
        
        Returns:
        --------
        dict or None : 信号信息
        """
        config = config_loader.get(config_id)
        
        if config is None:
            print(f"❌ 配置不存在: {config_id}")
            return None
        
        if not config.enabled:
            print(f"⚠️  配置已禁用: {config_id}")
            return None
        
        return self.calculate_signal(config, days)
    
    def calculate_by_stock(self, stock_code: str, days: int = 60) -> List[Dict]:
        """
        计算指定股票的所有信号
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        days : int
            数据天数
        
        Returns:
        --------
        list : 信号列表
        """
        configs = config_loader.get_by_stock(stock_code)
        
        if not configs:
            print(f"⚠️  无 {stock_code} 的配置")
            return []
        
        signals = []
        
        for config in configs:
            if config.enabled:
                signal = self.calculate_signal(config, days)
                if signal:
                    signals.append(signal)
        
        return signals
    
    def format_report(self, signals: List[Dict]) -> str:
        """
        格式化信号报告
        
        Parameters:
        -----------
        signals : list
            信号列表
        
        Returns:
        --------
        str : 格式化报告
        """
        if not signals:
            return "📋 交易信号报告\n\n⚪ 无交易信号"
        
        report = []
        report.append("📋 交易信号报告")
        report.append("=" * 70)
        report.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"信号: {len(signals)} 个")
        report.append("")
        
        # 分组
        buy = [s for s in signals if s['type'] == 'BUY']
        sell = [s for s in signals if s['type'] == 'SELL']
        hold = [s for s in signals if s['type'] == 'HOLD']
        
        if buy:
            report.append("🟢 买入信号:")
            report.append("-" * 70)
            for s in buy:
                report.append(f"  股票: {s['stock']}")
                report.append(f"  策略: {s['strategy']}")
                report.append(f"  当前价: ${s['current_price']:.2f}")
                report.append(f"  建议价: ${s['suggest_price_min']:.2f} - ${s['suggest_price_max']:.2f}")
                report.append(f"  原因: {s['reason']}")
                report.append("")
        
        if sell:
            report.append("🔴 卖出信号:")
            report.append("-" * 70)
            for s in sell:
                report.append(f"  股票: {s['stock']}")
                report.append(f"  策略: {s['strategy']}")
                report.append(f"  当前价: ${s['current_price']:.2f}")
                report.append(f"  建议价: ${s['suggest_price_min']:.2f} - ${s['suggest_price_max']:.2f}")
                report.append(f"  原因: {s['reason']}")
                report.append("")
        
        if hold:
            report.append("⚪ 持有信号:")
            report.append("-" * 70)
            for s in hold:
                report.append(f"  股票: {s['stock']}")
                report.append(f"  策略: {s['strategy']}")
                report.append("")
        
        report.append("=" * 70)
        
        return "\n".join(report)


# 全局计算器实例
signal_calculator = ConfigSignalCalculator()


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*70)
    print("配置信号计算器测试")
    print("="*70)
    
    # 初始化
    calc = ConfigSignalCalculator()
    
    # 测试1: 计算单个信号
    print("\n【测试1】计算TSLA信号")
    signal = calc.calculate_by_id('TSLA_strategy')
    
    if signal:
        print(f"\n✅ 信号:")
        print(f"   类型: {signal['type']}")
        print(f"   价格: ${signal['current_price']:.2f}")
        print(f"   原因: {signal['reason']}")
    
    # 测试2: 批量计算
    print("\n【测试2】批量计算所有信号")
    signals = calc.calculate_all()
    
    # 测试3: 生成报告
    print("\n【测试3】生成报告")
    report = calc.format_report(signals)
    print(report)
    
    print("\n✅ 测试完成\n")
