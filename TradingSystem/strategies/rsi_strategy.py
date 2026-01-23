"""
RSI策略
Relative Strength Index
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict
from .base_strategy import BaseStrategy


class RSIStrategy(BaseStrategy):
    """RSI策略"""
    
    @classmethod
    def get_default_params(cls) -> Dict:
        """获取默认参数"""
        return {
            'period': 14,
            'overbought': 70,
            'oversold': 30
        }
    
    def _rsi(self, data: pd.Series, period: int) -> pd.Series:
        """计算RSI指标"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def analyze(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        分析数据并生成信号
        
        Parameters:
        -----------
        df : DataFrame
            K线数据
        
        Returns:
        --------
        dict : 信号字典或None
        """
        # 获取参数
        period = self.params.get('period', 14)
        overbought = self.params.get('overbought', 70)
        oversold = self.params.get('oversold', 30)
        
        # 数据检查
        if len(df) < period + 1:
            return None
        
        # 计算RSI
        rsi = self._rsi(df['close'], period)
        rsi_value = rsi.iloc[-1]
        current_price = float(df['close'].iloc[-1])
        
        if np.isnan(rsi_value):
            return None
        
        # 判断信号
        signal_type = 'HOLD'
        reason = ''
        
        # RSI超卖，买入信号
        if rsi_value < oversold:
            signal_type = 'BUY'
            reason = f"RSI({rsi_value:.2f}) < {oversold} (超卖)"
        # RSI超买，卖出信号
        elif rsi_value > overbought:
            signal_type = 'SELL'
            reason = f"RSI({rsi_value:.2f}) > {overbought} (超买)"
        else:
            reason = f"RSI({rsi_value:.2f}) 在正常范围 ({oversold}-{overbought})"
        
        # 建议价格范围
        suggest_price_min = current_price * 0.98
        suggest_price_max = current_price * 1.02
        
        return {
            'type': signal_type,
            'reason': reason,
            'current_price': current_price,
            'suggest_price_min': suggest_price_min,
            'suggest_price_max': suggest_price_max,
            'indicators': {
                'rsi': float(rsi_value)
            }
        }
