"""
凯利公式计算器
用于动态仓位管理
"""
import numpy as np
from typing import Optional, Dict, List


class KellyCalculator:
    """
    凯利公式仓位计算器
    
    凯利公式: f* = (p * b - q) / b
    其中:
        f* = 最优仓位比例
        p = 胜率
        q = 败率 = 1 - p
        b = 赔率 = 平均盈利 / 平均亏损
    """
    
    def __init__(
        self,
        initial_win_rate: float = 0.55,
        initial_avg_win: float = 0.05,
        initial_avg_loss: float = 0.02,
        kelly_fraction: float = 0.25,
        max_position: float = 1.0,
        min_position: float = 0.0
    ):
        """
        初始化凯利计算器
        
        Parameters:
        -----------
        initial_win_rate : float
            初始胜率（0-1之间），默认0.55
        initial_avg_win : float
            初始平均盈利（比例），默认0.05 (5%)
        initial_avg_loss : float
            初始平均亏损（比例），默认0.02 (2%)
        kelly_fraction : float
            凯利分数（保守系数），默认0.25 (1/4凯利)
            建议范围: 0.1-0.5
        max_position : float
            最大仓位，默认1.0 (100%)
        min_position : float
            最小仓位，默认0.0 (0%)
        """
        self.win_rate = initial_win_rate
        self.avg_win = initial_avg_win
        self.avg_loss = initial_avg_loss
        self.kelly_fraction = kelly_fraction
        self.max_position = max_position
        self.min_position = min_position
        
        # 交易历史（用于更新统计）
        self.trade_history = []
        
        print(f"✅ 凯利计算器已初始化:")
        print(f"   初始胜率: {self.win_rate:.1%}")
        print(f"   平均盈利: {self.avg_win:.1%}")
        print(f"   平均亏损: {self.avg_loss:.1%}")
        print(f"   凯利分数: {self.kelly_fraction:.2f}")
    
    def calculate_position(
        self,
        signal_strength: float = 0.5,
        adjust_for_signal: bool = True
    ) -> float:
        """
        计算最优仓位
        
        Parameters:
        -----------
        signal_strength : float (0-1)
            信号强度，用于调整胜率
        adjust_for_signal : bool
            是否根据信号强度调整胜率
        
        Returns:
        --------
        float : 建议仓位比例 (0-1)
        """
        # 根据信号强度调整胜率
        if adjust_for_signal:
            adjusted_win_rate = self._adjust_win_rate(signal_strength)
        else:
            adjusted_win_rate = self.win_rate
        
        # 计算凯利仓位
        kelly_position = self._kelly_formula(
            adjusted_win_rate,
            self.avg_win,
            self.avg_loss
        )
        
        # 应用凯利分数（保守调整）
        conservative_position = kelly_position * self.kelly_fraction
        
        # 限制在合理范围内
        final_position = np.clip(
            conservative_position,
            self.min_position,
            self.max_position
        )
        
        return final_position
    
    def _kelly_formula(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        凯利公式计算
        
        f* = (p * b - q) / b
        """
        if avg_loss <= 0:
            return 0.0
        
        p = win_rate
        q = 1 - win_rate
        b = avg_win / avg_loss  # 赔率
        
        kelly = (p * b - q) / b
        
        # 凯利值为负时不建议开仓
        return max(0.0, kelly)
    
    def _adjust_win_rate(self, signal_strength: float) -> float:
        """
        根据信号强度调整胜率
        
        Parameters:
        -----------
        signal_strength : float (0-1)
            信号强度
        
        Returns:
        --------
        float : 调整后的胜率
        """
        # 信号强度的影响范围：±10%
        adjustment = (signal_strength - 0.5) * 0.2
        
        adjusted = self.win_rate + adjustment
        
        # 限制在合理范围 (30%-80%)
        return np.clip(adjusted, 0.3, 0.8)
    
    def add_trade(
        self,
        profit: float,
        position_size: float = 1.0
    ):
        """
        添加交易记录
        
        Parameters:
        -----------
        profit : float
            交易盈亏（比例，如0.05表示盈利5%）
        position_size : float
            实际仓位大小
        """
        self.trade_history.append({
            'profit': profit,
            'position_size': position_size,
            'is_win': profit > 0
        })
    
    def update_statistics(self, lookback: int = 30):
        """
        更新统计数据
        
        Parameters:
        -----------
        lookback : int
            回溯交易数量
        """
        if len(self.trade_history) < 5:
            return  # 样本太少，不更新
        
        # 取最近N笔交易
        recent_trades = self.trade_history[-lookback:]
        
        # 计算胜率
        wins = [t for t in recent_trades if t['is_win']]
        losses = [t for t in recent_trades if not t['is_win']]
        
        new_win_rate = len(wins) / len(recent_trades)
        
        # 计算平均盈亏
        if wins:
            new_avg_win = np.mean([t['profit'] for t in wins])
        else:
            new_avg_win = self.avg_win
        
        if losses:
            new_avg_loss = abs(np.mean([t['profit'] for t in losses]))
        else:
            new_avg_loss = self.avg_loss
        
        # 平滑更新（EMA）
        alpha = 0.3  # 平滑系数
        self.win_rate = alpha * new_win_rate + (1 - alpha) * self.win_rate
        self.avg_win = alpha * new_avg_win + (1 - alpha) * self.avg_win
        self.avg_loss = alpha * new_avg_loss + (1 - alpha) * self.avg_loss
        
        print(f"📊 凯利参数已更新 (最近{len(recent_trades)}笔):")
        print(f"   胜率: {self.win_rate:.1%}")
        print(f"   平均盈利: {self.avg_win:.1%}")
        print(f"   平均亏损: {self.avg_loss:.1%}")
    
    def get_stats(self) -> Dict:
        """获取当前统计数据"""
        return {
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'payoff_ratio': self.avg_win / self.avg_loss if self.avg_loss > 0 else 0,
            'kelly_fraction': self.kelly_fraction,
            'total_trades': len(self.trade_history)
        }
    
    def simulate_positions(
        self,
        signal_strengths: List[float]
    ) -> List[float]:
        """
        模拟不同信号强度下的仓位
        
        Parameters:
        -----------
        signal_strengths : list
            信号强度列表
        
        Returns:
        --------
        list : 对应的仓位列表
        """
        return [
            self.calculate_position(s)
            for s in signal_strengths
        ]


class AdaptiveKellyCalculator(KellyCalculator):
    """
    自适应凯利计算器
    根据市场波动率动态调整
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.volatility_adjustment = True
        self.base_volatility = 0.3  # 基准波动率（30%）
    
    def calculate_position(
        self,
        signal_strength: float = 0.5,
        current_volatility: Optional[float] = None
    ) -> float:
        """
        计算考虑波动率的最优仓位
        
        Parameters:
        -----------
        signal_strength : float
            信号强度
        current_volatility : float, optional
            当前市场波动率（年化）
        
        Returns:
        --------
        float : 建议仓位
        """
        # 基础凯利仓位
        base_position = super().calculate_position(signal_strength)
        
        # 波动率调整
        if self.volatility_adjustment and current_volatility is not None:
            volatility_factor = self.base_volatility / current_volatility
            # 波动率高时减仓，波动率低时可以加仓（有限度）
            volatility_factor = np.clip(volatility_factor, 0.5, 1.5)
            
            adjusted_position = base_position * volatility_factor
            
            return np.clip(adjusted_position, self.min_position, self.max_position)
        
        return base_position


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*70)
    print("凯利公式计算器测试")
    print("="*70 + "\n")
    
    # 测试1: 基础凯利计算
    print("【测试1】基础凯利计算")
    print("-"*70)
    
    kelly = KellyCalculator(
        initial_win_rate=0.55,
        initial_avg_win=0.05,
        initial_avg_loss=0.02,
        kelly_fraction=0.25
    )
    
    # 不同信号强度的仓位
    print("\n不同信号强度下的建议仓位:")
    signal_strengths = [0.3, 0.5, 0.7, 0.9, 1.0]
    
    for strength in signal_strengths:
        position = kelly.calculate_position(strength)
        print(f"  信号强度 {strength:.1f}: {position:.1%} 仓位")
    
    # 测试2: 添加交易记录并更新
    print("\n\n【测试2】交易记录更新")
    print("-"*70)
    
    # 模拟一些交易
    trades = [
        (0.06, True),   # 盈利6%
        (-0.02, False), # 亏损2%
        (0.04, True),   # 盈利4%
        (0.08, True),   # 盈利8%
        (-0.015, False),# 亏损1.5%
        (0.05, True),   # 盈利5%
        (-0.02, False), # 亏损2%
        (0.07, True),   # 盈利7%
    ]
    
    for profit, _ in trades:
        kelly.add_trade(profit)
    
    print(f"\n添加了 {len(trades)} 笔交易")
    
    # 更新统计
    kelly.update_statistics()
    
    # 查看统计
    stats = kelly.get_stats()
    print(f"\n当前统计:")
    print(f"  胜率: {stats['win_rate']:.1%}")
    print(f"  平均盈利: {stats['avg_win']:.1%}")
    print(f"  平均亏损: {stats['avg_loss']:.1%}")
    print(f"  赔率: {stats['payoff_ratio']:.2f}")
    
    # 测试3: 自适应凯利（考虑波动率）
    print("\n\n【测试3】自适应凯利（波动率调整）")
    print("-"*70)
    
    adaptive_kelly = AdaptiveKellyCalculator(
        initial_win_rate=0.55,
        initial_avg_win=0.05,
        initial_avg_loss=0.02,
        kelly_fraction=0.25
    )
    
    volatilities = [0.2, 0.3, 0.5, 0.7]  # 不同波动率场景
    
    print("\n相同信号强度(0.7)，不同波动率下的仓位:")
    for vol in volatilities:
        position = adaptive_kelly.calculate_position(
            signal_strength=0.7,
            current_volatility=vol
        )
        print(f"  波动率 {vol:.0%}: {position:.1%} 仓位")
    
    print("\n" + "="*70)
    print("测试完成")
    print("="*70 + "\n")
    
    # 测试4: 可视化不同场景
    print("【测试4】不同场景下的凯利仓位")
    print("-"*70)
    
    scenarios = [
        ("保守型", 0.52, 0.03, 0.02, 0.25),
        ("标准型", 0.55, 0.05, 0.02, 0.25),
        ("激进型", 0.58, 0.07, 0.02, 0.50),
    ]
    
    for name, wr, aw, al, kf in scenarios:
        k = KellyCalculator(wr, aw, al, kf)
        pos = k.calculate_position(0.7)
        print(f"\n{name}:")
        print(f"  胜率={wr:.0%}, 盈亏比={aw/al:.1f}, 凯利分数={kf:.2f}")
        print(f"  → 建议仓位: {pos:.1%}")
