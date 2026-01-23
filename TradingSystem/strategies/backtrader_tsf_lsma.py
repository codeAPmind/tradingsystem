"""
Backtrader版本的TSF-LSMA策略
用于回测
"""
import numpy as np
import backtrader as bt


class TSFIndicator(bt.Indicator):
    """TSF - Time Series Forecast"""
    lines = ('tsf',)
    params = (('period', 9),)

    def __init__(self):
        self.addminperiod(self.params.period)

    def next(self):
        data = np.array([self.data[i] for i in range(-self.params.period + 1, 1)])
        x = np.arange(len(data))
        coeffs = np.polyfit(x, data, 1)
        a, b = coeffs[0], coeffs[1]
        tsf_value = a * self.params.period + b
        self.lines.tsf[0] = tsf_value


class LSMAIndicator(bt.Indicator):
    """LSMA - Least Squares Moving Average"""
    lines = ('lsma',)
    params = (('period', 20),)

    def __init__(self):
        self.addminperiod(self.params.period)

    def next(self):
        data = np.array([self.data[i] for i in range(-self.params.period + 1, 1)])
        x = np.arange(len(data))
        coeffs = np.polyfit(x, data, 1)
        a, b = coeffs[0], coeffs[1]
        lsma_value = a * (self.params.period - 1) + b
        self.lines.lsma[0] = lsma_value


class TSFLSMAStrategy(bt.Strategy):
    """TSF-LSMA策略（支持百分比和绝对值阈值）"""
    
    params = (
        ('tsf_period', 9),
        ('lsma_period', 20),
        ('buy_threshold', 0.5),      # 买入阈值（绝对值）
        ('sell_threshold', 0.5),     # 卖出阈值（绝对值）
        ('use_percent', False),      # 是否使用百分比阈值
        ('buy_threshold_pct', 0.5),  # 买入阈值（百分比%）
        ('sell_threshold_pct', 0.5), # 卖出阈值（百分比%）
        ('printlog', False),
    )

    def __init__(self):
        self.tsf = TSFIndicator(self.data.close, period=self.params.tsf_period)
        self.lsma = LSMAIndicator(self.data.close, period=self.params.lsma_period)
        self.diff = self.tsf - self.lsma
        self.order = None
        
        # 记录每日资产值（用于绘制收益曲线）
        self.equity_curve = []
        
        # 记录买卖信号（用于绘制标注）
        self.buy_signals = []  # [(date, price), ...]
        self.sell_signals = []  # [(date, price), ...]

    def log(self, txt, dt=None):
        if self.params.printlog:
            dt = dt or self.data.datetime.date(0)
            print(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行, 价格: ${order.executed.price:.2f}, '
                        f'成本: ${order.executed.value:.2f}, '
                        f'手续费: ${order.executed.comm:.2f}')
            elif order.issell():
                self.log(f'卖出执行, 价格: ${order.executed.price:.2f}, '
                        f'成本: ${order.executed.value:.2f}, '
                        f'手续费: ${order.executed.comm:.2f}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'交易利润, 毛利润: ${trade.pnl:.2f}, 净利润: ${trade.pnlcomm:.2f}')

    def next(self):
        # 记录每日资产值
        current_value = self.broker.getvalue()
        current_date = self.data.datetime.date(0)
        self.equity_curve.append({
            'date': current_date,
            'value': current_value
        })
        
        if self.order:
            return
        
        tsf_value = self.tsf[0]
        lsma_value = self.lsma[0]
        diff = self.diff[0]
        
        # 计算买卖阈值
        if self.params.use_percent:
            buy_threshold = lsma_value * (self.params.buy_threshold_pct / 100)
            sell_threshold = lsma_value * (self.params.sell_threshold_pct / 100)
        else:
            buy_threshold = self.params.buy_threshold
            sell_threshold = self.params.sell_threshold
        
        if not self.position:
            # 买入信号：TSF > LSMA + buy_threshold
            if diff > buy_threshold:
                current_date = self.data.datetime.date(0)
                current_price = self.data.close[0]
                self.buy_signals.append((current_date, current_price))
                
                self.log(f'🟢 买入信号! TSF({tsf_value:.2f}) > LSMA({lsma_value:.2f}) + {buy_threshold:.2f}')
                cash = self.broker.getcash()
                price = self.data.close[0]
                size = int(cash * 0.95 / price)
                
                if size > 0:
                    self.order = self.buy(size=size)
                else:
                    self.log('⚠️  资金不足，无法买入')
        else:
            # 卖出信号：TSF < LSMA - sell_threshold
            if diff < -sell_threshold:
                current_date = self.data.datetime.date(0)
                current_price = self.data.close[0]
                self.sell_signals.append((current_date, current_price))
                
                self.log(f'🔴 卖出信号! TSF({tsf_value:.2f}) < LSMA({lsma_value:.2f}) - {sell_threshold:.2f}')
                self.order = self.close()

    def stop(self):
        self.log(f'(TSF={self.params.tsf_period}, LSMA={self.params.lsma_period}, '
                f'买入阈值={self.params.buy_threshold if not self.params.use_percent else str(self.params.buy_threshold_pct)+"%"}, '
                f'卖出阈值={self.params.sell_threshold if not self.params.use_percent else str(self.params.sell_threshold_pct)+"%"}) '
                f'最终资产: ${self.broker.getvalue():.2f}', dt=None)
