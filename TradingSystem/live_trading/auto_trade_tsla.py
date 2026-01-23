#!/usr/bin/env python3
# auto_trade_tsla.py
"""
Tesla自动交易脚本
结合每日信号和实盘交易

功能:
1. 自动生成TSF-LSMA信号
2. 根据信号自动下单
3. 支持模拟盘和真实盘
4. 完整的风险控制
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
from datetime import datetime
from futu import OrderType

# 导入模块
from us_trader import USTrader
from daily_signal_tsla import generate_signal


def auto_trade(use_simulate=True, buy_amount_usd=500, trading_pwd=None, dry_run=False):
    """
    Tesla自动交易
    
    Parameters:
    -----------
    use_simulate : bool
        True=模拟盘，False=真实盘
    buy_amount_usd : float
        每次买入金额（美元）
    trading_pwd : str
        交易密码（可选）
    dry_run : bool
        是否仅模拟运行（不真实下单）
    """
    print("\n" + "="*70)
    print("Tesla自动交易脚本")
    print("="*70)
    
    env_name = "模拟盘" if use_simulate else "真实盘"
    mode = "【模拟运行】" if dry_run else "【实际交易】"
    
    print(f"\n交易环境: {env_name}")
    print(f"运行模式: {mode}")
    print(f"买入金额: ${buy_amount_usd:.2f}")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ==================== 步骤1: 生成信号 ====================
    print(f"\n{'='*70}")
    print("步骤1: 生成交易信号")
    print(f"{'='*70}")
    
    signal_info = generate_signal(use_cache=True)
    
    if not signal_info:
        print("\n❌ 无法生成信号，退出")
        return False
    
    # 显示信号
    print(f"\n信号: {signal_info['signal']}")
    print(f"原因: {signal_info['reason']}")
    print(f"价格: ${signal_info['price']:.2f}")
    
    # ==================== 步骤2: 连接交易账户 ====================
    print(f"\n{'='*70}")
    print("步骤2: 连接交易账户")
    print(f"{'='*70}")
    
    trader = USTrader(
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
    print(f"\n可用资金: ${available_cash:,.2f}")
    
    # ==================== 步骤3: 执行交易 ====================
    print(f"\n{'='*70}")
    print("步骤3: 执行交易")
    print(f"{'='*70}")
    
    trade_executed = False
    
    # ---------- 买入信号 ----------
    if signal_info['signal'] == 'BUY':
        print("\n🟢 收到买入信号")
        
        # 获取当前价格
        current_price = trader.get_current_price('US.TSLA')
        
        if not current_price:
            print("❌ 无法获取当前价格")
            trader.disconnect()
            return False
        
        print(f"当前价格: ${current_price:.2f}")
        
        # 计算买入数量
        qty = int(buy_amount_usd / current_price)
        
        if qty < 1:
            print(f"\n⚠️  买入金额不足")
            print(f"   需要至少: ${current_price:.2f}")
            print(f"   当前设置: ${buy_amount_usd:.2f}")
            print(f"   建议增加买入金额")
        else:
            # 检查资金是否充足
            required_cash = qty * current_price * 1.01  # 预留1%
            
            if required_cash > available_cash:
                print(f"\n⚠️  资金不足")
                print(f"   需要: ${required_cash:,.2f}")
                print(f"   可用: ${available_cash:,.2f}")
            else:
                print(f"\n计划买入:")
                print(f"  数量: {qty} 股")
                print(f"  金额: ${qty * current_price:.2f}")
                
                # 限价单（略低于市价，提高成交概率）
                buy_price = round(current_price * 0.999, 2)
                print(f"  价格: ${buy_price:.2f} (略低于市价)")
                
                if dry_run:
                    print(f"\n【模拟运行】跳过实际下单")
                    trade_executed = True
                else:
                    # 实际下单
                    result = trader.buy('US.TSLA', buy_price, qty)
                    
                    if result is not None:
                        print(f"\n✅ 买入订单已提交")
                        order_id = result['order_id'].iloc[0]
                        print(f"   订单号: {order_id}")
                        trade_executed = True
                    else:
                        print(f"\n❌ 买入失败")
    
    # ---------- 卖出信号 ----------
    elif signal_info['signal'] == 'SELL':
        print("\n🔵 收到卖出信号（极少见）")
        print("⚠️  卖出阈值40.0很高，这是极端信号")
        
        # 查看持仓
        positions = trader.get_positions()
        
        if positions is None or len(positions) == 0:
            print("\n⚠️  无持仓，无需卖出")
        else:
            # 查找Tesla持仓
            tsla_positions = positions[positions['code'] == 'US.TSLA']
            
            if len(tsla_positions) == 0:
                print("\n⚠️  无Tesla持仓，无需卖出")
            else:
                qty = int(tsla_positions['qty'].iloc[0])
                cost_price = tsla_positions['cost_price'].iloc[0]
                
                print(f"\n当前持仓:")
                print(f"  数量: {qty} 股")
                print(f"  成本: ${cost_price:.2f}")
                
                # 获取当前价格
                current_price = trader.get_current_price('US.TSLA')
                
                if not current_price:
                    print("❌ 无法获取当前价格")
                else:
                    profit_loss = (current_price - cost_price) * qty
                    profit_pct = (current_price / cost_price - 1) * 100
                    
                    print(f"  当前价: ${current_price:.2f}")
                    print(f"  盈亏: ${profit_loss:.2f} ({profit_pct:+.2f}%)")
                    
                    print(f"\n计划卖出:")
                    print(f"  数量: {qty} 股")
                    
                    # 限价单（略高于市价）
                    sell_price = round(current_price * 1.001, 2)
                    print(f"  价格: ${sell_price:.2f} (略高于市价)")
                    
                    if dry_run:
                        print(f"\n【模拟运行】跳过实际下单")
                        trade_executed = True
                    else:
                        # 实际下单
                        result = trader.sell('US.TSLA', sell_price, qty)
                        
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
    print(f"信号: {signal_info['signal']}")
    print(f"交易: {'已执行' if trade_executed else '未执行'}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Tesla自动交易脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 模拟盘 + 模拟运行（安全测试）
  python auto_trade_tsla.py --dry-run

  # 模拟盘 + 实际下单
  python auto_trade_tsla.py

  # 真实盘 + 模拟运行（测试）
  python auto_trade_tsla.py --real --dry-run

  # 真实盘 + 实际下单（谨慎！）
  python auto_trade_tsla.py --real --amount 1000

  # 指定交易密码
  python auto_trade_tsla.py --pwd YOUR_PWD

建议:
  1. 先用 --dry-run 测试
  2. 在模拟盘充分测试
  3. 确认无误后再用真实盘
        """
    )
    
    parser.add_argument('--real',
                       action='store_true',
                       help='使用真实盘（默认：模拟盘）⚠️')
    parser.add_argument('--amount',
                       type=float,
                       default=500,
                       help='每次买入金额（美元，默认：500）')
    parser.add_argument('--pwd',
                       type=str,
                       default=None,
                       help='交易密码')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='模拟运行，不实际下单（安全测试）')
    
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
        use_simulate=not args.real,
        buy_amount_usd=args.amount,
        trading_pwd=args.pwd,
        dry_run=args.dry_run
    )


if __name__ == '__main__':
    main()
