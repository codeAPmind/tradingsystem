# daily_signal.py
"""
每日交易信号生成器

用途：
- 每天收盘后（15:05）运行
- 计算TSF-LSMA指标
- 生成次日操作建议

使用方法：
  python daily_signal.py

输出：
- 买入信号：次日开盘买入
- 卖出信号：次日开盘卖出
- 观望：继续持有或等待
"""
import sys
import os
# 同级别
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# 1. 获取当前脚本所在目录的“父目录”
# 第一个 dirname 是当前目录，第二个 dirname 就是上一层目录
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. 将父目录加入搜索路径
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from datetime import datetime, timedelta
from data.futu_data import FutuDataFetcher
import numpy as np
from futu import AuType


def calculate_tsf(prices, period=9):
    """
    计算TSF指标
    
    Parameters:
    -----------
    prices : array
        价格数组
    period : int
        周期（默认9）
    
    Returns:
    --------
    float : TSF值
    """
    data = prices[-period:]
    x = np.arange(period)
    coeffs = np.polyfit(x, data, 1)
    a, b = coeffs[0], coeffs[1]
    return a * period + b


def calculate_lsma(prices, period=20):
    """
    计算LSMA指标
    
    Parameters:
    -----------
    prices : array
        价格数组
    period : int
        周期（默认20）
    
    Returns:
    --------
    float : LSMA值
    """
    data = prices[-period:]
    x = np.arange(period)
    coeffs = np.polyfit(x, data, 1)
    a, b = coeffs[0], coeffs[1]
    return a * (period - 1) + b


