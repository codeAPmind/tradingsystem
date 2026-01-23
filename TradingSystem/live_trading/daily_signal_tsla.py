#!/usr/bin/env python3
# daily_signal_tsla.py
"""
Tesla (TSLA) 每日交易信号生成器
使用 TSF-LSMA 策略

策略参数:
- TSF周期: 9
- LSMA周期: 20
- 买入阈值: 1.0 (TSF > LSMA + 1.0)
- 卖出阈值: 40.0 (TSF < LSMA - 40.0)

注意: 卖出阈值40.0较大，意味着只在极端情况下卖出
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
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 添加项目路径
# 同级别
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 1. 获取当前脚本所在目录的“父目录”
# 第一个 dirname 是当前目录，第二个 dirname 就是上一层目录
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. 将父目录加入搜索路径
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data.us_data_cache import get_cache


class FinancialDatasetsAPI:
    """Financial Datasets API 客户端"""
    
    BASE_URL = "https://api.financialdatasets.ai"
    
    def __init__(self, api_key=None):
        import requests
        self.session = requests.Session()
        
        self.api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
        
        if self.api_key:
            self.session.headers.update({"X-API-KEY": self.api_key})
    
    def get_stock_prices(self, ticker, start_date=None, end_date=None):
        """获取股票价格"""
        url = f"{self.BASE_URL}/prices/"
        
        params = {
            'ticker': ticker,
            'interval': 'day',
            'interval_multiplier': 1,
        }
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'prices' in data:
                    prices_list = data['prices']
                    df = pd.DataFrame(prices_list)
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    return None
                
                if len(df) == 0:
                    return None
                
                df = df.rename(columns={
                    'time': 'date',
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume'
                })
                
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
            
            else:
                return None
                
        except Exception as e:
            return None


def calculate_tsf(data, period=9):
    """
    计算 TSF (Time Series Forecast)
    
    Parameters:
    -----------
    data : array-like
        价格数据
    period : int
        周期
    
    Returns:
    --------
    float : TSF值
    """
    if len(data) < period:
        return None
    
    # 取最近period个数据点
    recent_data = data[-period:]
    
    # 线性回归
    x = np.arange(len(recent_data))
    coeffs = np.polyfit(x, recent_data, 1)
    a, b = coeffs[0], coeffs[1]
    
    # 预测下一个点
    tsf_value = a * period + b
    
    return tsf_value


def calculate_lsma(data, period=20):
    """
    计算 LSMA (Least Squares Moving Average)
    
    Parameters:
    -----------
    data : array-like
        价格数据
    period : int
        周期
    
    Returns:
    --------
    float : LSMA值
    """
    if len(data) < period:
        return None
    
    # 取最近period个数据点
    recent_data = data[-period:]
    
    # 线性回归
    x = np.arange(len(recent_data))
    coeffs = np.polyfit(x, recent_data, 1)
    a, b = coeffs[0], coeffs[1]
    
    # 当前拟合值
    lsma_value = a * (period - 1) + b
    
    return lsma_value


def get_tsla_data(days=60, api_key=None, use_cache=True):
    """
    获取Tesla数据
    
    Parameters:
    -----------
    days : int
        获取最近多少天的数据
    api_key : str
        API密钥
    use_cache : bool
        是否使用缓存
    
    Returns:
    --------
    DataFrame
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    cache = get_cache()
    
    # 尝试从缓存加载
    if use_cache:
        cached_df = cache.get_prices('TSLA', start_date, end_date)
        
        if cached_df is not None and len(cached_df) >= 30:
            cache_start = cached_df['date'].min()
            cache_end = cached_df['date'].max()
            request_start = pd.to_datetime(start_date)
            request_end = pd.to_datetime(end_date)
            
            if cache_start <= request_start and cache_end >= request_end:
                return cached_df
    
    # 从API获取
    print(f"\n📡 从API获取数据...")
    api = FinancialDatasetsAPI(api_key=api_key)
    df = api.get_stock_prices('TSLA', start_date=start_date, end_date=end_date)
    
    if df is not None and len(df) > 0:
        if use_cache:
            cache.set_prices('TSLA', df)
        return df
    
    return None


