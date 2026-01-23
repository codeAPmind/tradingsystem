# data/futu_data.py
from futu import OpenQuoteContext, RET_OK, KLType, AuType
import pandas as pd
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import FUTU_HOST, FUTU_PORT


class FutuDataFetcher:
    """富途数据获取器"""
    
    def __init__(self, host=FUTU_HOST, port=FUTU_PORT):
        self.host = host
        self.port = port
        self.quote_ctx = None
    
    def connect(self):
        """连接FutuOpenD"""
        self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)
        print(f"✅ 已连接到FutuOpenD: {self.host}:{self.port}")
    
    def disconnect(self):
        """断开连接"""
        if self.quote_ctx:
            self.quote_ctx.close()
            print("✅ 已断开FutuOpenD连接")
    
    def get_history_kline(self, stock_code, start_date, end_date, ktype='K_DAY', autype=AuType.NONE):
        """
        获取历史K线数据
        
        Parameters:
        -----------
        stock_code : str
            股票代码，如 'HK.00700'
        start_date : str
            开始日期，格式 'YYYY-MM-DD'
        end_date : str
            结束日期，格式 'YYYY-MM-DD'
        ktype : str
            K线类型：'K_DAY'(日线), 'K_WEEK'(周线), 'K_MON'(月线)
        autype : AuType
            复权类型：AuType.NONE(不复权), AuType.QFQ(前复权), AuType.HFQ(后复权)
            默认使用不复权 (AuType.NONE)
        
        Returns:
        --------
        DataFrame : 包含OHLCV数据
        """
        if not self.quote_ctx:
            self.connect()
        
        autype_name = {AuType.NONE: "不复权", AuType.QFQ: "前复权", AuType.HFQ: "后复权"}
        print(f"📊 获取 {stock_code} 从 {start_date} 到 {end_date} 的数据 ({autype_name.get(autype, '不复权')})...")
        
        ret, data, page_req_key = self.quote_ctx.request_history_kline(
            stock_code,
            start=start_date,
            end=end_date,
            ktype=ktype,
            autype=autype,  # 添加复权类型参数
            max_count=1000
        )
        
        if ret == RET_OK:
            # 数据清洗和格式转换
            data['time_key'] = pd.to_datetime(data['time_key'])
            data = data.rename(columns={
                'time_key': 'datetime',
            })
            data = data.set_index('datetime')
            
            print(f"✅ 成功获取 {len(data)} 条数据")
            return data[['open', 'high', 'low', 'close', 'volume']]
        else:
            print(f"❌ 获取数据失败: {data}")
            return None
    
    def get_realtime_price(self, stock_code):
        """获取实时价格"""
        if not self.quote_ctx:
            self.connect()
        
        ret, data = self.quote_ctx.get_market_snapshot([stock_code])
        
        if ret == RET_OK:
            return data.iloc[0]['last_price']
        else:
            print(f"❌ 获取实时价格失败: {data}")
            return None
    
    def get_multiple_stocks(self, stock_list, start_date, end_date):
        """批量获取多只股票数据"""
        all_data = {}
        
        for stock_code in stock_list:
            df = self.get_history_kline(stock_code, start_date, end_date)
            if df is not None:
                all_data[stock_code] = df
        
        return all_data


# 使用示例
if __name__ == '__main__':
    fetcher = FutuDataFetcher()
    fetcher.connect()
    
    # 获取腾讯历史数据
    df = fetcher.get_history_kline('HK.00700', '2024-01-01', '2025-01-15')
    if df is not None:
        print("\n数据前5行:")
        print(df.head())
        print("\n数据后5行:")
        print(df.tail())
    
    # 获取实时价格
    price = fetcher.get_realtime_price('HK.00700')
    print(f"\n腾讯当前价格: {price}")
    
    fetcher.disconnect()