"""
MACD策略
Moving Average Convergence Divergence
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict
from .base_strategy import BaseStrategy


class MACDStrategy(BaseStrategy):
    """MACD策略"""
    
    @classmethod
    def get_default_params(cls) -> Dict:
        """获取默认参数"""
        return {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'threshold': 0.0
        }
    
    def _ema(self, data: pd.Series, period: int) -> pd.Series:
        """计算EMA"""
        return data.ewm(span=period, adjust=False).mean()
    
    def _macd(self, data: pd.Series, fast: int, slow: int, signal: int) -> Dict:
        """计算MACD指标"""
        ema_fast = self._ema(data, fast)
        ema_slow = self._ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self._ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
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
        fast_period = self.params.get('fast_period', 12)
        slow_period = self.params.get('slow_period', 26)
        signal_period = self.params.get('signal_period', 9)
        threshold = self.params.get('threshold', 0.0)
        
        # 数据检查
        if len(df) < slow_period + signal_period:
            return None
        
        # 计算MACD
        macd_data = self._macd(df['close'], fast_period, slow_period, signal_period)
        
        # 获取最新值
        macd = macd_data['macd'].iloc[-1]
        signal = macd_data['signal'].iloc[-1]
        histogram = macd_data['histogram'].iloc[-1]
        prev_histogram = macd_data['histogram'].iloc[-2] if len(df) > 1 else 0
        
        current_price = float(df['close'].iloc[-1])
        
        if np.isnan(macd) or np.isnan(signal):
            return None
        
        # 判断信号
        signal_type = 'HOLD'
        reason = ''
        
        # MACD金叉：MACD线上穿信号线
        if macd > signal and prev_histogram <= 0 and histogram > threshold:
            signal_type = 'BUY'
            reason = f"MACD金叉: MACD({macd:.2f}) > Signal({signal:.2f})"
        # MACD死叉：MACD线下穿信号线
        elif macd < signal and prev_histogram >= 0 and histogram < -threshold:
            signal_type = 'SELL'
            reason = f"MACD死叉: MACD({macd:.2f}) < Signal({signal:.2f})"
        else:
            reason = f"MACD({macd:.2f}) 与 Signal({signal:.2f}) 未形成交叉"
        
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
                'macd': float(macd),
                'signal': float(signal),
                'histogram': float(histogram)
            }
        }
