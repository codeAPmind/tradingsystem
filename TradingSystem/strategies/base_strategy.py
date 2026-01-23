"""
策略基类
所有策略都应该继承这个基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
import pandas as pd


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, **params):
        """
        初始化策略
        
        Parameters:
        -----------
        **params : dict
            策略参数
        """
        self.params = params
    
    @abstractmethod
    def analyze(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        分析数据并生成信号
        
        Parameters:
        -----------
        df : DataFrame
            K线数据，必须包含: open, high, low, close, volume
        
        Returns:
        --------
        dict : 信号字典或None
            {
                'type': 'BUY' | 'SELL' | 'HOLD',
                'reason': str,
                'current_price': float,
                'suggest_price_min': float,
                'suggest_price_max': float,
                'indicators': dict
            }
        """
        pass
    
    @classmethod
    def get_default_params(cls) -> Dict:
        """
        获取默认参数
        
        Returns:
        --------
        dict : 默认参数
        """
        return {}
    
    def get_params(self) -> Dict:
        """获取当前参数"""
        return self.params.copy()
