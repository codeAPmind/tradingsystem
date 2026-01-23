#!/usr/bin/env python3
# auto_trade_01797.py
"""
东方甄选(HK.01797)自动交易脚本
基于已有的回测策略和信号

功能:
1. 使用现有的回测策略（TSF-LSMA）
2. 自动生成交易信号
3. 根据信号自动下单
4. 港股交易规则（100股起，整手交易）
"""

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ 已加载 .env 文件")
except:
    pass

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from futu import OrderType

# 导入交易器
from hk_trader import HKTrader


def calculate_tsf(data, period=9):
    """计算TSF指标"""
    if len(data) < period:
        return None
    
    recent_data = data[-period:]
    x = np.arange(len(recent_data))
    coeffs = np.polyfit(x, recent_data, 1)
    a, b = coeffs[0], coeffs[1]
    tsf_value = a * period + b
    
    return tsf_value


def calculate_lsma(data, period=20):
    """计算LSMA指标"""
    if len(data) < period:
        return None
    
    recent_data = data[-period:]
    x = np.arange(len(recent_data))
    coeffs = np.polyfit(x, recent_data, 1)
    a, b = coeffs[0], coeffs[1]
    lsma_value = a * (period - 1) + b
    
    return lsma_value


def get_stock_data(trader, stock_code='HK.01797', days=60):
    """
    获取股票历史数据
    
    Parameters:
    -----------
    trader : HKTrader
        交易器实例
    stock_code : str
        股票代码
    days : int
        获取天数
    
    Returns:
    --------
    DataFrame
    """
    from futu import KLType, SubType
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    try:
        # 订阅K线
        ret_sub, err_msg = trader.quote_ctx.subscribe([stock_code], [SubType.K_DAY])
        
        if ret_sub != RET_OK:
            print(f"❌ 订阅失败: {err_msg}")
            return None
        
        # 获取K线数据
        ret, data, page_req_key = trader.quote_ctx.request_history_kline(
            stock_code,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            ktype=KLType.K_DAY,
            max_count=days
        )
        
        if ret == RET_OK:
            # 取消订阅
            trader.quote_ctx.unsubscribe([stock_code], [SubType.K_DAY])
            
            return data
        else:
            print(f"❌ 获取K线失败: {data}")
            return None
            
    except Exception as e:
        print(f"❌ 获取数据异常: {e}")
        return None


def generate_signal(trader, stock_code='HK.01797', 
                    tsf_period=9, lsma_period=20,
                    buy_threshold=1.0, sell_threshold=1.0):
    """
    生成交易信号
    
    Parameters:
    -----------
    trader : HKTrader
        交易器实例
    stock_code : str
        股票代码
    tsf_period : int
        TSF周期
    lsma_period : int
        LSMA周期
    buy_threshold : float
        买入阈值
    sell_threshold : float
        卖出阈值
    
    Returns:
    --------
    dict : 信号信息
    """
    print(f"\n{'='*70}")
    print(f"生成交易信号 - {stock_code}")
    print(f"{'='*70}\n")
    
    # 获取历史数据
    df = get_stock_data(trader, stock_code, days=60)
    
    if df is None or len(df) < lsma_period:
        print("❌ 数据不足，无法生成信号")
        return None
    
    print(f"✅ 数据获取成功")
    print(f"   数据范围: {df['time_key'].min()} 到 {df['time_key'].max()}")
    print(f"   数据条数: {len(df)}")
    
    # 使用收盘价计算指标
    close_prices = df['close'].values
    
    # 计算TSF和LSMA
    tsf_value = calculate_tsf(close_prices, period=tsf_period)
    lsma_value = calculate_lsma(close_prices, period=lsma_period)
    
    if tsf_value is None or lsma_value is None:
        print("❌ 指标计算失败")
        return None
    
    # 当前价格
    current_price = close_prices[-1]
    latest_date = df['time_key'].iloc[-1]
    
    # 计算差值
    diff = tsf_value - lsma_value
    
    # 生成信号
    signal = "HOLD"
    reason = ""
    
    if diff > buy_threshold:
        signal = "BUY"
        reason = f"TSF({tsf_value:.3f}) > LSMA({lsma_value:.3f}) + {buy_threshold}"
    elif diff < -sell_threshold:
        signal = "SELL"
        reason = f"TSF({tsf_value:.3f}) < LSMA({lsma_value:.3f}) - {sell_threshold}"
    else:
        signal = "HOLD"
        if diff > 0:
            reason = f"差值 {diff:.3f} 未达到买入阈值 {buy_threshold}"
        else:
            reason = f"差值 {diff:.3f} 未达到卖出阈值 {sell_threshold}"
    
    # 构建信号信息
    signal_info = {
        'date': latest_date,
        'price': current_price,
        'tsf': tsf_value,
        'lsma': lsma_value,
        'diff': diff,
        'signal': signal,
        'reason': reason,
        'buy_threshold': buy_threshold,
        'sell_threshold': sell_threshold
    }
    
    # 打印信号
    print(f"\n信号: {signal}")
    print(f"原因: {reason}")
    print(f"价格: HK${current_price:.3f}")
    print(f"TSF:  {tsf_value:.3f}")
    print(f"LSMA: {lsma_value:.3f}")
    print(f"差值: {diff:.3f}")
    
    return signal_info


