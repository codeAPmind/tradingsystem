# data/data_cache.py
import pandas as pd
import os
from datetime import datetime

class DataCache:
    """本地数据缓存"""
    
    def __init__(self, cache_dir='data_cache'):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def get_cache_path(self, stock_code, start_date, end_date):
        """生成缓存文件路径"""
        filename = f"{stock_code}_{start_date}_{end_date}.csv"
        return os.path.join(self.cache_dir, filename)
    
    def load(self, stock_code, start_date, end_date):
        """加载缓存数据"""
        path = self.get_cache_path(stock_code, start_date, end_date)
        
        if os.path.exists(path):
            print(f"📁 使用缓存数据: {stock_code}")
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            return df
        return None
    
    def save(self, stock_code, start_date, end_date, df):
        """保存数据到缓存"""
        path = self.get_cache_path(stock_code, start_date, end_date)
        df.to_csv(path)
        print(f"💾 数据已缓存: {path}")


# 使用方法
from data.futu_data import FutuDataFetcher
from data.data_cache import DataCache

cache = DataCache()
fetcher = FutuDataFetcher()

# 先尝试从缓存加载
df = cache.load('HK.01797', '2024-01-01', '2025-01-15')

if df is None:
    # 缓存没有，从富途获取
    fetcher.connect()
    df = fetcher.get_history_kline('HK.01797', '2024-01-01', '2025-01-15')
    fetcher.disconnect()
    
    # 保存到缓存
    if df is not None:
        cache.save('HK.01797', '2024-01-01', '2025-01-15', df)