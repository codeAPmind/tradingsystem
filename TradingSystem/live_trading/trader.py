# live_trading/trader.py
"""
实盘交易引擎 - 修复版

修复内容：
1. 添加 acc_id 参数（必须）
2. 正确处理账户ID
3. 添加详细的错误提示
4. 支持自动获取账户列表
"""
from futu import *
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import *


class LiveTrader:
    """实盘交易引擎"""
    
    def __init__(self, host=FUTU_HOST, port=FUTU_PORT):
        self.host = host
        self.port = port
        self.quote_ctx = None
        self.trade_ctx = None
        self.pwd_unlock = TRADING_PWD
        
        # 交易环境
        self.trd_env = TrdEnv.SIMULATE if TRADING_ENV == 'SIMULATE' else TrdEnv.REAL
        
        # 账户ID（非常重要！）
        self.acc_id = None  # 将在连接时获取
        
    def connect(self):
        """连接富途"""
        print(f"\n{'='*60}")
        print(f"{'连接Futu交易系统':^60}")
        print(f"{'='*60}\n")
        
        # 1. 行情连接
        self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)
        print(f"✅ 行情连接成功")
        
        # 2. 交易连接（港股）
        self.trade_ctx = OpenHKTradeContext(host=self.host, port=self.port)
        print(f"✅ 交易连接成功")
        
        # 3. 获取账户列表（关键步骤！）
        print(f"\n正在获取交易账户...")
        ret, data = self.trade_ctx.get_acc_list()
        
        if ret == RET_OK:
            if len(data) > 0:
                print(f"✅ 找到 {len(data)} 个交易账户:\n")
                
                # 显示所有账户
                for idx, row in data.iterrows():
                    env_name = "模拟盘" if row['trd_env'] == TrdEnv.SIMULATE else "真实盘"
                    print(f"  [{idx+1}] {row['acc_id']} ({env_name})")
                
                # 根据设置的环境选择账户
                target_accounts = data[data['trd_env'] == self.trd_env]
                
                if len(target_accounts) > 0:
                    self.acc_id = target_accounts.iloc[0]['acc_id']
                    env_name = "模拟盘" if self.trd_env == TrdEnv.SIMULATE else "真实盘"
                    print(f"\n✅ 已选择账户: {self.acc_id} ({env_name})")
                else:
                    env_name = "模拟盘" if self.trd_env == TrdEnv.SIMULATE else "真实盘"
                    print(f"\n❌ 没有找到{env_name}账户")
                    print(f"   请检查 config/settings.py 中的 TRADING_ENV 设置")
                    return False
            else:
                print(f"❌ 未找到任何交易账户")
                print(f"   请检查:")
                print(f"   1. Futu OpenD 是否已登录")
                print(f"   2. 是否有交易权限")
                return False
        else:
            print(f"❌ 获取账户列表失败: {data}")
            return False
        
        # 4. 解锁交易
        if self.pwd_unlock != '你的交易密码':
            print(f"\n正在解锁交易...")
            ret, data = self.trade_ctx.unlock_trade(self.pwd_unlock)
            if ret == RET_OK:
                print(f"✅ 交易解锁成功")
            else:
                print(f"❌ 交易解锁失败: {data}")
                print(f"   提示: 请检查 config/settings.py 中的交易密码")
                return False
        else:
            print(f"\n⚠️  警告: 交易密码未设置")
            print(f"   请在 config/settings.py 中设置 TRADING_PWD")
        
        print(f"\n{'='*60}")
        print(f"✅ 连接完成")
        print(f"{'='*60}\n")
        
        return True
    
    def disconnect(self):
        """断开连接"""
        if self.quote_ctx:
            self.quote_ctx.close()
        if self.trade_ctx:
            self.trade_ctx.close()
        print("✅ 已断开连接")
    
    def get_account_info(self):
        """获取账户信息"""
        if not self.acc_id:
            print("❌ 账户ID未设置，请先调用 connect()")
            return None
        
        ret, data = self.trade_ctx.accinfo_query(
            trd_env=self.trd_env,
            acc_id=self.acc_id,  # ← 关键！必须指定
            acc_index=0
        )
        
        if ret == RET_OK:
            print(f"\n{'='*60}")
            print(f"{'账户信息':^60}")
            print(f"{'='*60}")
            if len(data) > 0:
                print(f"账户ID:   {self.acc_id}")
                print(f"总资产:   {data['total_assets'][0]:,.2f}")
                print(f"现金:     {data['cash'][0]:,.2f}")
                print(f"市值:     {data['market_val'][0]:,.2f}")
                print(f"证券市值: {data.get('security_market_val', [0])[0]:,.2f}")
                print(f"可用资金: {data.get('avl_withdrawal_cash', [0])[0]:,.2f}")
            print(f"{'='*60}\n")
            return data
        else:
            print(f"❌ 获取账户信息失败: {data}")
            return None
    
    def get_positions(self):
        """获取持仓"""
        if not self.acc_id:
            print("❌ 账户ID未设置，请先调用 connect()")
            return None
        
        ret, data = self.trade_ctx.position_list_query(
            trd_env=self.trd_env,
            acc_id=self.acc_id,  # ← 关键！必须指定
            acc_index=0
        )
        
        if ret == RET_OK:
            if len(data) > 0:
                print(f"\n{'='*60}")
                print(f"{'当前持仓':^60}")
                print(f"{'='*60}")
                print(data[['code', 'stock_name', 'qty', 'cost_price', 'pl_val', 'pl_ratio']])
                print(f"{'='*60}\n")
            else:
                print(f"\n✅ 账户正常，当前无持仓\n")
            return data
        else:
            print(f"❌ 获取持仓失败: {data}")
            return None
    
    def get_orders(self, status_filter_list=None):
        """
        获取今日订单
        
        Parameters:
        -----------
        status_filter_list : list
            订单状态过滤，例如：
            [OrderStatus.SUBMITTED, OrderStatus.FILLED_ALL]
        """
        if not self.acc_id:
            print("❌ 账户ID未设置，请先调用 connect()")
            return None
        
        ret, data = self.trade_ctx.order_list_query(
            trd_env=self.trd_env,
            acc_id=self.acc_id,  # ← 关键！必须指定
            acc_index=0,
            status_filter_list=status_filter_list
        )
        
        if ret == RET_OK:
            if len(data) > 0:
                print(f"\n{'='*60}")
                print(f"{'今日订单':^60}")
                print(f"{'='*60}")
                print(data[['code', 'order_type', 'order_status', 'qty', 'price', 'dealt_qty', 'dealt_avg_price']])
                print(f"{'='*60}\n")
            else:
                print(f"\n今日无订单\n")
            return data
        else:
            print(f"❌ 获取订单失败: {data}")
            return None
    
    def buy(self, stock_code, price, qty, order_type=OrderType.NORMAL):
        """
        买入股票
        
        Parameters:
        -----------
        stock_code : str
            股票代码，例如 'HK.01797'
        price : float
            价格（限价单时有效）
        qty : int
            数量（港股至少100股，且必须是100的整数倍）
        order_type : OrderType
            订单类型：
            - OrderType.NORMAL: 限价单（默认）
            - OrderType.MARKET: 市价单
        """
        if not self.acc_id:
            print("❌ 账户ID未设置，请先调用 connect()")
            return None
        
        # 检查数量
        if qty < 100 or qty % 100 != 0:
            print(f"❌ 港股买入数量必须>=100且是100的整数倍")
            return None
        
        ret, data = self.trade_ctx.place_order(
            price=price,
            qty=qty,
            code=stock_code,
            trd_side=TrdSide.BUY,
            order_type=order_type,
            trd_env=self.trd_env,
            acc_id=self.acc_id,  # ← 关键！必须指定
            acc_index=0
        )
        
        if ret == RET_OK:
            print(f"\n✅ 买入订单提交成功:")
            print(f"   股票:   {stock_code}")
            print(f"   价格:   {price:.3f}")
            print(f"   数量:   {qty}")
            print(f"   订单号: {data['order_id'][0]}")
            print()
            return data
        else:
            print(f"\n❌ 买入失败: {data}\n")
            return None
    
    def sell(self, stock_code, price, qty, order_type=OrderType.NORMAL):
        """
        卖出股票
        
        Parameters同buy()
        """
        if not self.acc_id:
            print("❌ 账户ID未设置，请先调用 connect()")
            return None
        
        # 检查数量
        if qty < 100 or qty % 100 != 0:
            print(f"❌ 港股卖出数量必须>=100且是100的整数倍")
            return None
        
        ret, data = self.trade_ctx.place_order(
            price=price,
            qty=qty,
            code=stock_code,
            trd_side=TrdSide.SELL,
            order_type=order_type,
            trd_env=self.trd_env,
            acc_id=self.acc_id,  # ← 关键！必须指定
            acc_index=0
        )
        
        if ret == RET_OK:
            print(f"\n✅ 卖出订单提交成功:")
            print(f"   股票:   {stock_code}")
            print(f"   价格:   {price:.3f}")
            print(f"   数量:   {qty}")
            print(f"   订单号: {data['order_id'][0]}")
            print()
            return data
        else:
            print(f"\n❌ 卖出失败: {data}\n")
            return None
    
    def get_current_price(self, stock_code):
        """获取当前价格"""
        ret, data = self.quote_ctx.get_market_snapshot([stock_code])
        
        if ret == RET_OK:
            return data.iloc[0]['last_price']
        else:
            print(f"❌ 获取价格失败: {data}")
            return None
    
    def get_market_snapshot(self, stock_code):
        """获取详细行情快照"""
        ret, data = self.quote_ctx.get_market_snapshot([stock_code])
        
        if ret == RET_OK:
            snapshot = data.iloc[0]
            print(f"\n{'='*60}")
            print(f"{stock_code} 行情快照")
            print(f"{'='*60}")
            print(f"最新价:   {snapshot['last_price']:.3f}")
            print(f"开盘价:   {snapshot['open_price']:.3f}")
            print(f"最高价:   {snapshot['high_price']:.3f}")
            print(f"最低价:   {snapshot['low_price']:.3f}")
            print(f"昨收价:   {snapshot['prev_close_price']:.3f}")
            print(f"成交量:   {snapshot['volume']:,.0f}")
            print(f"成交额:   {snapshot['turnover']:,.2f}")
            print(f"涨跌幅:   {snapshot['change_rate']:.2f}%")
            print(f"{'='*60}\n")
            return snapshot
        else:
            print(f"❌ 获取行情快照失败: {data}")
            return None


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*70)
    print("Futu 实盘交易测试")
    print("="*70)
    
    trader = LiveTrader()
    
    # 连接
    if not trader.connect():
        print("\n❌ 连接失败，退出")
        sys.exit(1)
    
    # 查看账户信息
    trader.get_account_info()
    
    # 查看持仓
    trader.get_positions()
    
    # 查看订单
    trader.get_orders()
    
    # 获取行情
    trader.get_market_snapshot('HK.01797')
    
    # 测试下单（注释掉，避免误操作）
    print("\n提示: 如需测试下单，请取消以下代码的注释")
    print("建议在模拟盘测试:")
    print("  trader.buy('HK.01797', 22.50, 100)")
    print()
    
    # trader.buy('HK.01797', 22.50, 100)  # 取消注释以测试
    
    trader.disconnect()