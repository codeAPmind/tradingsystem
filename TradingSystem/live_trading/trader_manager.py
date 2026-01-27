#!/usr/bin/env python3
"""
统一交易管理器
自动识别市场，调用对应交易引擎
"""
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from live_trading.hk_trader import HKTrader
from live_trading.us_trader import USTrader


class TraderManager:
    """统一交易管理器"""
    
    def __init__(self, host='127.0.0.1', port=11111, use_simulate=True):
        """
        初始化交易管理器
        
        Parameters:
        -----------
        host : str
            Futu OpenD 主机地址
        port : int
            Futu OpenD 端口
        use_simulate : bool
            是否使用模拟盘（True=模拟，False=真实）
        """
        self.host = host
        self.port = port
        self.use_simulate = use_simulate
        
        # 初始化交易引擎（延迟初始化）
        self.hk_trader = None
        self.us_trader = None
        
        # 连接状态
        self.hk_connected = False
        self.us_connected = False
        
        print(f"\n{'='*70}")
        print(f"{'统一交易管理器初始化':^70}")
        print(f"{'='*70}")
        print(f"交易环境: {'模拟盘' if use_simulate else '真实盘'}")
        print(f"Futu地址: {host}:{port}")
        print(f"{'='*70}\n")
    
    def connect_hk(self):
        """连接港股交易器"""
        print("\n[TraderManager] 正在连接港股交易器...")
        
        if not self.hk_trader:
            self.hk_trader = HKTrader(
                host=self.host,
                port=self.port,
                use_simulate=self.use_simulate
            )
        
        self.hk_connected = self.hk_trader.connect()
        
        if self.hk_connected:
            print("[TraderManager] ✅ 港股交易器连接成功")
        else:
            print("[TraderManager] ❌ 港股交易器连接失败")
        
        return self.hk_connected
    
    def connect_us(self):
        """连接美股交易器"""
        print("\n[TraderManager] 正在连接美股交易器...")
        
        if not self.us_trader:
            self.us_trader = USTrader(
                host=self.host,
                port=self.port,
                use_simulate=self.use_simulate
            )
        
        self.us_connected = self.us_trader.connect()
        
        if self.us_connected:
            print("[TraderManager] ✅ 美股交易器连接成功")
        else:
            print("[TraderManager] ❌ 美股交易器连接失败")
        
        return self.us_connected
    
    def connect_all(self):
        """连接所有交易器"""
        hk_success = self.connect_hk()
        us_success = self.connect_us()
        
        if hk_success or us_success:
            print(f"\n[TraderManager] ✅ 至少一个市场连接成功")
            return True
        else:
            print(f"\n[TraderManager] ❌ 所有市场连接失败")
            return False
    
    def get_trader(self, stock_code):
        """
        根据股票代码获取对应交易器
        
        Parameters:
        -----------
        stock_code : str
            股票代码（如 'TSLA' 或 'HK.01797'）
        
        Returns:
        --------
        HKTrader or USTrader or None
        """
        if stock_code.startswith('HK.'):
            # 港股
            if not self.hk_connected:
                print(f"[TraderManager] 港股交易器未连接，尝试连接...")
                self.connect_hk()
            
            return self.hk_trader if self.hk_connected else None
        else:
            # 美股
            if not self.us_connected:
                print(f"[TraderManager] 美股交易器未连接，尝试连接...")
                self.connect_us()
            
            return self.us_trader if self.us_connected else None
    
    def buy(self, stock_code, price, qty, order_type=None):
        """
        统一买入接口
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        price : float
            价格（市价单时可以为0）
        qty : int
            数量
        order_type : OrderType
            订单类型（None表示使用默认）
        
        Returns:
        --------
        DataFrame or None
        """
        trader = self.get_trader(stock_code)
        if trader:
            return trader.buy(stock_code, price, qty, order_type)
        else:
            print(f"[TraderManager] ❌ 无法获取交易器: {stock_code}")
            return None
    
    def sell(self, stock_code, price, qty, order_type=None):
        """
        统一卖出接口
        
        Parameters同buy()
        """
        trader = self.get_trader(stock_code)
        if trader:
            return trader.sell(stock_code, price, qty, order_type)
        else:
            print(f"[TraderManager] ❌ 无法获取交易器: {stock_code}")
            return None
    
    def get_account_info(self, market='HK'):
        """
        获取账户信息
        
        Parameters:
        -----------
        market : str
            'HK' 或 'US'
        """
        if market == 'HK' and self.hk_trader and self.hk_connected:
            return self.hk_trader.get_account_info()
        elif market == 'US' and self.us_trader and self.us_connected:
            return self.us_trader.get_account_info()
        else:
            print(f"[TraderManager] ❌ {market}市场未连接或交易器不存在")
            return None
    
    def get_all_positions(self):
        """
        获取所有市场的持仓
        
        Returns:
        --------
        list : 持仓列表
        """
        positions = []
        
        # 获取港股持仓
        if self.hk_trader and self.hk_connected:
            try:
                hk_pos = self.hk_trader.get_positions()
                if hk_pos is not None and len(hk_pos) > 0:
                    positions.extend(hk_pos.to_dict('records'))
                    print(f"[TraderManager] 港股持仓: {len(hk_pos)} 只")
            except Exception as e:
                print(f"[TraderManager] 获取港股持仓失败: {e}")
        
        # 获取美股持仓
        if self.us_trader and self.us_connected:
            try:
                us_pos = self.us_trader.get_positions()
                if us_pos is not None and len(us_pos) > 0:
                    positions.extend(us_pos.to_dict('records'))
                    print(f"[TraderManager] 美股持仓: {len(us_pos)} 只")
            except Exception as e:
                print(f"[TraderManager] 获取美股持仓失败: {e}")
        
        print(f"[TraderManager] 总持仓: {len(positions)} 只")
        return positions
    
    def get_all_orders(self):
        """获取所有市场的订单"""
        orders = []
        
        # 获取港股订单
        if self.hk_trader and self.hk_connected:
            try:
                hk_orders = self.hk_trader.get_orders()
                if hk_orders is not None and len(hk_orders) > 0:
                    orders.extend(hk_orders.to_dict('records'))
            except Exception as e:
                print(f"[TraderManager] 获取港股订单失败: {e}")
        
        # 获取美股订单
        if self.us_trader and self.us_connected:
            try:
                us_orders = self.us_trader.get_orders()
                if us_orders is not None and len(us_orders) > 0:
                    orders.extend(us_orders.to_dict('records'))
            except Exception as e:
                print(f"[TraderManager] 获取美股订单失败: {e}")
        
        return orders
    
    def get_current_price(self, stock_code):
        """获取当前价格"""
        trader = self.get_trader(stock_code)
        if trader:
            return trader.get_current_price(stock_code)
        return None
    
    def get_market_snapshot(self, stock_code):
        """获取市场快照"""
        trader = self.get_trader(stock_code)
        if trader:
            return trader.get_market_snapshot(stock_code)
        return None
    
    def cancel_order(self, stock_code, order_id):
        """撤单"""
        trader = self.get_trader(stock_code)
        if trader:
            return trader.cancel_order(order_id)
        return None
    
    def disconnect(self):
        """断开所有连接"""
        print(f"\n[TraderManager] 正在断开所有连接...")
        
        if self.hk_trader:
            self.hk_trader.disconnect()
            self.hk_connected = False
        
        if self.us_trader:
            self.us_trader.disconnect()
            self.us_connected = False
        
        print(f"[TraderManager] ✅ 所有连接已断开")
    
    def get_status(self):
        """获取连接状态"""
        status = {
            'hk_connected': self.hk_connected,
            'us_connected': self.us_connected,
            'hk_acc_id': self.hk_trader.acc_id if self.hk_trader else None,
            'us_acc_id': self.us_trader.acc_id if self.us_trader else None,
        }
        return status


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*70)
    print("统一交易管理器测试")
    print("="*70)
    
    # 创建管理器（模拟盘）
    manager = TraderManager(use_simulate=True)
    
    # 连接所有市场
    if manager.connect_all():
        # 查看状态
        status = manager.get_status()
        print(f"\n连接状态:")
        print(f"  港股: {'已连接' if status['hk_connected'] else '未连接'}")
        print(f"  美股: {'已连接' if status['us_connected'] else '未连接'}")
        
        # 获取所有持仓
        positions = manager.get_all_positions()
        
        # 获取港股账户信息
        if status['hk_connected']:
            manager.get_account_info('HK')
        
        # 获取美股账户信息
        if status['us_connected']:
            manager.get_account_info('US')
    
    # 断开连接
    manager.disconnect()
    
    print("\n✅ 测试完成\n")
