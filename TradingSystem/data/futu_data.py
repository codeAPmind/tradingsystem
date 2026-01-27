# data/futu_data.py
"""
富途数据获取器
优化版本：返回标准格式的DataFrame，支持缓存
"""
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
        获取历史K线数据（返回标准格式）
        
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
        DataFrame : 标准格式，包含 date, open, high, low, close, volume 列
                   date 列为字符串格式 'YYYY-MM-DD'
                   不使用索引，普通DataFrame
        """
        if not self.quote_ctx:
            self.connect()
        
        autype_name = {AuType.NONE: "不复权", AuType.QFQ: "前复权", AuType.HFQ: "后复权"}
        print(f"📊 [Futu] 获取 {stock_code} 从 {start_date} 到 {end_date} ({autype_name.get(autype, '不复权')})...")
        
        ret, data, page_req_key = self.quote_ctx.request_history_kline(
            stock_code,
            start=start_date,
            end=end_date,
            ktype=ktype,
            autype=autype,
            max_count=1000
        )
        
        if ret == RET_OK:
            # 重要：转换为标准格式
            # 1. 提取需要的列
            result_df = pd.DataFrame({
                'date': data['time_key'].values,  # 直接使用原始日期字符串
                'open': data['open'].values,
                'high': data['high'].values,
                'low': data['low'].values,
                'close': data['close'].values,
                'volume': data['volume'].values
            })
            
            # 2. 确保 date 列是字符串格式 'YYYY-MM-DD'
            # 如果 time_key 是 datetime，转换为字符串
            if pd.api.types.is_datetime64_any_dtype(result_df['date']):
                result_df['date'] = pd.to_datetime(result_df['date']).dt.strftime('%Y-%m-%d')
            else:
                # 如果已经是字符串，确保格式正确
                result_df['date'] = pd.to_datetime(result_df['date']).dt.strftime('%Y-%m-%d')
            
            # 3. 重置索引，确保是普通DataFrame（不使用日期索引）
            result_df = result_df.reset_index(drop=True)
            
            # 4. 确保数值列是float类型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                result_df[col] = result_df[col].astype(float)
            
            print(f"✅ [Futu] 成功获取 {len(result_df)} 条数据")
            print(f"   列: {list(result_df.columns)}")
            print(f"   日期范围: {result_df['date'].iloc[0]} 到 {result_df['date'].iloc[-1]}")
            print(f"   数据类型: date={result_df['date'].dtype}, close={result_df['close'].dtype}")
            
            return result_df
        else:
            print(f"❌ [Futu] 获取数据失败: {data}")
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
    
    try:
        fetcher.connect()
        
        print("\n" + "="*70)
        print("测试1: 获取东方甄选数据")
        print("="*70)
        
        df = fetcher.get_history_kline('HK.01797', '2024-12-01', '2025-01-27')
        if df is not None:
            print("\n数据预览:")
            print(df.head())
            print(f"\n数据信息:")
            print(f"  形状: {df.shape}")
            print(f"  列: {list(df.columns)}")
            print(f"  类型:\n{df.dtypes}")
            print(f"\n最后5行:")
            print(df.tail())
        
        print("\n" + "="*70)
        print("测试2: 获取腾讯控股数据")
        print("="*70)
        
        df2 = fetcher.get_history_kline('HK.00700', '2025-01-01', '2025-01-27')
        if df2 is not None:
            print("\n数据预览:")
            print(df2.head())
        
        print("\n" + "="*70)
        print("测试3: 获取实时价格")
        print("="*70)
        
        price1 = fetcher.get_realtime_price('HK.01797')
        price2 = fetcher.get_realtime_price('HK.00700')
        
        print(f"\n东方甄选 (HK.01797): HK${price1:.2f}")
        print(f"腾讯控股 (HK.00700): HK${price2:.2f}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        fetcher.disconnect()
        print("\n✅ 测试完成")
