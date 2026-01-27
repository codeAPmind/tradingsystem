#!/usr/bin/env python3
"""
风控管理器
Risk Management System

功能:
1. 单笔金额限制
2. 单日交易次数限制
3. 持仓比例限制
4. 止损/止盈检查
5. 资金充足性检查
"""
from datetime import datetime, date


class RiskManager:
    """风控管理器"""
    
    def __init__(self):
        """初始化风控管理器"""
        
        # ==================== 风控参数 ====================
        
        # 金额限制
        self.max_single_amount = 50000      # 单笔最大金额（美元）
        self.max_single_amount_hk = 400000  # 单笔最大金额（港币）
        
        # 交易次数限制
        self.max_daily_trades = 20          # 单日最大交易次数
        
        # 持仓限制
        self.max_position_ratio = 0.3       # 单只股票最大持仓比例（30%）
        self.max_total_position = 0.9       # 最大总持仓比例（90%）
        
        # 止损止盈
        self.stop_loss_ratio = 0.05         # 止损比例（5%）
        self.take_profit_ratio = 0.10       # 止盈比例（10%）
        
        # 最小持仓时间
        self.min_holding_hours = 1          # 最小持仓时间（小时）
        
        # ==================== 统计数据 ====================
        
        # 今日交易统计
        self.daily_trades = 0
        self.daily_buy_amount = 0
        self.daily_sell_amount = 0
        self.last_reset_date = date.today()
        
        # 交易记录
        self.trade_history = []
        
        print(f"\n{'='*70}")
        print(f"{'风控管理器初始化':^70}")
        print(f"{'='*70}")
        print(f"单笔最大金额: ${self.max_single_amount:,.0f} / HK${self.max_single_amount_hk:,.0f}")
        print(f"单日最大交易次数: {self.max_daily_trades}")
        print(f"单只股票最大持仓: {self.max_position_ratio:.1%}")
        print(f"止损比例: {self.stop_loss_ratio:.1%}")
        print(f"止盈比例: {self.take_profit_ratio:.1%}")
        print(f"{'='*70}\n")
    
    def check_order(self, order_data, account_info=None, positions=None):
        """
        风控检查
        
        Parameters:
        -----------
        order_data : dict
            订单数据
            {
                'stock_code': str,
                'direction': 'BUY' or 'SELL',
                'price': float,
                'qty': int
            }
        account_info : dict, optional
            账户信息
        positions : list, optional
            当前持仓列表
        
        Returns:
        --------
        tuple : (is_pass, reason)
            is_pass: bool - 是否通过
            reason: str - 原因
        """
        # 每日统计自动重置
        self._check_and_reset_daily()
        
        stock_code = order_data.get('stock_code', '')
        direction = order_data.get('direction', 'BUY')
        price = order_data.get('price', 0)
        qty = order_data.get('qty', 0)
        
        # 计算金额
        amount = price * qty
        
        print(f"\n[风控检查] 开始检查订单:")
        print(f"  股票: {stock_code}")
        print(f"  方向: {direction}")
        print(f"  价格: ${price:.2f}")
        print(f"  数量: {qty}")
        print(f"  金额: ${amount:,.2f}")
        
        # ==================== 检查1: 单笔金额限制 ====================
        
        is_hk = stock_code.startswith('HK.')
        max_amount = self.max_single_amount_hk if is_hk else self.max_single_amount
        currency = 'HK$' if is_hk else '$'
        
        if amount > max_amount:
            reason = f"单笔金额超限（{currency}{amount:,.2f} > {currency}{max_amount:,.2f}）"
            print(f"[风控检查] ❌ {reason}")
            return False, reason
        
        print(f"[风控检查] ✅ 单笔金额检查通过")
        
        # ==================== 检查2: 今日交易次数限制 ====================
        
        if self.daily_trades >= self.max_daily_trades:
            reason = f"今日交易次数已达上限（{self.daily_trades}/{self.max_daily_trades}）"
            print(f"[风控检查] ❌ {reason}")
            return False, reason
        
        print(f"[风控检查] ✅ 交易次数检查通过（{self.daily_trades}/{self.max_daily_trades}）")
        
        # ==================== 检查3: 资金检查（买入时）====================
        
        if direction == 'BUY' and account_info:
            available = account_info.get('cash', 0)
            if available == 0:
                available = account_info.get('avl_withdrawal_cash', 0)
            
            if amount > available:
                reason = f"资金不足（需要${amount:,.2f}，可用${available:,.2f}）"
                print(f"[风控检查] ❌ {reason}")
                return False, reason
            
            print(f"[风控检查] ✅ 资金充足（需要${amount:,.2f}，可用${available:,.2f}）")
        
        # ==================== 检查4: 持仓比例限制（买入时）====================
        
        if direction == 'BUY' and account_info and positions is not None:
            total_assets = account_info.get('total_assets', 0)
            
            if total_assets > 0:
                # 计算买入后的持仓比例
                new_position_ratio = amount / total_assets
                
                if new_position_ratio > self.max_position_ratio:
                    reason = f"单只股票持仓比例将超限（{new_position_ratio:.1%} > {self.max_position_ratio:.1%}）"
                    print(f"[风控检查] ❌ {reason}")
                    return False, reason
                
                print(f"[风控检查] ✅ 持仓比例检查通过（{new_position_ratio:.1%}/{self.max_position_ratio:.1%}）")
                
                # 检查总持仓比例
                current_position_value = sum(
                    pos.get('market_val', 0) for pos in positions
                )
                new_total_position = (current_position_value + amount) / total_assets
                
                if new_total_position > self.max_total_position:
                    reason = f"总持仓比例将超限（{new_total_position:.1%} > {self.max_total_position:.1%}）"
                    print(f"[风控检查] ❌ {reason}")
                    return False, reason
                
                print(f"[风控检查] ✅ 总持仓比例检查通过（{new_total_position:.1%}/{self.max_total_position:.1%}）")
        
        # ==================== 检查5: 卖出时持仓检查 ====================
        
        if direction == 'SELL' and positions is not None:
            # 检查是否有持仓
            has_position = False
            available_qty = 0
            
            for pos in positions:
                if pos.get('code') == stock_code:
                    has_position = True
                    available_qty = pos.get('can_sell_qty', pos.get('qty', 0))
                    break
            
            if not has_position:
                reason = f"无持仓无法卖出（{stock_code}）"
                print(f"[风控检查] ❌ {reason}")
                return False, reason
            
            if qty > available_qty:
                reason = f"可卖数量不足（需要{qty}，可卖{available_qty}）"
                print(f"[风控检查] ❌ {reason}")
                return False, reason
            
            print(f"[风控检查] ✅ 持仓检查通过（可卖{available_qty}）")
        
        # ==================== 所有检查通过 ====================
        
        print(f"[风控检查] ✅ 所有检查通过\n")
        return True, "通过"
    
    def update_daily_stats(self, order_data):
        """
        更新今日统计
        
        Parameters:
        -----------
        order_data : dict
            订单数据
        """
        self._check_and_reset_daily()
        
        direction = order_data.get('direction', 'BUY')
        amount = order_data.get('price', 0) * order_data.get('qty', 0)
        
        self.daily_trades += 1
        
        if direction == 'BUY':
            self.daily_buy_amount += amount
        else:
            self.daily_sell_amount += amount
        
        # 记录交易
        self.trade_history.append({
            'time': datetime.now(),
            'stock_code': order_data.get('stock_code'),
            'direction': direction,
            'amount': amount
        })
        
        print(f"[风控统计] 今日交易次数: {self.daily_trades}")
        print(f"[风控统计] 今日买入金额: ${self.daily_buy_amount:,.2f}")
        print(f"[风控统计] 今日卖出金额: ${self.daily_sell_amount:,.2f}")
    
    def check_stop_loss_take_profit(self, position):
        """
        检查止损止盈
        
        Parameters:
        -----------
        position : dict
            持仓数据
        
        Returns:
        --------
        tuple : (should_close, reason)
        """
        pl_ratio = position.get('pl_ratio', 0) / 100  # 转换为小数
        
        # 止损检查
        if pl_ratio <= -self.stop_loss_ratio:
            reason = f"触发止损（亏损{pl_ratio:.1%}，止损线{-self.stop_loss_ratio:.1%}）"
            return True, reason
        
        # 止盈检查
        if pl_ratio >= self.take_profit_ratio:
            reason = f"触发止盈（盈利{pl_ratio:.1%}，止盈线{self.take_profit_ratio:.1%}）"
            return True, reason
        
        return False, "正常"
    
    def _check_and_reset_daily(self):
        """检查并重置每日统计"""
        today = date.today()
        
        if today != self.last_reset_date:
            print(f"\n[风控] 日期变更，重置统计（{self.last_reset_date} -> {today}）")
            self.reset_daily_stats()
            self.last_reset_date = today
    
    def reset_daily_stats(self):
        """重置今日统计"""
        self.daily_trades = 0
        self.daily_buy_amount = 0
        self.daily_sell_amount = 0
        print(f"[风控] ✅ 今日统计已重置")
    
    def get_daily_stats(self):
        """获取今日统计"""
        self._check_and_reset_daily()
        
        return {
            'trades': self.daily_trades,
            'buy_amount': self.daily_buy_amount,
            'sell_amount': self.daily_sell_amount,
            'total_amount': self.daily_buy_amount + self.daily_sell_amount
        }
    
    def set_params(self, **kwargs):
        """
        设置风控参数
        
        Parameters:
        -----------
        max_single_amount : float
            单笔最大金额
        max_daily_trades : int
            单日最大交易次数
        max_position_ratio : float
            单只股票最大持仓比例
        stop_loss_ratio : float
            止损比例
        take_profit_ratio : float
            止盈比例
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                print(f"[风控] 参数更新: {key} = {value}")
    
    def get_params(self):
        """获取风控参数"""
        return {
            'max_single_amount': self.max_single_amount,
            'max_single_amount_hk': self.max_single_amount_hk,
            'max_daily_trades': self.max_daily_trades,
            'max_position_ratio': self.max_position_ratio,
            'max_total_position': self.max_total_position,
            'stop_loss_ratio': self.stop_loss_ratio,
            'take_profit_ratio': self.take_profit_ratio
        }


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*70)
    print("风控管理器测试")
    print("="*70)
    
    # 创建风控管理器
    risk_mgr = RiskManager()
    
    # 模拟账户信息
    account = {
        'total_assets': 100000,
        'cash': 50000,
        'avl_withdrawal_cash': 50000
    }
    
    # 模拟持仓
    positions = [
        {
            'code': 'TSLA',
            'qty': 100,
            'cost_price': 420,
            'market_val': 44000,
            'can_sell_qty': 100
        }
    ]
    
    # 测试1: 正常买入订单
    print("\n" + "="*70)
    print("测试1: 正常买入订单")
    print("="*70)
    
    order1 = {
        'stock_code': 'NVDA',
        'direction': 'BUY',
        'price': 500,
        'qty': 50
    }
    
    is_pass, reason = risk_mgr.check_order(order1, account, positions)
    print(f"\n结果: {'✅ 通过' if is_pass else '❌ 拒绝'}")
    print(f"原因: {reason}")
    
    if is_pass:
        risk_mgr.update_daily_stats(order1)
    
    # 测试2: 超过单笔金额限制
    print("\n" + "="*70)
    print("测试2: 超过单笔金额限制")
    print("="*70)
    
    order2 = {
        'stock_code': 'TSLA',
        'direction': 'BUY',
        'price': 1000,
        'qty': 100
    }
    
    is_pass, reason = risk_mgr.check_order(order2, account, positions)
    print(f"\n结果: {'✅ 通过' if is_pass else '❌ 拒绝'}")
    print(f"原因: {reason}")
    
    # 测试3: 卖出持仓
    print("\n" + "="*70)
    print("测试3: 卖出持仓")
    print("="*70)
    
    order3 = {
        'stock_code': 'TSLA',
        'direction': 'SELL',
        'price': 440,
        'qty': 50
    }
    
    is_pass, reason = risk_mgr.check_order(order3, account, positions)
    print(f"\n结果: {'✅ 通过' if is_pass else '❌ 拒绝'}")
    print(f"原因: {reason}")
    
    # 显示统计
    print("\n" + "="*70)
    print("今日统计")
    print("="*70)
    stats = risk_mgr.get_daily_stats()
    print(f"交易次数: {stats['trades']}")
    print(f"买入金额: ${stats['buy_amount']:,.2f}")
    print(f"卖出金额: ${stats['sell_amount']:,.2f}")
    
    print("\n✅ 测试完成\n")
