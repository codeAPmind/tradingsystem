"""
Momentum Sentiment Strategy - 动量情绪策略
结合技术指标、相对强度和AI情绪分析的增强型策略
"""
import backtrader as bt
import anthropic
import json
from datetime import datetime, timedelta


class MomentumSentimentStrategy(bt.Strategy):
    """
    动量情绪策略
    
    核心特点:
    1. 技术指标: RSI + MACD + ADX 三重确认
    2. 相对强度: TSLA vs SPY 过滤
    3. 情绪分析: AI分析新闻情绪（可选）
    4. 动态仓位: 凯利公式 + 信号强度
    5. 动态止损: ATR跟踪止损
    
    适用场景:
    - 趋势性强的股票（如TSLA）
    - 波动率较高的市场
    - 有新闻影响的标的
    """
    
    params = (
        # 技术指标参数
        ('rsi_period', 14),
        ('rsi_threshold', 45),
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        ('adx_period', 14),
        ('adx_threshold', 15),
        ('atr_period', 14),
        
        # 相对强度参数
        ('use_relative_strength', True),
        ('rs_threshold', 1.1),  # TSLA RSI需要比SPY高10%
        ('spy_oversold', 35),    # SPY超卖阈值（防守）
        
        # 仓位管理参数
        ('use_kelly', True),
        ('kelly_fraction', 0.25),  # 保守凯利：1/4
        ('win_rate', 0.55),        # 历史胜率（需要回测统计）
        ('avg_win', 0.05),         # 平均盈利5%
        ('avg_loss', 0.02),        # 平均亏损2%
        ('max_position', 0.95),    # 最大仓位95%
        
        # 止损参数
        ('atr_stop_multiplier', 1.5),  # ATR止损倍数
        ('trailing_stop', True),       # 是否使用跟踪止损
        
        # 情绪分析参数
        ('use_sentiment', False),      # 是否启用情绪分析（需要API key）
        ('sentiment_weight', 0.2),     # 情绪权重20%
        ('technical_weight', 0.5),     # 技术指标权重50%
        ('rs_weight', 0.3),            # 相对强度权重30%
        
        # 其他参数
        ('printlog', True),
    )
    
    def __init__(self):
        """初始化策略"""
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        
        # 订单跟踪
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        self.stop_price = None
        
        # 记录买卖信号（用于绘图）
        self.buy_signals = []
        self.sell_signals = []
        self.equity_curve = []
        
        # === 技术指标（主标的 - TSLA）===
        self.rsi = bt.indicators.RSI(
            self.datas[0],
            period=self.params.rsi_period
        )
        
        self.macd = bt.indicators.MACD(
            self.datas[0],
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal
        )
        
        self.adx = bt.indicators.ADX(
            self.datas[0],
            period=self.params.adx_period
        )
        
        self.atr = bt.indicators.ATR(
            self.datas[0],
            period=self.params.atr_period
        )
        
        # === 基准指标（SPY - 如果提供）===
        self.spy_available = len(self.datas) > 1
        
        if self.spy_available and self.params.use_relative_strength:
            self.spy_rsi = bt.indicators.RSI(
                self.datas[1],
                period=self.params.rsi_period
            )
            self.spy_macd = bt.indicators.MACD(
                self.datas[1],
                period_me1=self.params.macd_fast,
                period_me2=self.params.macd_slow,
                period_signal=self.params.macd_signal
            )
            
            # 相对强度指标
            self.relative_strength = self.rsi / self.spy_rsi
        else:
            self.spy_rsi = None
            self.spy_macd = None
            self.relative_strength = None
        
        # === 情绪分析（可选）===
        if self.params.use_sentiment:
            try:
                import os
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if api_key:
                    self.claude_client = anthropic.Anthropic(api_key=api_key)
                    self.sentiment_enabled = True
                    self.log("✅ 情绪分析已启用")
                else:
                    self.sentiment_enabled = False
                    self.log("⚠️  未设置ANTHROPIC_API_KEY，情绪分析禁用")
            except:
                self.sentiment_enabled = False
                self.log("⚠️  Anthropic库未安装，情绪分析禁用")
        else:
            self.sentiment_enabled = False
        
        self.sentiment_cache = {}
        self.last_sentiment_date = None
        
        self.log(f"策略初始化完成")
        self.log(f"  相对强度过滤: {'启用' if self.params.use_relative_strength and self.spy_available else '禁用'}")
        self.log(f"  凯利仓位管理: {'启用' if self.params.use_kelly else '禁用'}")
        self.log(f"  情绪分析: {'启用' if self.sentiment_enabled else '禁用'}")
    
    def log(self, txt, dt=None):
        """日志输出"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
                self.log(
                    f'买入执行: 价格={order.executed.price:.2f}, '
                    f'成本={order.executed.value:.2f}, '
                    f'手续费={order.executed.comm:.2f}'
                )
                
                # 计算止损价
                if self.params.trailing_stop:
                    self.stop_price = order.executed.price - (
                        self.atr[0] * self.params.atr_stop_multiplier
                    )
                    self.log(f'  止损价: {self.stop_price:.2f}')
                
            else:  # 卖出
                self.log(
                    f'卖出执行: 价格={order.executed.price:.2f}, '
                    f'成本={order.executed.value:.2f}, '
                    f'手续费={order.executed.comm:.2f}'
                )
                
                # 计算盈亏
                if self.buy_price:
                    profit = order.executed.price - self.buy_price
                    profit_pct = (profit / self.buy_price) * 100
                    self.log(f'  盈亏: {profit:.2f} ({profit_pct:+.2f}%)')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'订单取消/保证金不足/被拒绝')
        
        self.order = None
    
    def notify_trade(self, trade):
        """交易通知"""
        if not trade.isclosed:
            return
        
        self.log(f'交易盈亏: 毛利={trade.pnl:.2f}, 净利={trade.pnlcomm:.2f}')
    
    def next(self):
        """策略主逻辑"""
        # 记录资产曲线
        self.equity_curve.append({
            'date': self.datas[0].datetime.date(0),
            'value': self.broker.getvalue()
        })
        
        # 如果有待处理订单，不操作
        if self.order:
            return
        
        # === 1. 计算技术信号 ===
        technical_signal = self._calculate_technical_signal()
        
        # === 2. 计算相对强度 ===
        if self.params.use_relative_strength and self.spy_available:
            rs_signal = self._calculate_relative_strength_signal()
            
            # 大盘极弱，防守性平仓
            if self.spy_rsi[0] < self.params.spy_oversold and self.position:
                self.log(f'⏸️  大盘超卖({self.spy_rsi[0]:.2f})，防守性平仓')
                self.order = self.close()
                self.sell_signals.append((
                    self.datas[0].datetime.date(0),
                    self.dataclose[0]
                ))
                return
        else:
            rs_signal = 0.5  # 中性
        
        # === 3. 计算情绪信号（可选）===
        if self.sentiment_enabled:
            sentiment_signal = self._get_sentiment_signal()
        else:
            sentiment_signal = 0.0  # 中性
        
        # === 4. 融合信号 ===
        combined_signal = self._combine_signals(
            technical_signal,
            rs_signal,
            sentiment_signal
        )
        
        # === 5. 交易决策 ===
        if not self.position:  # 无持仓
            if combined_signal['magnitude'] > 0.6:  # 强信号阈值
                # 计算仓位
                position_size = self._calculate_position_size(
                    combined_signal['magnitude']
                )
                
                if position_size > 0:
                    # 计算买入股数
                    cash = self.broker.getcash()
                    price = self.dataclose[0]
                    size = int((cash * position_size) / price)
                    
                    if size > 0:
                        self.log(
                            f'📈 买入信号: 技术={technical_signal:.2f}, '
                            f'相对强度={rs_signal:.2f}, 情绪={sentiment_signal:.2f}, '
                            f'综合={combined_signal["magnitude"]:.2f}, '
                            f'仓位={position_size*100:.1f}%'
                        )
                        
                        self.order = self.buy(size=size)
                        self.buy_signals.append((
                            self.datas[0].datetime.date(0),
                            self.dataclose[0]
                        ))
        
        else:  # 有持仓
            # 动态跟踪止损
            if self.params.trailing_stop:
                new_stop = self.dataclose[0] - (
                    self.atr[0] * self.params.atr_stop_multiplier
                )
                
                if new_stop > self.stop_price:
                    self.stop_price = new_stop
                
                # 触发止损
                if self.dataclose[0] < self.stop_price:
                    self.log(f'🛑 止损触发: 当前={self.dataclose[0]:.2f}, 止损={self.stop_price:.2f}')
                    self.order = self.close()
                    self.sell_signals.append((
                        self.datas[0].datetime.date(0),
                        self.dataclose[0]
                    ))
                    return
            
            # 信号转弱，主动平仓
            if combined_signal['magnitude'] < 0.3:
                self.log(f'📉 信号转弱({combined_signal["magnitude"]:.2f})，主动平仓')
                self.order = self.close()
                self.sell_signals.append((
                    self.datas[0].datetime.date(0),
                    self.dataclose[0]
                ))
    
    def _calculate_technical_signal(self):
        """计算技术指标信号强度（0-1）"""
        signals = []
        
        # RSI信号
        if self.rsi[0] > self.params.rsi_threshold:
            rsi_strength = (self.rsi[0] - self.params.rsi_threshold) / (100 - self.params.rsi_threshold)
            signals.append(min(rsi_strength, 1.0))
        else:
            signals.append(0.0)
        
        # MACD信号
        if self.macd.macd[0] > self.macd.signal[0]:
            macd_diff = self.macd.macd[0] - self.macd.signal[0]
            macd_strength = min(abs(macd_diff) / 5.0, 1.0)  # 假设5为强信号
            signals.append(macd_strength)
        else:
            signals.append(0.0)
        
        # ADX信号
        if self.adx[0] > self.params.adx_threshold:
            adx_strength = min(
                (self.adx[0] - self.params.adx_threshold) / (50 - self.params.adx_threshold),
                1.0
            )
            signals.append(adx_strength)
        else:
            signals.append(0.0)
        
        # 平均信号强度
        avg_signal = sum(signals) / len(signals) if signals else 0.0
        
        return avg_signal
    
    def _calculate_relative_strength_signal(self):
        """计算相对强度信号（0-1）"""
        if not self.spy_available or self.spy_rsi[0] == 0:
            return 0.5  # 中性
        
        # RSI相对强度
        rs = self.rsi[0] / self.spy_rsi[0]
        
        # 归一化到0-1（假设RS范围0.5-2.0）
        normalized_rs = (rs - 0.5) / 1.5
        normalized_rs = max(0, min(normalized_rs, 1.0))
        
        return normalized_rs
    
    def _get_sentiment_signal(self):
        """
        获取情绪信号（-1到+1）
        注意：这是简化版本，实际需要新闻API
        """
        if not self.sentiment_enabled:
            return 0.0
        
        current_date = self.datas[0].datetime.date(0)
        
        # 检查缓存
        if current_date == self.last_sentiment_date:
            return self.sentiment_cache.get(current_date, 0.0)
        
        # 这里应该调用新闻API和Claude分析
        # 由于回测时无法获取历史新闻，这里返回模拟值
        # 在实盘时，应该替换为真实的情绪分析
        
        sentiment = 0.0  # 默认中性
        
        # 示例：可以基于价格波动模拟情绪
        # 实际应该使用真实新闻数据
        if len(self.dataclose) > 5:
            price_change = (self.dataclose[0] - self.dataclose[-5]) / self.dataclose[-5]
            sentiment = max(-1.0, min(1.0, price_change * 10))  # 简化映射
        
        self.sentiment_cache[current_date] = sentiment
        self.last_sentiment_date = current_date
        
        return sentiment
    
    def _combine_signals(self, technical, rs, sentiment):
        """
        融合信号
        
        Returns:
        --------
        dict : {
            'direction': 'LONG' | 'FLAT',
            'magnitude': 0.0 ~ 1.0
        }
        """
        # 加权平均
        weighted_signal = (
            technical * self.params.technical_weight +
            rs * self.params.rs_weight +
            (sentiment + 1) / 2 * self.params.sentiment_weight
        )
        
        # 协同加成（所有信号都强时）
        if technical > 0.6 and rs > 0.6 and sentiment > 0.3:
            synergy_bonus = 0.15 * technical * rs
            weighted_signal += synergy_bonus
        
        magnitude = min(weighted_signal, 1.0)
        
        return {
            'direction': 'LONG' if magnitude > 0.5 else 'FLAT',
            'magnitude': magnitude
        }
    
    def _calculate_position_size(self, signal_strength):
        """
        计算仓位大小
        
        Parameters:
        -----------
        signal_strength : float (0-1)
            信号强度
        
        Returns:
        --------
        float : 仓位比例 (0-1)
        """
        if not self.params.use_kelly:
            # 固定仓位
            return self.params.max_position * signal_strength
        
        # 凯利公式
        # 根据信号强度调整胜率
        adjusted_win_rate = self.params.win_rate + (signal_strength - 0.5) * 0.1
        adjusted_win_rate = max(0.4, min(0.7, adjusted_win_rate))
        
        p = adjusted_win_rate
        q = 1 - p
        b = self.params.avg_win / self.params.avg_loss
        
        # 完整凯利
        kelly_full = (p * b - q) / b
        
        # 保守凯利
        kelly_conservative = kelly_full * self.params.kelly_fraction
        
        # 限制在[0, max_position]
        position = max(0, min(kelly_conservative, self.params.max_position))
        
        return position
    
    def stop(self):
        """策略结束"""
        self.log(
            f'策略结束: 最终资产={self.broker.getvalue():.2f}, '
            f'收益={(self.broker.getvalue() - self.broker.startingcash):.2f}'
        )


# 使用示例
if __name__ == '__main__':
    import sys
    sys.path.append('..')
    
    print("""
动量情绪策略 (Momentum Sentiment Strategy)
========================================

策略特点:
1. ✅ 技术指标三重确认 (RSI + MACD + ADX)
2. ✅ 相对强度过滤 (TSLA vs SPY)
3. ✅ 凯利公式动态仓位
4. ✅ ATR动态跟踪止损
5. ✅ AI情绪分析（可选）

使用方法:
1. 在回测界面选择"动量情绪"策略
2. 设置参数（使用默认值即可）
3. 开始回测

参数说明:
- rsi_threshold: RSI阈值（默认45）
- rs_threshold: 相对强度阈值（默认1.1）
- kelly_fraction: 凯利比例（默认0.25）
- atr_stop_multiplier: 止损倍数（默认1.5）

注意事项:
- 建议使用至少1年的历史数据
- 情绪分析需要API密钥（可选）
- 相对强度过滤需要SPY数据
    """)