def generate_signal(api_key=None, use_cache=True):
    """
    生成Tesla交易信号
    
    Parameters:
    -----------
    api_key : str
        API密钥
    use_cache : bool
        是否使用缓存
    
    Returns:
    --------
    dict : 信号信息
    """
    print(f"\n{'='*70}")
    print(f"Tesla (TSLA) 每日信号生成")
    print(f"{'='*70}\n")
    
    # 获取数据（最近60天）
    df = get_tsla_data(days=60, api_key=api_key, use_cache=use_cache)
    
    if df is None or len(df) < 30:
        print("❌ 无法获取足够的数据")
        return None
    
    print(f"✅ 数据获取成功")
    print(f"   数据范围: {df['date'].min().date()} 到 {df['date'].max().date()}")
    print(f"   数据条数: {len(df)}")
    
    # 使用收盘价计算指标
    close_prices = df['close'].values
    
    # 计算TSF和LSMA
    tsf_period = 9
    lsma_period = 20
    
    if len(close_prices) < lsma_period:
        print(f"❌ 数据不足，需要至少{lsma_period}个交易日")
        return None
    
    tsf_value = calculate_tsf(close_prices, period=tsf_period)
    lsma_value = calculate_lsma(close_prices, period=lsma_period)
    
    if tsf_value is None or lsma_value is None:
        print("❌ 指标计算失败")
        return None
    
    # 当前价格
    current_price = close_prices[-1]
    latest_date = df['date'].iloc[-1]
    
    # 计算差值
    diff = tsf_value - lsma_value
    
    # 策略参数
    buy_threshold = 1.0
    sell_threshold = 40.0
    
    # 生成信号
    signal = "HOLD"
    reason = ""
    
    if diff > buy_threshold:
        signal = "BUY"
        reason = f"TSF({tsf_value:.2f}) > LSMA({lsma_value:.2f}) + {buy_threshold}"
    elif diff < -sell_threshold:
        signal = "SELL"
        reason = f"TSF({tsf_value:.2f}) < LSMA({lsma_value:.2f}) - {sell_threshold}"
    else:
        signal = "HOLD"
        if diff > 0:
            reason = f"差值 {diff:.2f} 未达到买入阈值 {buy_threshold}"
        else:
            reason = f"差值 {diff:.2f} 未达到卖出阈值 {sell_threshold}"
    
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
    
    return signal_info


