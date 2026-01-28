"""
动量+情绪策略 (Backtrader版本)
Momentum + Sentiment Strategy

核心特性:
1. 相对强度过滤 (vs SPY)
2. 凯利公式动态仓位
3. AI情绪分析加成
"""
import backtrader as bt
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.sentiment_analyzer import SentimentAnalyzer, MockSentimentAnalyzer
    from utils.kelly_calculator import KellyCalculator
    UTILS_AVAILABLE = True
except ImportError:
    print("⚠️  工具模块导入失败，使用基础功能")
    UTILS_AVAILABLE = False


class MomentumSentimentStrategy(bt.Strategy):
    """
    动量+情绪策略
    
    策略逻辑:
    1. 技术指标: RSI + MACD + ADX (动量+趋势)
    2. 相对强度: TSLA vs SPY (只在强于大盘时买入)
    3. 情绪分析: AI分析新闻情绪 (可选)
    4. 动态仓位: 凯利公式计算最优仓位
    """
    
    params = (
        # === 技术指标参数 ===
        ('rsi_period', 14),
        ('rsi_threshold', 45),
        
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        
        ('adx_period', 14),
        ('adx_threshold', 15),
        
        # === 相对强度参数 ===
        ('use_relative_strength', True),
        ('rs_threshold', 1.1),  # TSLA RSI需比SPY高10%
        ('spy_rsi_oversold', 35),  # SPY超卖阈值
        
        # === 仓位管理参数 ===
        ('use_kelly', True),
        ('kelly_fraction', 0.25),  # 保守凯利
        ('max_position', 0.95),    # 最大95%仓位
        ('min_position', 0.0),
        
        # === 情绪分析参数 ===
        ('use_sentiment', False),  # 默认关闭（需要API密钥）
        ('sentiment_weight', 0.3),  # 情绪权重30%
        
        # === 其他参数 ===
        ('printlog', True),
        ('hold_days', 5),  # 最小持仓天数
    )
    
    def __init__(self):
        """初始化策略"""
        
        # === 数据引用 ===
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        
        # SPY数据（如果提供）
        if len(self.datas) > 1:
            self.spy_close = self.datas[1].close
            self.has_spy = True
        else:
            self.has_spy = False
            if self.params.use_relative_strength:
                print("⚠️  未提供SPY数据，相对强度过滤已禁用")
                self.params.use_relative_strength = False
        
        # === TSLA技术指标 ===
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
        
        # === SPY指标 (如果可用) ===
        if self.has_spy:
            self.spy_rsi = bt.indicators.RSI(
                self.datas[1],
                period=self.params.rsi_period
            )
        
        # === 凯利计算器 ===
        if self.params.use_kelly and UTILS_AVAILABLE:
            self.kelly = KellyCalculator(
                initial_win_rate=0.55,
                initial_avg_win=0.05,
                initial_avg_loss=0.02,
                kelly_fraction=self.params.kelly_fraction,
                max_position=self.params.max_position
            )
            self.use_kelly = True
        else:
            self.use_kelly = False
        
        # === 情绪分析器 ===
        if self.params.use_sentiment and UTILS_AVAILABLE:
            # 优先使用真实API，否则使用模拟
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self.sentiment = SentimentAnalyzer(api_key)
            else:
                print("⚠️  未设置API密钥，使用模拟情绪分析")
                self.sentiment = MockSentimentAnalyzer()
            self.use_sentiment = True
        else:
            self.use_sentiment = False
        
        # === 交易状态 ===
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.entry_date = None
        
        # === 信号记录（用于绘图）===
        self.buy_signals = []
        self.sell_signals = []
        
        # === 收益曲线记录 ===
        self.equity_curve = []
        
        if self.params.printlog:
            print("\n" + "="*70)
            print("动量+情绪策略已初始化".center(70))
            print("="*70)
            print(f"相对强度过滤: {'✅ 启用' if self.params.use_relative_strength else '❌ 禁用'}")
            print(f"凯利仓位管理: {'✅ 启用' if self.use_kelly else '❌ 禁用'}")
            print(f"情绪分析: {'✅ 启用' if self.use_sentiment else '❌ 禁用'}")
            print("="*70 + "\n")
    
    def notify_order(self, order):
        """订单通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.entry_date = self.datas[0].datetime.date(0)
                
                if self.params.printlog:
                    print(f'✅ 买入执行: 价格={order.executed.price:.2f}, '
                          f'数量={order.executed.size:.0f}, '
                          f'手续费={order.executed.comm:.2f}')
            
            elif order.issell():
                if self.params.printlog:
                    print(f'✅ 卖出执行: 价格={order.executed.price:.2f}, '
                          f'数量={order.executed.size:.0f}, '
                          f'手续费={order.executed.comm:.2f}')
                
                # 记录交易到凯利计算器
                if self.use_kelly and self.buyprice:
                    profit_pct = (order.executed.price - self.buyprice) / self.buyprice
                    self.kelly.add_trade(profit_pct)
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if self.params.printlog:
                print('❌ 订单失败')
        
        self.order = None
    
    def notify_trade(self, trade):
        """交易通知"""
        if not trade.isclosed:
            return
        
        if self.params.printlog:
            print(f'💰 交易利润: 毛利={trade.pnl:.2f}, 净利={trade.pnlcomm:.2f}')
    
    def next(self):
        """策略逻辑主函数"""
        
        # 记录收益曲线
        self.equity_curve.append({
            'date': self.datas[0].datetime.date(0),
            'value': self.broker.getvalue()
        })
        
        # 如果有待处理订单，等待
        if self.order:
            return
        
        # === 1. 计算技术信号 ===
        technical_signal = self._calculate_technical_signal()
        
        # === 2. 相对强度过滤 ===
        if self.params.use_relative_strength:
            relative_strength = self._calculate_relative_strength()
            
            # 大盘极弱 → 平仓
            if self.has_spy and self.spy_rsi[0] < self.params.spy_rsi_oversold:
                if self.position:
                    if self.params.printlog:
                        print(f'⚠️  SPY超卖({self.spy_rsi[0]:.1f}), 平仓保护')
                    self.order = self.sell()
                    self.sell_signals.append((
                        self.datas[0].datetime.date(0),
                        self.dataclose[0]
                    ))
                return
        else:
            relative_strength = 0.5  # 中性
        
        # === 3. 情绪分析 ===
        sentiment_score = self._get_sentiment_score()
        
        # === 4. 融合决策 ===
        combined_signal = self._combine_signals(
            technical_signal,
            relative_strength,
            sentiment_score
        )
        
        # === 5. 执行交易 ===
        if not self.position:
            # 无持仓 → 检查买入条件
            if combined_signal['magnitude'] > 0.5:
                # 计算仓位
                position_size = self._calculate_position_size(
                    combined_signal['magnitude']
                )
                
                if position_size > 0.01:  # 至少1%仓位才交易
                    self.order = self.order_target_percent(target=position_size)
                    
                    self.buy_signals.append((
                        self.datas[0].datetime.date(0),
                        self.dataclose[0]
                    ))
                    
                    if self.params.printlog:
                        print(f'\n📈 买入信号:')
                        print(f'   日期: {self.datas[0].datetime.date(0)}')
                        print(f'   价格: {self.dataclose[0]:.2f}')
                        print(f'   技术信号: {technical_signal:.2f}')
                        print(f'   相对强度: {relative_strength:.2f}')
                        print(f'   情绪分数: {sentiment_score:+.2f}')
                        print(f'   综合信号: {combined_signal["magnitude"]:.2f}')
                        print(f'   目标仓位: {position_size:.1%}')
        
        else:
            # 有持仓 → 检查卖出条件
            
            # 持有天数检查
            if self.entry_date:
                hold_days = (self.datas[0].datetime.date(0) - self.entry_date).days
                if hold_days < self.params.hold_days:
                    return  # 未满最小持仓天数
            
            # 信号转弱 → 卖出
            if combined_signal['magnitude'] < 0.3:
                self.order = self.sell()
                
                self.sell_signals.append((
                    self.datas[0].datetime.date(0),
                    self.dataclose[0]
                ))
                
                if self.params.printlog:
                    print(f'\n📉 卖出信号:')
                    print(f'   日期: {self.datas[0].datetime.date(0)}')
                    print(f'   价格: {self.dataclose[0]:.2f}')
                    print(f'   综合信号: {combined_signal["magnitude"]:.2f} (转弱)')
                    
                    if self.buyprice:
                        profit_pct = (self.dataclose[0] - self.buyprice) / self.buyprice
                        print(f'   收益: {profit_pct:+.1%}')
    
    def _calculate_technical_signal(self) -> float:
        """计算技术指标信号强度 (0-1)"""
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
            macd_strength = min(abs(macd_diff) / 5.0, 1.0)
            signals.append(macd_strength)
        else:
            signals.append(0.0)
        
        # ADX信号
        if self.adx[0] > self.params.adx_threshold:
            adx_strength = min((self.adx[0] - self.params.adx_threshold) / 35, 1.0)
            signals.append(adx_strength)
        else:
            signals.append(0.0)
        
        return np.mean(signals)
    
    def _calculate_relative_strength(self) -> float:
        """计算相对强度 (0-1)"""
        if not self.has_spy:
            return 0.5  # 中性
        
        if self.spy_rsi[0] > 0:
            rs = self.rsi[0] / self.spy_rsi[0]
        else:
            rs = 1.0
        
        # 归一化到0-1 (假设RS范围0.5-2.0)
        normalized_rs = (rs - 0.5) / 1.5
        
        return max(0, min(normalized_rs, 1.0))
    
    def _get_sentiment_score(self) -> float:
        """获取情绪分数 (-1 to 1)"""
        if not self.use_sentiment:
            return 0.0
        
        # 简化版：每天获取一次
        # 实际应该集成新闻API
        
        # 这里使用模拟数据
        # 实际使用时应该调用: self.sentiment.analyze_news_batch(news_list, 'TSLA')
        
        return 0.0  # 中性
    
    def _combine_signals(
        self,
        technical: float,
        relative_strength: float,
        sentiment: float
    ) -> dict:
        """
        融合信号
        
        Returns:
        --------
        dict: {
            'magnitude': float (0-1),
            'direction': str ('LONG', 'FLAT')
        }
        """
        # 检查是否满足基本条件
        if self.params.use_relative_strength:
            if relative_strength < 0.3:  # TSLA相对太弱
                return {'magnitude': 0.0, 'direction': 'FLAT'}
        
        # 加权融合
        tech_weight = 0.5
        rs_weight = 0.3 if self.params.use_relative_strength else 0.0
        sent_weight = self.params.sentiment_weight if self.use_sentiment else 0.0
        
        # 标准化权重
        total_weight = tech_weight + rs_weight + sent_weight
        if total_weight == 0:
            total_weight = 1.0
        
        # 情绪从-1~1映射到0~1
        sentiment_normalized = (sentiment + 1) / 2
        
        weighted_signal = (
            technical * tech_weight +
            relative_strength * rs_weight +
            sentiment_normalized * sent_weight
        ) / total_weight
        
        # 协同加成（所有信号都强时）
        if technical > 0.6 and relative_strength > 0.6 and sentiment > 0.3:
            weighted_signal += 0.15
        
        magnitude = min(weighted_signal, 1.0)
        
        return {
            'magnitude': magnitude,
            'direction': 'LONG' if magnitude > 0.5 else 'FLAT'
        }
    
    def _calculate_position_size(self, signal_strength: float) -> float:
        """计算仓位大小"""
        if self.use_kelly:
            # 使用凯利公式
            position = self.kelly.calculate_position(signal_strength)
        else:
            # 固定仓位
            position = self.params.max_position
        
        return position
    
    def stop(self):
        """策略结束时调用"""
        if self.params.printlog:
            print('\n' + '='*70)
            print('策略运行结束'.center(70))
            print('='*70)
            print(f'最终资产: ${self.broker.getvalue():.2f}')
            
            if self.use_kelly:
                stats = self.kelly.get_stats()
                print(f'\n凯利统计:')
                print(f'  总交易: {stats["total_trades"]}')
                print(f'  胜率: {stats["win_rate"]:.1%}')
                print(f'  盈亏比: {stats["payoff_ratio"]:.2f}')
            
            print('='*70 + '\n')


# 使用示例
if __name__ == '__main__':
    print("请通过回测引擎运行此策略")
    print("示例: python main.py -> 选择动量+情绪策略")
