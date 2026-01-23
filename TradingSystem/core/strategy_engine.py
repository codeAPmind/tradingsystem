"""
策略引擎
管理多个策略，生成交易信号
"""
import sys
from pathlib import Path
from typing import Optional, Dict, List
import pandas as pd
from datetime import datetime

# 导入策略类
from strategies.tsf_lsma_strategy import TSFLSMAStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.rsi_strategy import RSIStrategy


class StrategyEngine:
    """策略引擎"""
    
    def __init__(self):
        """初始化策略引擎"""
        # 已注册的策略类
        self.strategy_classes = {}
        
        # 当前激活的策略实例
        self.active_strategies = {}
        
        # 注册默认策略
        self._register_default_strategies()
        
        print("✅ 策略引擎已初始化")
        print(f"   已注册策略: {', '.join(self.strategy_classes.keys())}")
    
    def _register_default_strategies(self):
        """注册默认策略"""
        # TSF-LSMA策略
        self.strategy_classes['TSF-LSMA'] = TSFLSMAStrategy
        
        # MACD策略
        self.strategy_classes['MACD'] = MACDStrategy
        
        # RSI策略
        self.strategy_classes['RSI'] = RSIStrategy
    
    def register_strategy(self, name: str, strategy_class):
        """
        注册新策略
        
        Parameters:
        -----------
        name : str
            策略名称
        strategy_class : BaseStrategy
            策略类
        """
        self.strategy_classes[name] = strategy_class
        print(f"✅ 已注册策略: {name}")
    
    def activate_strategy(self, stock_code: str, strategy_name: str, params: Optional[Dict] = None):
        """
        激活策略
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        strategy_name : str
            策略名称
        params : dict, optional
            策略参数（如果不提供，使用默认参数）
        """
        if strategy_name not in self.strategy_classes:
            raise ValueError(f"策略 {strategy_name} 未注册")
        
        # 获取策略类
        strategy_class = self.strategy_classes[strategy_name]
        
        # 使用提供的参数或默认参数
        if params is None:
            params = strategy_class.get_default_params()
        
        # 创建策略实例
        strategy_instance = strategy_class(**params)
        
        # 保存到激活列表
        key = f"{stock_code}_{strategy_name}"
        self.active_strategies[key] = {
            'stock_code': stock_code,
            'strategy_name': strategy_name,
            'strategy': strategy_instance,
            'params': params
        }
        
        print(f"✅ 已激活策略: {stock_code} - {strategy_name}")
        print(f"   参数: {params}")
    
    def generate_signal(self, stock_code: str, df: pd.DataFrame) -> List[Dict]:
        """
        生成交易信号
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        df : DataFrame
            K线数据，必须包含: open, high, low, close, volume
        
        Returns:
        --------
        list : 信号列表
            [{
                'stock': 'TSLA',
                'type': 'BUY',  # BUY/SELL/HOLD
                'reason': 'TSF > LSMA + 0.5%',
                'current_price': 420.0,
                'suggest_price_min': 415.0,
                'suggest_price_max': 425.0,
                'time': '2025-01-22 16:00:00',
                'strategy': 'TSF-LSMA',
                'params': {...}
            }, ...]
        """
        signals = []
        
        # 遍历所有激活的策略
        for key, info in self.active_strategies.items():
            if info['stock_code'] == stock_code:
                strategy_instance = info['strategy']
                
                # 调用策略的analyze方法
                signal = strategy_instance.analyze(df)
                
                if signal:
                    signal['stock'] = stock_code
                    signal['strategy'] = info['strategy_name']
                    signal['params'] = info['params']
                    signal['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    signals.append(signal)
        
        return signals
    
    
    def get_strategy_params(self, strategy_name: str) -> Dict:
        """
        获取策略默认参数
        
        Parameters:
        -----------
        strategy_name : str
            策略名称
        
        Returns:
        --------
        dict : 默认参数
        """
        if strategy_name not in self.strategy_classes:
            return {}
        
        strategy_class = self.strategy_classes[strategy_name]
        return strategy_class.get_default_params()
    
    def list_strategies(self) -> List[Dict]:
        """
        列出所有已注册的策略
        
        Returns:
        --------
        list : 策略列表
        """
        strategies = []
        for name, strategy_class in self.strategy_classes.items():
            strategies.append({
                'name': name,
                'description': strategy_class.__doc__ or '',
                'params': strategy_class.get_default_params()
            })
        return strategies
    
    def deactivate_strategy(self, stock_code: str, strategy_name: str):
        """
        停用策略
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        strategy_name : str
            策略名称
        """
        key = f"{stock_code}_{strategy_name}"
        if key in self.active_strategies:
            del self.active_strategies[key]
            print(f"✅ 已停用策略: {stock_code} - {strategy_name}")


# 使用示例
if __name__ == '__main__':
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    
    from core.data_manager import DataManager
    
    # 初始化
    data_manager = DataManager()
    strategy_engine = StrategyEngine()
    
    # 测试TSLA
    print("\n=== 测试TSLA ===")
    
    # 激活策略
    strategy_engine.activate_strategy('TSLA', 'TSF-LSMA', {
        'tsf_period': 9,
        'lsma_period': 20,
        'buy_threshold_pct': 0.5,
        'sell_threshold_pct': 0.5,
        'use_percent': True
    })
    
    # 获取数据
    df = data_manager.get_kline_data('TSLA', '2024-12-01', '2025-01-22')
    
    if df is not None:
        # 生成信号
        signals = strategy_engine.generate_signal('TSLA', df)
        
        for signal in signals:
            print(f"\n信号类型: {signal['type']}")
            print(f"原因: {signal['reason']}")
            print(f"当前价: ${signal['current_price']:.2f}")
            print(f"建议价: ${signal['suggest_price_min']:.2f} - ${signal['suggest_price_max']:.2f}")
    
    data_manager.disconnect()
