"""
Tushare数据获取
支持A股股票、指数、财务数据
"""
import os
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'futu_backtest_trader'))


class TushareDataFetcher:
    """Tushare数据获取器"""
    
    def __init__(self, token=None):
        """
        初始化
        
        Parameters:
        -----------
        token : str
            Tushare API token
            获取方式: https://tushare.pro/register
        """
        self.token = token or os.environ.get("TUSHARE_TOKEN")
        
        if not self.token:
            raise ValueError("请设置TUSHARE_TOKEN环境变量")
        
        # 导入tushare
        try:
            import tushare as ts
            self.ts = ts
        except ImportError:
            raise ImportError("请安装tushare: pip install tushare")
        
        # 设置token
        self.ts.set_token(self.token)
        self.pro = self.ts.pro_api()
        
        print(f"✅ Tushare已初始化")
    
    def get_stock_code_with_exchange(self, stock_code):
        """
        添加交易所前缀
        
        Parameters:
        -----------
        stock_code : str
            6位股票代码，如 '600519', '000001'
        
        Returns:
        --------
        str : 带交易所前缀的代码
            - 上海: '600519.SH'
            - 深圳: '000001.SZ'
        """
        if '.' in stock_code:
            return stock_code
        
        # 上海: 60xxxx, 68xxxx
        if stock_code.startswith('60') or stock_code.startswith('68'):
            return f"{stock_code}.SH"
        # 深圳: 00xxxx, 30xxxx
        elif stock_code.startswith('00') or stock_code.startswith('30'):
            return f"{stock_code}.SZ"
        else:
            raise ValueError(f"无法识别股票代码: {stock_code}")
    
    def get_history_kline(self, stock_code, start_date, end_date):
        """
        获取历史K线数据
        
        Parameters:
        -----------
        stock_code : str
            股票代码，如 '600519' 或 '600519.SH'
        start_date : str
            开始日期 'YYYY-MM-DD'
        end_date : str
            结束日期 'YYYY-MM-DD'
        
        Returns:
        --------
        DataFrame : K线数据
            包含: date, open, high, low, close, volume
        """
        ts_code = self.get_stock_code_with_exchange(stock_code)
        
        # 转换日期格式（Tushare使用YYYYMMDD）
        start = start_date.replace('-', '')
        end = end_date.replace('-', '')
        
        print(f"📊 获取 {ts_code} 从 {start_date} 到 {end_date} 的数据...")
        
        try:
            # 获取数据
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start,
                end_date=end
            )
            
            if df is None or len(df) == 0:
                print(f"❌ 未获取到数据")
                return None
            
            # 数据清洗
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.rename(columns={
                'trade_date': 'date',
                'vol': 'volume'
            })
            
            # 按日期排序
            df = df.sort_values('date')
            df = df.reset_index(drop=True)
            
            # Tushare的成交量单位是手（100股），转换为股
            df['volume'] = df['volume'] * 100
            
            print(f"✅ 成功获取 {len(df)} 条数据")
            
            return df[['date', 'open', 'high', 'low', 'close', 'volume']]
        
        except Exception as e:
            print(f"❌ 获取数据失败: {e}")
            return None
    
    def get_realtime_price(self, stock_code):
        """
        获取实时价格
        
        注意: Tushare免费版不支持实时数据
        需要使用东方财富或其他数据源
        """
        print(f"⚠️  Tushare免费版不支持实时数据")
        print(f"   建议使用东方财富API获取实时行情")
        return None
    
    def get_stock_basic(self, stock_code):
        """
        获取股票基本信息
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        
        Returns:
        --------
        dict : 股票信息
        """
        ts_code = self.get_stock_code_with_exchange(stock_code)
        
        try:
            df = self.pro.stock_basic(
                ts_code=ts_code,
                fields='ts_code,name,industry,market,list_date'
            )
            
            if df is None or len(df) == 0:
                return None
            
            return df.iloc[0].to_dict()
        
        except Exception as e:
            print(f"❌ 获取股票信息失败: {e}")
            return None
    
    def get_daily_basic(self, stock_code, trade_date=None):
        """
        获取每日指标
        包括: PE, PB, PS, 总市值、流通市值等
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        trade_date : str, optional
            交易日期 'YYYY-MM-DD'
        
        Returns:
        --------
        dict : 每日指标
        """
        ts_code = self.get_stock_code_with_exchange(stock_code)
        
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
        else:
            trade_date = trade_date.replace('-', '')
        
        try:
            df = self.pro.daily_basic(
                ts_code=ts_code,
                trade_date=trade_date,
                fields='ts_code,trade_date,pe,pb,ps,total_mv,circ_mv'
            )
            
            if df is None or len(df) == 0:
                return None
            
            return df.iloc[0].to_dict()
        
        except Exception as e:
            print(f"❌ 获取每日指标失败: {e}")
            return None


# 使用示例
if __name__ == '__main__':
    # 检查环境变量
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        print("❌ 请设置TUSHARE_TOKEN环境变量")
        print("   获取Token: https://tushare.pro/register")
        print("   设置方法: 在.env文件中添加 TUSHARE_TOKEN=your_token")
        exit(1)
    
    # 初始化
    try:
        fetcher = TushareDataFetcher()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        exit(1)
    
    # 获取贵州茅台历史数据
    print("\n=== 测试贵州茅台 ===")
    df = fetcher.get_history_kline('600519', '2025-01-01', '2025-01-22')
    if df is not None:
        print("\n数据前5行:")
        print(df.head())
        print("\n数据后5行:")
        print(df.tail())
    
    # 获取基本信息
    print("\n=== 股票信息 ===")
    info = fetcher.get_stock_basic('600519')
    if info:
        print(f"名称: {info.get('name')}")
        print(f"行业: {info.get('industry')}")
        print(f"市场: {info.get('market')}")
    
    # 获取估值指标
    print("\n=== 估值指标 ===")
    basic = fetcher.get_daily_basic('600519')
    if basic:
        print(f"PE: {basic.get('pe')}")
        print(f"PB: {basic.get('pb')}")
        print(f"PS: {basic.get('ps')}")
        print(f"总市值: {basic.get('total_mv')}万元")
