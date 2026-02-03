"""
Backtrader Bollinger RSI Strategy
布林带+RSI策略（回测版本）

适用于震荡行情的回测
"""
import backtrader as bt


class BacktraderBollingerRSI(bt.Strategy):
    """
    Bollinger Bands + RSI 策略（Backtrader版本）
    
    策略逻辑:
    - 买入: 价格触及下轨 + RSI超卖
    - 卖出: 价格触及上轨 + RSI超买
    
    适用场景:
    - 震荡行情
    - 区间波动
    - 科技股、叙事股
    """
    
    params = (
        # 布林带参数
        ('bb_period', 15),        # 布林带周期（阿里最优）
        ('bb_devfactor', 2.0),    # 标准差倍数
        
        # RSI参数
        ('rsi_period', 10),       # RSI周期（阿里最优）
        ('rsi_oversold', 35),     # RSI超卖线（阿里最优）
        ('rsi_overbought', 75),   # RSI超买线（阿里最优）
        
        # 触及阈值
        ('bb_touch_pct', 0.01),   # 触及布林带阈值1%
        
        # 仓位管理
        ('position_size', 0.95),  # 最大仓位95%
        
        # 止损参数
        ('use_stop_loss', True),  # 是否使用止损
        ('stop_loss_pct', 0.02),  # 止损比例2%
        
        # 其他
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
        
        # 记录买卖信号
        self.buy_signals = []
        self.sell_signals = []
        self.equity_curve = []
        
        # === 计算布林带 ===
        self.bollinger = bt.indicators.BollingerBands(
            self.datas[0],
            period=self.params.bb_period,
            devfactor=self.params.bb_devfactor
        )
        
        # 布林带指标
        self.bb_top = self.bollinger.top
        self.bb_mid = self.bollinger.mid
        self.bb_bot = self.bollinger.bot
        
        # === 计算RSI ===
        self.rsi = bt.indicators.RSI(
            self.datas[0],
            period=self.params.rsi_period
        )
        
        self.log(f"策略初始化完成")
        self.log(f"  布林带周期: {self.params.bb_period}")
        self.log(f"  布林带倍数: {self.params.bb_devfactor}")
        self.log(f"  RSI周期: {self.params.rsi_period}")
        self.log(f"  RSI超卖线: {self.params.rsi_oversold}")
        self.log(f"  RSI超买线: {self.params.rsi_overbought}")
    
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
                if self.params.use_stop_loss:
                    self.stop_price = order.executed.price * (1 - self.params.stop_loss_pct)
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
        
        # 获取当前数据
        current_price = self.dataclose[0]
        current_bb_top = self.bb_top[0]
        current_bb_mid = self.bb_mid[0]
        current_bb_bot = self.bb_bot[0]
        current_rsi = self.rsi[0]
        
        # 计算距离布林带的百分比
        band_width = current_bb_top - current_bb_bot
        
        if band_width > 0:
            dist_to_top = (current_bb_top - current_price) / band_width
            dist_to_bot = (current_price - current_bb_bot) / band_width
        else:
            dist_to_top = 1.0
            dist_to_bot = 1.0
        
        # === 交易决策 ===
        if not self.position:  # 无持仓
            # 买入信号: 价格触及下轨 + RSI超卖
            if dist_to_bot < self.params.bb_touch_pct and current_rsi < self.params.rsi_oversold:
                # 计算买入数量
                cash = self.broker.getcash()
                price = self.dataclose[0]
                size = int((cash * self.params.position_size) / price)
                
                if size > 0:
                    self.log(
                        f'📈 买入信号: '
                        f'价格={current_price:.2f}, '
                        f'距下轨={dist_to_bot*100:.1f}%, '
                        f'RSI={current_rsi:.1f} (< {self.params.rsi_oversold})'
                    )
                    
                    self.order = self.buy(size=size)
                    self.buy_signals.append((
                        self.datas[0].datetime.date(0),
                        self.dataclose[0]
                    ))
        
        else:  # 有持仓
            # 止损检查
            if self.params.use_stop_loss and self.stop_price:
                if current_price < self.stop_price:
                    self.log(
                        f'🛑 触发止损: '
                        f'当前={current_price:.2f}, '
                        f'止损={self.stop_price:.2f}'
                    )
                    self.order = self.close()
                    self.sell_signals.append((
                        self.datas[0].datetime.date(0),
                        self.dataclose[0]
                    ))
                    return
            
            # 卖出信号: 价格触及上轨 + RSI超买
            if dist_to_top < self.params.bb_touch_pct and current_rsi > self.params.rsi_overbought:
                self.log(
                    f'📉 卖出信号: '
                    f'价格={current_price:.2f}, '
                    f'距上轨={dist_to_top*100:.1f}%, '
                    f'RSI={current_rsi:.1f} (> {self.params.rsi_overbought})'
                )
                
                self.order = self.close()
                self.sell_signals.append((
                    self.datas[0].datetime.date(0),
                    self.dataclose[0]
                ))
    
    def stop(self):
        """策略结束"""
        final_value = self.broker.getvalue()
        pnl = final_value - self.broker.startingcash
        pnl_pct = (pnl / self.broker.startingcash) * 100
        
        self.log(
            f'策略结束: '
            f'最终资产={final_value:.2f}, '
            f'收益={pnl:.2f} ({pnl_pct:+.2f}%)'
        )


# 使用示例
if __name__ == '__main__':
    print("""
Bollinger RSI 策略 (Backtrader版本)
========================================

策略特点:
1. ✅ 布林带 + RSI 双重确认
2. ✅ 适用于震荡行情
3. ✅ 参数已优化（阿里实测）
4. ✅ 内置止损保护

默认参数（阿里最优）:
- bb_period: 15
- bb_devfactor: 2.0
- rsi_period: 10
- rsi_oversold: 35
- rsi_overbought: 75

使用方法:
1. 在回测界面选择 "布林带RSI"
2. 使用默认参数或自定义
3. 适合震荡行情回测

注意事项:
- 震荡期效果最好
- 单边趋势表现一般
- 建议配合TSF-LSMA使用
    """)
