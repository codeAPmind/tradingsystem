# data_cache.py
"""
数据缓存模块
本地保存股票数据，避免重复API调用
"""
import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path


class USDataCache:
    """数据缓存管理器"""
    
    def __init__(self, cache_dir='data_cache'):
        """
        初始化缓存
        
        Parameters:
        -----------
        cache_dir : str
            缓存目录路径
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 元数据文件
        self.metadata_file = self.cache_dir / 'metadata.json'
        self.metadata = self._load_metadata()
    
    def _load_metadata(self):
        """加载元数据"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """保存元数据"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def _get_cache_filename(self, ticker):
        """获取缓存文件名"""
        return self.cache_dir / f"{ticker.upper()}_prices.csv"
    
    def get_prices(self, ticker, start_date=None, end_date=None):
        """
        从缓存获取价格数据
        
        Parameters:
        -----------
        ticker : str
            股票代码
        start_date : str, optional
            开始日期 'YYYY-MM-DD'
        end_date : str, optional
            结束日期 'YYYY-MM-DD'
        
        Returns:
        --------
        DataFrame or None
        """
        cache_file = self._get_cache_filename(ticker)
        
        if not cache_file.exists():
            return None
        
        try:
            # 读取缓存
            df = pd.read_csv(cache_file)
            
            # 转换日期，移除时区信息避免比较问题
            df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
            
            # 过滤日期范围（转换为无时区的datetime）
            if start_date:
                start_dt = pd.to_datetime(start_date).tz_localize(None)
                df = df[df['date'] >= start_dt]
            if end_date:
                end_dt = pd.to_datetime(end_date).tz_localize(None)
                df = df[df['date'] <= end_dt]
            
            if len(df) == 0:
                return None
            
            # 获取元数据
            ticker_key = ticker.upper()
            cache_info = self.metadata.get(ticker_key, {})
            
            print(f"✅ 从缓存加载数据")
            print(f"   缓存文件: {cache_file.name}")
            print(f"   数据条数: {len(df)}")
            print(f"   日期范围: {df['date'].min().date()} 到 {df['date'].max().date()}")
            
            if cache_info.get('last_update'):
                print(f"   最后更新: {cache_info['last_update']}")
            
            return df
            
        except Exception as e:
            print(f"⚠️ 读取缓存失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def set_prices(self, ticker, df):
        """
        保存价格数据到缓存
        
        Parameters:
        -----------
        ticker : str
            股票代码
        df : DataFrame
            价格数据
        """
        if df is None or len(df) == 0:
            return
        
        cache_file = self._get_cache_filename(ticker)
        
        try:
            # 创建副本避免修改原数据
            df = df.copy()
            
            # 确保date列是datetime类型，移除时区信息
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                # 移除时区信息
                if hasattr(df['date'].dtype, 'tz') and df['date'].dtype.tz is not None:
                    df['date'] = df['date'].dt.tz_localize(None)
            
            # 如果缓存已存在，合并数据
            if cache_file.exists():
                existing_df = pd.read_csv(cache_file)
                existing_df['date'] = pd.to_datetime(existing_df['date']).dt.tz_localize(None)
                
                # 合并并去重
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
                combined_df = combined_df.sort_values('date')
                df = combined_df
            
            # 保存到CSV
            df.to_csv(cache_file, index=False)
            
            # 更新元数据
            ticker_key = ticker.upper()
            self.metadata[ticker_key] = {
                'ticker': ticker_key,
                'rows': len(df),
                'start_date': df['date'].min().strftime('%Y-%m-%d'),
                'end_date': df['date'].max().strftime('%Y-%m-%d'),
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'cache_file': cache_file.name
            }
            self._save_metadata()
            
            print(f"✅ 数据已保存到缓存")
            print(f"   缓存文件: {cache_file.name}")
            print(f"   数据条数: {len(df)}")
            print(f"   日期范围: {df['date'].min().date()} 到 {df['date'].max().date()}")
            
        except Exception as e:
            print(f"⚠️ 保存缓存失败: {e}")
            import traceback
            traceback.print_exc()
    
    def clear_cache(self, ticker=None):
        """
        清除缓存
        
        Parameters:
        -----------
        ticker : str, optional
            股票代码。如果不提供，清除所有缓存
        """
        if ticker:
            # 清除特定股票的缓存
            ticker_key = ticker.upper()
            cache_file = self._get_cache_filename(ticker)
            
            if cache_file.exists():
                cache_file.unlink()
                print(f"✅ 已清除 {ticker_key} 的缓存")
            
            if ticker_key in self.metadata:
                del self.metadata[ticker_key]
                self._save_metadata()
        else:
            # 清除所有缓存
            for cache_file in self.cache_dir.glob('*.csv'):
                cache_file.unlink()
            
            self.metadata = {}
            self._save_metadata()
            print(f"✅ 已清除所有缓存")
    
    def get_cache_info(self, ticker=None):
        """
        获取缓存信息
        
        Parameters:
        -----------
        ticker : str, optional
            股票代码。如果不提供，返回所有缓存信息
        """
        if ticker:
            ticker_key = ticker.upper()
            return self.metadata.get(ticker_key)
        else:
            return self.metadata
    
    def print_cache_summary(self):
        """打印缓存摘要"""
        print("\n" + "="*70)
        print("缓存摘要")
        print("="*70)
        
        if not self.metadata:
            print("缓存为空")
            return
        
        print(f"缓存目录: {self.cache_dir.absolute()}")
        print(f"缓存股票数: {len(self.metadata)}")
        print()
        
        for ticker, info in sorted(self.metadata.items()):
            print(f"{ticker}:")
            print(f"  数据条数: {info['rows']}")
            print(f"  日期范围: {info['start_date']} 到 {info['end_date']}")
            print(f"  最后更新: {info['last_update']}")
            print(f"  缓存文件: {info['cache_file']}")
            print()


# 全局缓存实例
_cache = None


def get_cache(cache_dir='data_cache'):
    """
    获取全局缓存实例
    
    Parameters:
    -----------
    cache_dir : str
        缓存目录路径
    
    Returns:
    --------
    USDataCache
    """
    global _cache
    if _cache is None:
        _cache = USDataCache(cache_dir)
    return _cache