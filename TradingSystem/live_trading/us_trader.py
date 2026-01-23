#!/usr/bin/env python3
# us_trader.py
"""
美股实盘/模拟交易引擎
支持Tesla (TSLA) 等美股交易

特点:
1. 支持美股交易
2. 自动获取账户ID
3. 支持实盘和模拟盘切换
4. 完整的错误处理
"""

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ 已加载 .env 文件")
except ImportError:
    print("⚠️ 未安装 python-dotenv")
except Exception as e:
    print(f"⚠️ 加载 .env 文件失败: {e}")

import os
import sys
from futu import *


class USTrader:
    """美股交易引擎"""
    
    def __init__(self, host='127.0.0.1', port=11111, use_simulate=True, trading_pwd=None):
        """
        初始化交易引擎
        
        Parameters:
        -----------
        host : str
            Futu OpenD 主机地址
        port : int
            Futu OpenD 端口
        use_simulate : bool
            是否使用模拟盘（True=模拟，False=真实）
        trading_pwd : str
            交易密码（可选）
        """
        self.host = host
        self.port = port
        self.quote_ctx = None
        self.trade_ctx = None
        self.trading_pwd = trading_pwd or os.environ.get("FUTU_TRADING_PWD")
        
        # 交易环境
        self.use_simulate = use_simulate
        self.trd_env = TrdEnv.SIMULATE if use_simulate else TrdEnv.REAL
        
        # 账户ID（将在连接时自动获取）
        self.acc_id = None
        self.acc_list = None
        
    def connect(self):
        """连接Futu OpenD"""
        print(f"\n{'='*70}")
        print(f"{'连接Futu美股交易系统':^70}")
        print(f"{'='*70}\n")
        
        env_name = "模拟盘" if self.use_simulate else "真实盘"
        print(f"交易环境: {env_name}")
        
        try:
            # 1. 行情连接
            print(f"\n正在连接行情服务器...")
            self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)
            print(f"✅ 行情连接成功")
            
            # 2. 美股交易连接
            print(f"正在连接美股交易服务器...")
            self.trade_ctx = OpenUSTradeContext(host=self.host, port=self.port)
            print(f"✅ 美股交易连接成功")
            
            # 3. 获取账户列表
            print(f"\n正在获取交易账户...")
            ret, data = self.trade_ctx.get_acc_list()
            
            if ret == RET_OK:
                self.acc_list = data
                
                if len(data) > 0:
                    print(f"✅ 找到 {len(data)} 个交易账户:\n")
                    
                    # 显示所有账户
                    for idx, row in data.iterrows():
                        env = "模拟盘" if row['trd_env'] == TrdEnv.SIMULATE else "真实盘"
                        print(f"  [{idx+1}] {row['acc_id']} ({env})")
                    
                    # 根据设置的环境选择账户
                    target_accounts = data[data['trd_env'] == self.trd_env]
                    
                    if len(target_accounts) > 0:
                        self.acc_id = target_accounts.iloc[0]['acc_id']
                        print(f"\n✅ 已选择账户: {self.acc_id} ({env_name})")
                    else:
                        print(f"\n❌ 没有找到{env_name}账户")
                        print(f"   可用账户:")
                        for idx, row in data.iterrows():
                            env = "模拟盘" if row['trd_env'] == TrdEnv.SIMULATE else "真实盘"
                            print(f"     {row['acc_id']} ({env})")
                        return False
                else:
                    print(f"❌ 未找到任何交易账户")
                    print(f"   请检查:")
                    print(f"   1. Futu OpenD 是否已启动")
                    print(f"   2. 是否已登录账户")
                    print(f"   3. 是否有美股交易权限")
                    return False
            else:
                print(f"❌ 获取账户列表失败: {data}")
                return False
            
            # 4. 解锁交易（如果设置了密码）
            if self.trading_pwd:
                print(f"\n正在解锁交易...")
                ret, data = self.trade_ctx.unlock_trade(self.trading_pwd)
                if ret == RET_OK:
                    print(f"✅ 交易解锁成功")
                else:
                    print(f"❌ 交易解锁失败: {data}")
                    print(f"   提示: 请检查交易密码是否正确")
                    return False
            else:
                print(f"\n⚠️  未设置交易密码")
                print(f"   提示: 可通过参数或环境变量 FUTU_TRADING_PWD 设置")
            
            print(f"\n{'='*70}")
            print(f"✅ 连接完成")
            print(f"{'='*70}\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 连接失败: {e}")
            print(f"\n可能的原因:")
            print(f"1. Futu OpenD 未启动")
            print(f"2. 端口号不正确（默认11111）")
            print(f"3. 网络连接问题")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.quote_ctx:
            self.quote_ctx.close()
            print("✅ 行情连接已关闭")
        if self.trade_ctx:
            self.trade_ctx.close()
            print("✅ 交易连接已关闭")
    
    def get_account_info(self):
        """获取账户信息"""
        if not self.acc_id:
            print("❌ 账户ID未设置，请先调用 connect()")
            return None
        
        try:
            ret, data = self.trade_ctx.accinfo_query(
                trd_env=self.trd_env,
                acc_id=self.acc_id
            )
            
            if ret == RET_OK:
                print(f"\n{'='*70}")
                print(f"{'账户信息':^70}")
                print(f"{'='*70}")
                if len(data) > 0:
                    row = data.iloc[0]
                    print(f"账户ID:       {self.acc_id}")
                    print(f"币种:         {row.get('currency', 'USD')}")
                    print(f"总资产:       ${row.get('total_assets', 0):,.2f}")
                    print(f"现金:         ${row.get('cash', 0):,.2f}")
                    print(f"证券市值:     ${row.get('market_val', 0):,.2f}")
                    print(f"可用资金:     ${row.get('avl_withdrawal_cash', 0):,.2f}")
                    print(f"购买力:       ${row.get('power', 0):,.2f}")
                    print(f"最大购买力:   ${row.get('max_power_short', 0):,.2f}")
                print(f"{'='*70}\n")
                return data
            else:
                print(f"❌ 获取账户信息失败: {data}")
                return None
                
        except Exception as e:
            print(f"❌ 获取账户信息异常: {e}")
            return None
    
    def get_positions(self):
        """获取持仓"""
        if not self.acc_id:
            print("❌ 账户ID未设置，请先调用 connect()")
            return None
        
        try:
            ret, data = self.trade_ctx.position_list_query(
                trd_env=self.trd_env,
                acc_id=self.acc_id
            )
            
            if ret == RET_OK:
                if len(data) > 0:
                    print(f"\n{'='*70}")
                    print(f"{'当前持仓':^70}")
                    print(f"{'='*70}")
                    print(data[['code', 'stock_name', 'qty', 'cost_price', 
                               'market_val', 'pl_val', 'pl_ratio']])
                    print(f"{'='*70}\n")
                else:
                    print(f"\n✅ 账户正常，当前无持仓\n")
                return data
            else:
                print(f"❌ 获取持仓失败: {data}")
                return None
                
        except Exception as e:
            print(f"❌ 获取持仓异常: {e}")
            return None
    
    def get_orders(self, status_filter_list=None):
        """
        获取订单列表
        
        Parameters:
        -----------
        status_filter_list : list
            订单状态过滤，例如：
            [OrderStatus.SUBMITTED, OrderStatus.FILLED_ALL]
            None 表示查询所有状态
        """
        if not self.acc_id:
            print("❌ 账户ID未设置，请先调用 connect()")
            return None
        
        try:
            ret, data = self.trade_ctx.order_list_query(
                trd_env=self.trd_env,
                acc_id=self.acc_id,
                status_filter_list=status_filter_list
            )
            
            if ret == RET_OK:
                if len(data) > 0:
                    print(f"\n{'='*70}")
                    print(f"{'订单列表':^70}")
                    print(f"{'='*70}")
                    print(data[['code', 'trd_side', 'order_status', 'qty', 
                               'price', 'dealt_qty', 'dealt_avg_price']])
                    print(f"{'='*70}\n")
                else:
                    print(f"\n✅ 无订单记录\n")
                return data
            else:
                print(f"❌ 获取订单失败: {data}")
                return None
                
        except Exception as e:
            print(f"❌ 获取订单异常: {e}")
            return None
    
    def buy(self, stock_code, price, qty, order_type=OrderType.NORMAL):
        """
        买入股票
        
        Parameters:
        -----------
        stock_code : str
            股票代码，例如 'US.TSLA'
        price : float
            价格（限价单时有效）
        qty : int
            数量（美股1股起，无整数倍限制）
        order_type : OrderType
            订单类型：
            - OrderType.NORMAL: 限价单（默认）
            - OrderType.MARKET: 市价单
        
        Returns:
        --------
        DataFrame or None
        """
        if not self.acc_id:
            print("❌ 账户ID未设置，请先调用 connect()")
            return None
        
        # 美股检查：至少1股
        if qty < 1:
            print(f"❌ 买入数量必须>=1股")
            return None
        
        try:
            ret, data = self.trade_ctx.place_order(
                price=price,
                qty=qty,
                code=stock_code,
                trd_side=TrdSide.BUY,
                order_type=order_type,
                trd_env=self.trd_env,
                acc_id=self.acc_id
            )
            
            if ret == RET_OK:
                print(f"\n✅ 买入订单提交成功:")
                print(f"   股票:   {stock_code}")
                print(f"   类型:   {'市价单' if order_type == OrderType.MARKET else '限价单'}")
                if order_type == OrderType.NORMAL:
                    print(f"   价格:   ${price:.2f}")
                print(f"   数量:   {qty} 股")
                print(f"   订单号: {data['order_id'].iloc[0]}")
                print()
                return data
            else:
                print(f"\n❌ 买入失败: {data}")
                print(f"\n可能的原因:")
                print(f"1. 资金不足")
                print(f"2. 价格超出涨跌幅限制")
                print(f"3. 股票代码错误")
                print(f"4. 交易时间限制")
                print()
                return None
                
        except Exception as e:
            print(f"\n❌ 买入异常: {e}\n")
            return None
    
    def sell(self, stock_code, price, qty, order_type=OrderType.NORMAL):
        """
        卖出股票
        
        Parameters同buy()
        """
        if not self.acc_id:
            print("❌ 账户ID未设置，请先调用 connect()")
            return None
        
        # 美股检查：至少1股
        if qty < 1:
            print(f"❌ 卖出数量必须>=1股")
            return None
        
        try:
            ret, data = self.trade_ctx.place_order(
                price=price,
                qty=qty,
                code=stock_code,
                trd_side=TrdSide.SELL,
                order_type=order_type,
                trd_env=self.trd_env,
                acc_id=self.acc_id
            )
            
            if ret == RET_OK:
                print(f"\n✅ 卖出订单提交成功:")
                print(f"   股票:   {stock_code}")
                print(f"   类型:   {'市价单' if order_type == OrderType.MARKET else '限价单'}")
                if order_type == OrderType.NORMAL:
                    print(f"   价格:   ${price:.2f}")
                print(f"   数量:   {qty} 股")
                print(f"   订单号: {data['order_id'].iloc[0]}")
                print()
                return data
            else:
                print(f"\n❌ 卖出失败: {data}")
                print(f"\n可能的原因:")
                print(f"1. 持仓不足")
                print(f"2. 价格超出涨跌幅限制")
                print(f"3. 股票代码错误")
                print(f"4. 交易时间限制")
                print()
                return None
                
        except Exception as e:
            print(f"\n❌ 卖出异常: {e}\n")
            return None
    
    def get_current_price(self, stock_code):
        """获取当前价格"""
        try:
            ret, data = self.quote_ctx.get_market_snapshot([stock_code])
            
            if ret == RET_OK:
                return data.iloc[0]['last_price']
            else:
                print(f"❌ 获取价格失败: {data}")
                return None
                
        except Exception as e:
            print(f"❌ 获取价格异常: {e}")
            return None
    
    def get_market_snapshot(self, stock_code):
        """获取详细行情快照"""
        try:
            ret, data = self.quote_ctx.get_market_snapshot([stock_code])
            
            if ret == RET_OK:
                snapshot = data.iloc[0]
                print(f"\n{'='*70}")
                print(f"{stock_code} 行情快照")
                print(f"{'='*70}")
                print(f"最新价:   ${snapshot['last_price']:.2f}")
                print(f"开盘价:   ${snapshot['open_price']:.2f}")
                print(f"最高价:   ${snapshot['high_price']:.2f}")
                print(f"最低价:   ${snapshot['low_price']:.2f}")
                print(f"昨收价:   ${snapshot['prev_close_price']:.2f}")
                print(f"成交量:   {snapshot['volume']:,.0f}")
                print(f"成交额:   ${snapshot['turnover']:,.2f}")
                print(f"涨跌额:   ${snapshot['change_val']:.2f}")
                print(f"涨跌幅:   {snapshot['change_rate']:.2f}%")
                print(f"{'='*70}\n")
                return snapshot
            else:
                print(f"❌ 获取行情快照失败: {data}")
                return None
                
        except Exception as e:
            print(f"❌ 获取行情快照异常: {e}")
            return None
    
    def cancel_order(self, order_id):
        """
        撤销订单
        
        Parameters:
        -----------
        order_id : str or int
            订单ID
        """
        if not self.acc_id:
            print("❌ 账户ID未设置，请先调用 connect()")
            return None
        
        try:
            ret, data = self.trade_ctx.modify_order(
                modify_order_op=ModifyOrderOp.CANCEL,
                order_id=order_id,
                qty=0,
                price=0,
                trd_env=self.trd_env,
                acc_id=self.acc_id
            )
            
            if ret == RET_OK:
                print(f"\n✅ 订单撤销成功: {order_id}\n")
                return data
            else:
                print(f"\n❌ 订单撤销失败: {data}\n")
                return None
                
        except Exception as e:
            print(f"\n❌ 订单撤销异常: {e}\n")
            return None


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*70)
    print("Futu 美股交易测试")
    print("="*70)
    
    # 创建交易器（模拟盘）
    trader = USTrader(
        host='127.0.0.1',
        port=11111,
        use_simulate=True,  # True=模拟盘，False=真实盘
        trading_pwd=None    # 交易密码（可选）
    )
    
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
    
    # 获取Tesla行情
    trader.get_market_snapshot('US.TSLA')
    
    # 测试下单（注释掉，避免误操作）
    print("\n" + "="*70)
    print("提示: 如需测试下单，请取消以下代码的注释")
    print("="*70)
    print("\n示例：买入1股Tesla")
    print("  current_price = trader.get_current_price('US.TSLA')")
    print("  trader.buy('US.TSLA', current_price, 1)")
    print()
    print("示例：市价买入10股Tesla")
    print("  trader.buy('US.TSLA', 0, 10, order_type=OrderType.MARKET)")
    print()
    
    # 取消注释以测试
    # current_price = trader.get_current_price('US.TSLA')
    # if current_price:
    #     trader.buy('US.TSLA', current_price, 1)
    
    # 断开连接
    trader.disconnect()
    
    print("\n✅ 测试完成\n")