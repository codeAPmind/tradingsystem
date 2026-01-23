"""
TSF-LSMA策略
Time Series Forecast - Least Squares Moving Average
"""
import numpy as np
import pandas as pd
from typing import Optional, Dict
from .base_strategy import BaseStrategy


class TSFLSMAStrategy(BaseStrategy):
    """TSF-LSMA策略"""
    
    @classmethod
    def get_default_params(cls) -> Dict:
        """获取默认参数"""
        return {
            'tsf_period': 9,
            'lsma_period': 20,
            'buy_threshold_pct': 0.5,
            'sell_threshold_pct': 0.5,
            'use_percent': True
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
        tsf_period = self.params.get('tsf_period', 9)
        lsma_period = self.params.get('lsma_period', 20)
        buy_threshold_pct = self.params.get('buy_threshold_pct', 0.5)
        sell_threshold_pct = self.params.get('sell_threshold_pct', 0.5)
        use_percent = self.params.get('use_percent', True)
        
        # 数据检查
        if len(df) < max(tsf_period, lsma_period):
            return None
        
        # 计算TSF
        tsf_values = []
        for i in range(len(df)):
            if i < tsf_period - 1:
                tsf_values.append(np.nan)
            else:
                data = df['close'].iloc[i-tsf_period+1:i+1].values
                x = np.arange(len(data))
                coeffs = np.polyfit(x, data, 1)
                # TSF = a + b * (N)
                tsf = coeffs[0] * tsf_period + coeffs[1]
                tsf_values.append(tsf)
        
        # 计算LSMA
        lsma_values = []
        for i in range(len(df)):
            if i < lsma_period - 1:
                lsma_values.append(np.nan)
            else:
                data = df['close'].iloc[i-lsma_period+1:i+1].values
                x = np.arange(len(data))
                coeffs = np.polyfit(x, data, 1)
                # LSMA = a + b * (N-1)
                lsma = coeffs[0] * (lsma_period - 1) + coeffs[1]
                lsma_values.append(lsma)
        
        # 获取最新值
        tsf = tsf_values[-1]
        lsma = lsma_values[-1]
        current_price = float(df['close'].iloc[-1])
        
        if np.isnan(tsf) or np.isnan(lsma):
            return None
        
        # 计算差值
        diff = tsf - lsma
        
        # 判断信号
        signal_type = 'HOLD'
        reason = ''
        
        if use_percent:
            # 使用百分比阈值
            buy_threshold = lsma * (buy_threshold_pct / 100)
            sell_threshold = lsma * (sell_threshold_pct / 100)
            
            if diff > buy_threshold:
                signal_type = 'BUY'
                reason = f"TSF ({tsf:.2f}) > LSMA ({lsma:.2f}) + {buy_threshold_pct}% ({buy_threshold:.2f})"
            elif diff < -sell_threshold:
                signal_type = 'SELL'
                reason = f"TSF ({tsf:.2f}) < LSMA ({lsma:.2f}) - {sell_threshold_pct}% ({sell_threshold:.2f})"
            else:
                reason = f"差值 {diff:.2f} 在阈值范围内"
        else:
            # 使用绝对值阈值
            buy_threshold = self.params.get('buy_threshold', 0.5)
            sell_threshold = self.params.get('sell_threshold', 0.5)
            
            if diff > buy_threshold:
                signal_type = 'BUY'
                reason = f"TSF ({tsf:.2f}) > LSMA ({lsma:.2f}) + {buy_threshold:.2f}"
            elif diff < -sell_threshold:
                signal_type = 'SELL'
                reason = f"TSF ({tsf:.2f}) < LSMA ({lsma:.2f}) - {sell_threshold:.2f}"
            else:
                reason = f"差值 {diff:.2f} 在阈值范围内"
        
        # 建议价格范围（当前价±2%）
        suggest_price_min = current_price * 0.98
        suggest_price_max = current_price * 1.02
        
        return {
            'type': signal_type,
            'reason': reason,
            'current_price': current_price,
            'suggest_price_min': suggest_price_min,
            'suggest_price_max': suggest_price_max,
            'indicators': {
                'tsf': float(tsf),
                'lsma': float(lsma),
                'diff': float(diff)
            }
        }