def print_signal(signal_info):
    """打印信号信息"""
    
    if signal_info is None:
        return
    
    print(f"\n{'='*70}")
    print(f"📊 信号报告")
    print(f"{'='*70}\n")
    
    # 基本信息
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据日期: {signal_info['date'].strftime('%Y-%m-%d')}")
    print(f"股票代码: TSLA (Tesla Inc.)")
    
    print(f"\n💰 价格信息:")
    print(f"  当前价格: ${signal_info['price']:.2f}")
    
    print(f"\n📈 技术指标:")
    print(f"  TSF(9):   {signal_info['tsf']:.2f}")
    print(f"  LSMA(20): {signal_info['lsma']:.2f}")
    print(f"  差值:     {signal_info['diff']:.2f}")
    
    print(f"\n⚙️ 策略参数:")
    print(f"  买入阈值: {signal_info['buy_threshold']:.1f}")
    print(f"  卖出阈值: {signal_info['sell_threshold']:.1f}")
    
    # 信号
    signal = signal_info['signal']
    
    print(f"\n🎯 交易信号:")
    
    if signal == "BUY":
        print(f"  ✅ 【买入信号】 🟢")
        print(f"  原因: {signal_info['reason']}")
        print(f"\n  💡 操作建议:")
        print(f"     - 考虑买入Tesla股票")
        print(f"     - 建议分批建仓（不要all-in）")
        print(f"     - 设置止损: ${signal_info['price'] * 0.95:.2f} (-5%)")
        
    elif signal == "SELL":
        print(f"  ❌ 【卖出信号】 🔵")
        print(f"  原因: {signal_info['reason']}")
        print(f"\n  💡 操作建议:")
        print(f"     - 考虑卖出持仓")
        print(f"     - 注意: 卖出阈值很高(40.0)，这是极端信号")
        print(f"     - 市场可能出现重大转折")
        
    else:  # HOLD
        print(f"  ⏸️ 【持有/观望】 ⚪")
        print(f"  原因: {signal_info['reason']}")
        print(f"\n  💡 操作建议:")
        print(f"     - 继续持有现有仓位")
        print(f"     - 或者观望等待更好时机")
        print(f"     - 注意: 买入阈值较低(1.0)，容易触发")
        print(f"     - 注意: 卖出阈值很高(40.0)，很难触发")
    
    # 风险提示
    print(f"\n⚠️ 风险提示:")
    print(f"  1. 本信号仅供参考，不构成投资建议")
    print(f"  2. 策略使用极端卖出阈值(40.0)")
    print(f"     → 很容易买入，很难卖出")
    print(f"     → 适合长期持仓策略")
    print(f"  3. Tesla股价波动性大，请控制仓位")
    print(f"  4. 请根据自身风险承受能力决策")
    print(f"  5. 建议设置止损保护资金安全")
    
    print(f"\n{'='*70}\n")


def save_signal_to_file(signal_info, output_dir='signals'):
    """
    保存信号到文件
    
    Parameters:
    -----------
    signal_info : dict
        信号信息
    output_dir : str
        输出目录
    """
    if signal_info is None:
        return
    
    # 创建目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 文件名：日期_信号.txt
    date_str = signal_info['date'].strftime('%Y%m%d')
    filename = f"{output_dir}/TSLA_{date_str}_signal.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"{'='*70}\n")
        f.write(f"Tesla (TSLA) 交易信号\n")
        f.write(f"{'='*70}\n\n")
        
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"数据日期: {signal_info['date'].strftime('%Y-%m-%d')}\n")
        f.write(f"股票代码: TSLA\n\n")
        
        f.write(f"价格信息:\n")
        f.write(f"  当前价格: ${signal_info['price']:.2f}\n\n")
        
        f.write(f"技术指标:\n")
        f.write(f"  TSF(9):   {signal_info['tsf']:.2f}\n")
        f.write(f"  LSMA(20): {signal_info['lsma']:.2f}\n")
        f.write(f"  差值:     {signal_info['diff']:.2f}\n\n")
        
        f.write(f"策略参数:\n")
        f.write(f"  买入阈值: {signal_info['buy_threshold']:.1f}\n")
        f.write(f"  卖出阈值: {signal_info['sell_threshold']:.1f}\n\n")
        
        f.write(f"交易信号: {signal_info['signal']}\n")
        f.write(f"原因: {signal_info['reason']}\n")
    
    print(f"✅ 信号已保存到: {filename}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Tesla每日交易信号生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--api-key',
                       type=str,
                       default=None,
                       help='financialdatasets.ai API密钥')
    parser.add_argument('--no-cache',
                       action='store_true',
                       help='不使用缓存')
    parser.add_argument('--save',
                       action='store_true',
                       help='保存信号到文件')
    
    args = parser.parse_args()
    
    # 生成信号
    signal_info = generate_signal(
        api_key=args.api_key,
        use_cache=not args.no_cache
    )
    
    # 打印信号
    print_signal(signal_info)
    
    # 保存到文件
    if args.save and signal_info:
        save_signal_to_file(signal_info)


if __name__ == '__main__':
    main()