def auto_trade(stock_code='HK.01797', 
               use_simulate=True, 
               buy_amount_hkd=10000,
               trading_pwd=None,
               dry_run=False,
               buy_threshold=1.0,
               sell_threshold=1.0):
    """
    自动交易
    
    Parameters:
    -----------
    stock_code : str
        股票代码
    use_simulate : bool
        True=模拟盘，False=真实盘
    buy_amount_hkd : float
        每次买入金额（港币）
    trading_pwd : str
        交易密码
    dry_run : bool
        是否仅模拟运行
    buy_threshold : float
        买入阈值
    sell_threshold : float
        卖出阈值
    """
    print("\n" + "="*70)
    print(f"东方甄选({stock_code})自动交易脚本")
    print("="*70)
    
    env_name = "模拟盘" if use_simulate else "真实盘"
    mode = "【模拟运行】" if dry_run else "【实际交易】"
    
    print(f"\n交易环境: {env_name}")
    print(f"运行模式: {mode}")
    print(f"买入金额: HK${buy_amount_hkd:,.2f}")
    print(f"买入阈值: {buy_threshold}")
    print(f"卖出阈值: {sell_threshold}")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ==================== 步骤1: 连接交易账户 ====================
    print(f"\n{'='*70}")
    print("步骤1: 连接交易账户")
    print(f"{'='*70}")
    
    trader = HKTrader(
        use_simulate=use_simulate,
        trading_pwd=trading_pwd
    )
    
    if not trader.connect():
        print("\n❌ 连接失败，退出")
        return False
    
    # 查看账户信息
    account_info = trader.get_account_info()
    
    if not account_info or len(account_info) == 0:
        print("\n❌ 无法获取账户信息，退出")
        trader.disconnect()
        return False
    
    # 获取可用资金
    available_cash = account_info.iloc[0].get('cash', 0)
    print(f"\n可用资金: HK${available_cash:,.2f}")
    
    # ==================== 步骤2: 生成信号 ====================
    print(f"\n{'='*70}")
    print("步骤2: 生成交易信号")
    print(f"{'='*70}")
    
    signal_info = generate_signal(
        trader, 
        stock_code=stock_code,
        buy_threshold=buy_threshold,
        sell_threshold=sell_threshold
    )
    
    if not signal_info:
        print("\n❌ 无法生成信号，退出")
        trader.disconnect()
        return False
    
    # ==================== 步骤3: 执行交易 ====================
    print(f"\n{'='*70}")
    print("步骤3: 执行交易")
    print(f"{'='*70}")
    
    trade_executed = False
    
    # ---------- 买入信号 ----------
    if signal_info['signal'] == 'BUY':
        print("\n🟢 收到买入信号")
        
        # 获取当前价格
        current_price = trader.get_current_price(stock_code)
        
        if not current_price:
            print("❌ 无法获取当前价格")
            trader.disconnect()
            return False
        
        print(f"当前价格: HK${current_price:.3f}")
        
        # 计算买入数量（港股100股起，100的整数倍）
        qty_float = buy_amount_hkd / current_price
        qty = int(qty_float // 100) * 100  # 向下取整到100的整数倍
        
        if qty < 100:
            print(f"\n⚠️  买入金额不足")
            print(f"   需要至少: HK${current_price * 100:.2f} (100股)")
            print(f"   当前设置: HK${buy_amount_hkd:.2f}")
            print(f"   建议增加买入金额")
        else:
            # 检查资金是否充足
            required_cash = qty * current_price * 1.01  # 预留1%
            
            if required_cash > available_cash:
                print(f"\n⚠️  资金不足")
                print(f"   需要: HK${required_cash:,.2f}")
                print(f"   可用: HK${available_cash:,.2f}")
            else:
                print(f"\n计划买入:")
                print(f"  数量: {qty} 股 ({qty//100} 手)")
                print(f"  金额: HK${qty * current_price:,.2f}")
                
                # 限价单（略低于市价，提高成交概率）
                buy_price = round(current_price * 0.999, 3)
                print(f"  价格: HK${buy_price:.3f} (略低于市价)")
                
                if dry_run:
                    print(f"\n【模拟运行】跳过实际下单")
                    trade_executed = True
                else:
                    # 实际下单
                    result = trader.buy(stock_code, buy_price, qty)
                    
                    if result is not None:
                        print(f"\n✅ 买入订单已提交")
                        order_id = result['order_id'].iloc[0]
                        print(f"   订单号: {order_id}")
                        trade_executed = True
                    else:
                        print(f"\n❌ 买入失败")
    
    # ---------- 卖出信号 ----------
    elif signal_info['signal'] == 'SELL':
        print("\n🔴 收到卖出信号")
        
        # 查看持仓
        positions = trader.get_positions()
        
        if positions is None or len(positions) == 0:
            print("\n⚠️  无持仓，无需卖出")
        else:
            # 查找该股票持仓
            stock_positions = positions[positions['code'] == stock_code]
            
            if len(stock_positions) == 0:
                print(f"\n⚠️  无{stock_code}持仓，无需卖出")
            else:
                qty = int(stock_positions['qty'].iloc[0])
                cost_price = stock_positions['cost_price'].iloc[0]
                
                # 数量必须是100的整数倍
                qty = (qty // 100) * 100
                
                if qty < 100:
                    print(f"\n⚠️  持仓不足100股，无法卖出")
                    print(f"   当前持仓: {stock_positions['qty'].iloc[0]} 股")
                else:
                    print(f"\n当前持仓:")
                    print(f"  数量: {qty} 股 ({qty//100} 手)")
                    print(f"  成本: HK${cost_price:.3f}")
                    
                    # 获取当前价格
                    current_price = trader.get_current_price(stock_code)
                    
                    if not current_price:
                        print("❌ 无法获取当前价格")
                    else:
                        profit_loss = (current_price - cost_price) * qty
                        profit_pct = (current_price / cost_price - 1) * 100
                        
                        print(f"  当前价: HK${current_price:.3f}")
                        print(f"  盈亏: HK${profit_loss:,.2f} ({profit_pct:+.2f}%)")
                        
                        print(f"\n计划卖出:")
                        print(f"  数量: {qty} 股 ({qty//100} 手)")
                        
                        # 限价单（略高于市价）
                        sell_price = round(current_price * 1.001, 3)
                        print(f"  价格: HK${sell_price:.3f} (略高于市价)")
                        
                        if dry_run:
                            print(f"\n【模拟运行】跳过实际下单")
                            trade_executed = True
                        else:
                            # 实际下单
                            result = trader.sell(stock_code, sell_price, qty)
                            
                            if result is not None:
                                print(f"\n✅ 卖出订单已提交")
                                order_id = result['order_id'].iloc[0]
                                print(f"   订单号: {order_id}")
                                trade_executed = True
                            else:
                                print(f"\n❌ 卖出失败")
    
    # ---------- 持有信号 ----------
    else:  # HOLD
        print("\n⚪ 收到持有信号")
        print("暂不交易，保持当前状态")
    
    # ==================== 步骤4: 显示账户状态 ====================
    print(f"\n{'='*70}")
    print("步骤4: 当前账户状态")
    print(f"{'='*70}")
    
    trader.get_account_info()
    trader.get_positions()
    
    # 查看今日订单
    if trade_executed:
        print(f"\n今日订单:")
        trader.get_orders()
    
    # ==================== 步骤5: 断开连接 ====================
    trader.disconnect()
    
    # ==================== 总结 ====================
    print(f"\n{'='*70}")
    print("执行总结")
    print(f"{'='*70}")
    print(f"股票: {stock_code}")
    print(f"信号: {signal_info['signal']}")
    print(f"交易: {'已执行' if trade_executed else '未执行'}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='东方甄选(HK.01797)自动交易脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 模拟盘 + 模拟运行（安全测试）
  python auto_trade_01797.py --dry-run

  # 模拟盘 + 实际下单
  python auto_trade_01797.py

  # 真实盘 + 模拟运行（测试）
  python auto_trade_01797.py --real --dry-run

  # 真实盘 + 实际下单（谨慎！）
  python auto_trade_01797.py --real --amount 20000

  # 自定义阈值
  python auto_trade_01797.py --buy-threshold 0.5 --sell-threshold 0.5

建议:
  1. 先用 --dry-run 测试
  2. 在模拟盘充分测试
  3. 确认无误后再用真实盘
        """
    )
    
    parser.add_argument('--stock',
                       type=str,
                       default='HK.01797',
                       help='股票代码（默认：HK.01797）')
    parser.add_argument('--real',
                       action='store_true',
                       help='使用真实盘（默认：模拟盘）⚠️')
    parser.add_argument('--amount',
                       type=float,
                       default=10000,
                       help='每次买入金额（港币，默认：10000）')
    parser.add_argument('--pwd',
                       type=str,
                       default=None,
                       help='交易密码')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='模拟运行，不实际下单（安全测试）')
    parser.add_argument('--buy-threshold',
                       type=float,
                       default=1.0,
                       help='买入阈值（默认：1.0）')
    parser.add_argument('--sell-threshold',
                       type=float,
                       default=1.0,
                       help='卖出阈值（默认：1.0）')
    
    args = parser.parse_args()
    
    # 确认真实盘操作
    if args.real and not args.dry_run:
        print("\n" + "="*70)
        print("⚠️  警告: 即将使用真实盘进行实际交易！")
        print("="*70)
        print("\n这将使用真实资金下单！")
        print("请确认你已经:")
        print("  1. 在模拟盘充分测试")
        print("  2. 理解策略风险")
        print("  3. 设置了止损")
        print("\n输入 'YES' 继续，其他任何输入将取消:")
        
        confirmation = input().strip()
        
        if confirmation != 'YES':
            print("\n已取消操作")
            return
    
    # 执行自动交易
    auto_trade(
        stock_code=args.stock,
        use_simulate=not args.real,
        buy_amount_hkd=args.amount,
        trading_pwd=args.pwd,
        dry_run=args.dry_run,
        buy_threshold=args.buy_threshold,
        sell_threshold=args.sell_threshold
    )


if __name__ == '__main__':
    main()