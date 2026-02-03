"""
Bollinger Bands + RSI 策略
Bollinger RSI Strategy

适用于震荡行情，捕捉超买超卖反转机会

策略逻辑:
- 买入: 价格触及下轨 + RSI超卖
- 卖出: 价格触及上轨 + RSI超买
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict
from strategies.base_strategy import BaseStrategy


class BollingerRSIStrategy(BaseStrategy):
    """
    Bollinger Bands + RSI 策略
    
    适用场景:
    - 震荡行情（区间波动）
    - 科技股、叙事股
    - 无明确趋势的市场
    
    核心思想:
    - 布林带：判断价格位置（上轨/下轨）
    - RSI：确认超买/超卖状态
    - 双重确认：提高信号可靠性
    """
    
    @staticmethod
    def get_default_params():
        """获取默认参数"""
        return {
            'bb_period': 15,          # 布林带周期（阿里最优）
            'bb_devfactor': 2.0,      # 布林带标准差倍数
            'rsi_period': 10,         # RSI周期（阿里最优）
            'rsi_oversold': 35,       # RSI超卖线（阿里最优）
            'rsi_overbought': 75,     # RSI超买线（阿里最优）
            'bb_touch_pct': 0.01,     # 触及布林带的阈值（1%）
            'use_midband': False,     # 是否使用中轨策略
        }
    
    def __init__(self, **params):
        """
        初始化策略
        
        Parameters:
        -----------
        bb_period : int
            布林带周期（默认15）
        bb_devfactor : float
            布林带标准差倍数（默认2.0）
        rsi_period : int
            RSI周期（默认10）
        rsi_oversold : float
            RSI超卖线（默认35）
        rsi_overbought : float
            RSI超买线（默认75）
        bb_touch_pct : float
            触及布林带阈值（默认0.01 = 1%）
        use_midband : bool
            是否使用中轨突破策略（默认False）
        """
        # 合并默认参数和用户参数
        default_params = self.get_default_params()
        default_params.update(params)
        
        self.bb_period = default_params['bb_period']
        self.bb_devfactor = default_params['bb_devfactor']
        self.rsi_period = default_params['rsi_period']
        self.rsi_oversold = default_params['rsi_oversold']
        self.rsi_overbought = default_params['rsi_overbought']
        self.bb_touch_pct = default_params['bb_touch_pct']
        self.use_midband = default_params['use_midband']
    
    def calculate_bollinger_bands(self, df):
        """
        计算布林带
        
        Parameters:
        -----------
        df : DataFrame
            必须包含 'close' 列
        
        Returns:
        --------
        upper, middle, lower : Series
            上轨、中轨、下轨
        """
        close = df['close'].astype(float)
        
        # 计算中轨（移动平均）
        middle = close.rolling(window=self.bb_period).mean()
        
        # 计算标准差
        std = close.rolling(window=self.bb_period).std()
        
        # 计算上下轨
        upper = middle + (std * self.bb_devfactor)
        lower = middle - (std * self.bb_devfactor)
        
        return upper, middle, lower
    
    def calculate_rsi(self, df):
        """
        计算RSI
        
        Parameters:
        -----------
        df : DataFrame
            必须包含 'close' 列
        
        Returns:
        --------
        rsi : Series
            RSI指标值
        """
        close = df['close'].astype(float)
        
        # 计算价格变化
        delta = close.diff()
        
        # 分离涨跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均涨跌幅
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        
        # 避免除以0
        avg_loss = avg_loss.replace(0, 0.0001)
        
        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def analyze(self, df):
        """
        分析数据生成信号
        
        Parameters:
        -----------
        df : DataFrame
            K线数据，必须包含: date, open, high, low, close, volume
        
        Returns:
        --------
        dict : 信号信息
            {
                'type': 'BUY' | 'SELL' | 'HOLD',
                'reason': '信号原因',
                'current_price': 当前价格,
                'suggest_price_min': 建议买入最低价,
                'suggest_price_max': 建议买入最高价,
                'indicators': {指标值}
            }
        """
        # 检查数据量
        min_data = max(self.bb_period, self.rsi_period) + 5
        if len(df) < min_data:
            return None
        
        # 计算指标
        bb_upper, bb_mid, bb_lower = self.calculate_bollinger_bands(df)
        rsi = self.calculate_rsi(df)
        
        # 获取最新数据
        latest_idx = len(df) - 1
        current_price = float(df['close'].iloc[latest_idx])
        current_bb_upper = float(bb_upper.iloc[latest_idx])
        current_bb_mid = float(bb_mid.iloc[latest_idx])
        current_bb_lower = float(bb_lower.iloc[latest_idx])
        current_rsi = float(rsi.iloc[latest_idx])
        
        # 检查数据有效性
        if pd.isna(current_bb_upper) or pd.isna(current_rsi):
            return None
        
        # 计算距离布林带的百分比
        band_width = current_bb_upper - current_bb_lower
        
        if band_width > 0:
            dist_to_upper = (current_bb_upper - current_price) / band_width
            dist_to_lower = (current_price - current_bb_lower) / band_width
        else:
            dist_to_upper = 1.0
            dist_to_lower = 1.0
        
        # 生成信号
        signal_type = 'HOLD'
        reason = ''
        
        # 买入信号：价格触及下轨 + RSI超卖
        if dist_to_lower < self.bb_touch_pct:
            if current_rsi < self.rsi_oversold:
                signal_type = 'BUY'
                reason = (
                    f'价格触及下轨 (距离{dist_to_lower*100:.1f}%) + '
                    f'RSI超卖 ({current_rsi:.1f} < {self.rsi_oversold})'
                )
            else:
                signal_type = 'HOLD'
                reason = (
                    f'价格接近下轨 (距离{dist_to_lower*100:.1f}%) '
                    f'但RSI未超卖 (RSI={current_rsi:.1f})'
                )
        
        # 卖出信号：价格触及上轨 + RSI超买
        elif dist_to_upper < self.bb_touch_pct:
            if current_rsi > self.rsi_overbought:
                signal_type = 'SELL'
                reason = (
                    f'价格触及上轨 (距离{dist_to_upper*100:.1f}%) + '
                    f'RSI超买 ({current_rsi:.1f} > {self.rsi_overbought})'
                )
            else:
                signal_type = 'HOLD'
                reason = (
                    f'价格接近上轨 (距离{dist_to_upper*100:.1f}%) '
                    f'但RSI未超买 (RSI={current_rsi:.1f})'
                )
        
        # 其他情况
        else:
            if current_rsi < self.rsi_oversold:
                signal_type = 'HOLD'
                reason = (
                    f'RSI超卖 ({current_rsi:.1f}) '
                    f'但价格未到下轨，等待更好位置'
                )
            elif current_rsi > self.rsi_overbought:
                signal_type = 'HOLD'
                reason = (
                    f'RSI超买 ({current_rsi:.1f}) '
                    f'但价格未到上轨，等待更好位置'
                )
            else:
                signal_type = 'HOLD'
                reason = f'价格在布林带中间，RSI中性 ({current_rsi:.1f})'
        
        # 建议价格
        if signal_type == 'BUY':
            suggest_min = current_bb_lower * 0.99
            suggest_max = current_bb_lower * 1.01
        elif signal_type == 'SELL':
            suggest_min = current_bb_upper * 0.99
            suggest_max = current_bb_upper * 1.01
        else:
            suggest_min = current_price * 0.99
            suggest_max = current_price * 1.01
        
        return {
            'type': signal_type,
            'reason': reason,
            'current_price': current_price,
            'suggest_price_min': suggest_min,
            'suggest_price_max': suggest_max,
            'indicators': {
                'BB_Upper': current_bb_upper,
                'BB_Middle': current_bb_mid,
                'BB_Lower': current_bb_lower,
                'BB_Width': band_width,
                'RSI': current_rsi,
                'Dist_to_Upper_%': dist_to_upper * 100,
                'Dist_to_Lower_%': dist_to_lower * 100,
            }
        }


# 使用示例
if __name__ == '__main__':
    print("""
Bollinger Bands + RSI 策略
========================================

策略特点:
1. ✅ 适用于震荡行情
2. ✅ 双重确认（BB + RSI）
3. ✅ 参数优化（阿里巴巴实测）
4. ✅ 清晰的买卖信号

使用场景:
- 科技股震荡期
- 叙事股区间波动
- 无明确趋势的市场

参数说明:
- bb_period: 布林带周期（推荐15）
- bb_devfactor: 标准差倍数（推荐2.0）
- rsi_period: RSI周期（推荐10）
- rsi_oversold: RSI超卖线（推荐35）
- rsi_overbought: RSI超买线（推荐75）

配合使用:
- 上涨趋势 → TSF-LSMA
- 震荡行情 → Bollinger RSI ⭐
- 动量启动 → MomentumSentiment
    """)