def check_signal(stock_code='HK.01797', 
                buy_threshold=1.2, 
                sell_threshold=1.0,
                has_position=False):
    """
    检查交易信号
    
    Parameters:
    -----------
    stock_code : str
        股票代码（默认：HK.01797 东方甄选）
    buy_threshold : float
        买入阈值（默认：1.2）
    sell_threshold : float
        卖出阈值（默认：1.0）
    has_position : bool
        是否已持仓（默认：False）
    """
    
    fetcher = FutuDataFetcher()
    fetcher.connect()
    
    print(f"\n{'='*70}")
    print(f"东方甄选 (01797) 交易信号")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    try:
        # 获取最近40天数据（确保够用）
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=50)).strftime('%Y-%m-%d')
        
        print(f"正在获取数据...")
        df = fetcher.get_history_kline(
            stock_code,
            start_date,
            end_date,
            autype=AuType.NONE  # 不复权
        )
        
        if df is None or len(df) < 20:
            print("❌ 数据不足，无法计算指标")
            return
        
        print(f"✅ 成功获取 {len(df)} 条数据\n")
        
        # 提取收盘价
        prices = df['close'].values
        
        # 计算指标
        tsf = calculate_tsf(prices, 9)
        lsma = calculate_lsma(prices, 20)
        diff = tsf - lsma
        
        # 当前价格
        close_price = prices[-1]
        prev_close = prices[-2] if len(prices) > 1 else close_price
        change_pct = ((close_price - prev_close) / prev_close) * 100
        
        # 显示当前状态
        print(f"📊 当前数据")
        print(f"{'-'*70}")
        print(f"今日收盘:  {close_price:.3f} ({change_pct:+.2f}%)")
        print(f"昨日收盘:  {prev_close:.3f}")
        print(f"")
        print(f"📈 技术指标")
        print(f"{'-'*70}")
        print(f"TSF(9):    {tsf:.3f}")
        print(f"LSMA(20):  {lsma:.3f}")
        print(f"差值:      {diff:.3f}")
        print(f"")
        print(f"⚙️  策略参数")
        print(f"{'-'*70}")
        print(f"买入阈值:  {buy_threshold}")
        print(f"卖出阈值:  {sell_threshold}")
        print(f"当前仓位:  {'有持仓' if has_position else '空仓'}")
        print(f"")
        
        # 判断信号
        print(f"{'='*70}")
        
        if not has_position:
            # 没有持仓，看买入信号
            if diff > buy_threshold and diff < buy_threshold+ 0.4:
                print(f"🟢 【买入信号】")
                print(f"{'='*70}")
                print(f"触发条件: Diff({diff:.3f}) > 买入阈值({buy_threshold})")
                print(f"")
                print(f"📋 明日操作建议：")
                print(f"  操作: 开盘买入")
                print(f"  参考价格: {close_price:.3f}")
                print(f"  建议价格区间: {close_price*0.97:.3f} - {close_price*1.03:.3f} (±3%)")
                print(f"  建议仓位: 50% 资金（约50,000 HKD）")
                print(f"  预计数量: {int(50000 / close_price / 100) * 100} 股")
                print(f"")
                print(f"⚠️  注意事项：")
                print(f"  1. 次日09:30开盘时检查价格")
                print(f"  2. 如果开盘价超过 {close_price*1.03:.3f}，放弃本次")
                print(f"  3. 记录实际成交价格")
                print(f"{'='*70}")
            
            else:
                print(f"⚪ 【观望】- 等待买入信号")
                print(f"{'='*70}")
                print(f"当前差值: {diff:.3f}")
                print(f"距离买入: 还需上涨 {buy_threshold - diff:.3f}")
                print(f"")
                print(f"📋 建议：")
                print(f"  继续等待，不要冲动买入")
                print(f"{'='*70}")
        
        else:
            # 有持仓，看卖出信号
            if diff > sell_threshold:
                print(f"🔴 【卖出信号】")
                print(f"{'='*70}")
                print(f"触发条件: Diff({diff:.3f}) < -卖出阈值(-{sell_threshold})")
                print(f"")
                print(f"📋 明日操作建议：")
                print(f"  操作: 开盘卖出")
                print(f"  参考价格: {close_price:.3f}")
                print(f"  建议价格区间: {close_price*0.97:.3f} - {close_price*1.03:.3f} (±3%)")
                print(f"  卖出数量: 全部持仓")
                print(f"")
                print(f"⚠️  注意事项：")
                print(f"  1. 次日09:30开盘时检查价格")
                print(f"  2. 优先使用市价单快速成交")
                print(f"  3. 记录实际成交价格和盈亏")
                print(f"{'='*70}")
            
            else:
                print(f"⚪ 【持有】- 继续持仓")
                print(f"{'='*70}")
                print(f"当前差值: {diff:.3f}")
                print(f"距离卖出: 还需下跌 {diff + sell_threshold:.3f}")
                print(f"")
                print(f"📋 建议：")
                print(f"  继续持有，耐心等待")
                print(f"  关注日内波动")
                print(f"{'='*70}")
        
        print(f"")
        
        # 显示最近5天数据
        print(f"📅 最近5天数据")
        print(f"{'-'*70}")
        print(f"{'日期':<12} {'收盘':<8} {'涨跌%':<8}")
        print(f"{'-'*70}")
        
        for i in range(max(0, len(df)-5), len(df)):
            date = df.index[i].strftime('%Y-%m-%d')
            close = df['close'].iloc[i]
            if i > 0:
                prev = df['close'].iloc[i-1]
                chg = ((close - prev) / prev) * 100
                print(f"{date:<12} {close:<8.3f} {chg:>+7.2f}%")
            else:
                print(f"{date:<12} {close:<8.3f} {'--':<8}")
        
        print(f"{'-'*70}\n")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        fetcher.disconnect()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='每日交易信号生成')
    parser.add_argument('--stock',
                       default='HK.01797',
                       help='股票代码（默认：HK.01797）')
    parser.add_argument('--buy',
                       type=float,
                       default=0.9,
                       help='买入阈值（默认：1.2）')
    parser.add_argument('--sell',
                       type=float,
                       default=4.0,
                       help='卖出阈值（默认：1.0）')
    parser.add_argument('--position',
                       action='store_true',
                       help='是否已持仓（默认：False）')
    
    args = parser.parse_args()
    
    check_signal(
        stock_code=args.stock,
        buy_threshold=args.buy,
        sell_threshold=args.sell,
        has_position=args.position
    )


if __name__ == '__main__':
    main()