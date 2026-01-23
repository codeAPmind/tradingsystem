"""
数据缓存模块
本地保存股票数据，避免重复API调用
"""
import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, cache_dir: str = 'data_cache'):
        """
        初始化缓存
        
        Parameters:
        -----------
        cache_dir : str
            缓存目录路径
        """
        # 使用绝对路径
        if not os.path.isabs(cache_dir):
            base_dir = Path(__file__).parent.parent
            self.cache_dir = base_dir / cache_dir
        else:
            self.cache_dir = Path(cache_dir)
        
        self.cache_dir.mkdir(exist_ok=True)
        
        # 元数据文件
        self.metadata_file = self.cache_dir / 'metadata.json'
        self.metadata = self._load_metadata()
        
        print(f"✅ 缓存系统已初始化: {self.cache_dir}")
    
    def _load_metadata(self) -> dict:
        """加载元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata(self):
        """保存元数据"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def _get_cache_filename(self, ticker: str) -> Path:
        """获取缓存文件名"""
        # 处理特殊字符
        safe_ticker = ticker.replace('.', '_')
        return self.cache_dir / f"{safe_ticker}_prices.csv"
    
    def get_prices(
        self, 
        ticker: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
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
            
            # 转换日期，移除时区信息
            df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
            
            # 过滤日期范围
            if start_date:
                start_dt = pd.to_datetime(start_date).tz_localize(None)
                df = df[df['date'] >= start_dt]
            if end_date:
                end_dt = pd.to_datetime(end_date).tz_localize(None)
                df = df[df['date'] <= end_dt]
            
            if len(df) == 0:
                return None
            
            print(f"✅ 从缓存加载 {ticker}")
            print(f"   数据条数: {len(df)}")
            print(f"   日期范围: {df['date'].min().date()} 到 {df['date'].max().date()}")
            
            return df
        
        except Exception as e:
            print(f"⚠️  缓存读取失败: {e}")
            return None
    
    def set_prices(self, ticker: str, df: pd.DataFrame):
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
            # 确保date列存在
            if 'date' not in df.columns:
                print(f"⚠️  数据缺少date列")
                return
            
            # 如果已有缓存，合并数据
            if cache_file.exists():
                existing_df = pd.read_csv(cache_file)
                existing_df['date'] = pd.to_datetime(existing_df['date'])
                df['date'] = pd.to_datetime(df['date'])
                
                # 合并并去重
                combined_df = pd.concat([existing_df, df])
                combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
                combined_df = combined_df.sort_values('date')
                
                df = combined_df
            
            # 保存到CSV
            df.to_csv(cache_file, index=False)
            
            # 更新元数据
            self.metadata[ticker] = {
                'last_update': datetime.now().isoformat(),
                'record_count': len(df),
                'date_range': [
                    str(df['date'].min().date()),
                    str(df['date'].max().date())
                ]
            }
            self._save_metadata()
            
            print(f"✅ 缓存已保存: {ticker}")
        
        except Exception as e:
            print(f"⚠️  缓存保存失败: {e}")
    
    def clear_cache(self, ticker: Optional[str] = None):
        """
        清除缓存
        
        Parameters:
        -----------
        ticker : str, optional
            股票代码，如果不指定则清除所有缓存
        """
        if ticker:
            cache_file = self._get_cache_filename(ticker)
            if cache_file.exists():
                cache_file.unlink()
                if ticker in self.metadata:
                    del self.metadata[ticker]
                    self._save_metadata()
                print(f"✅ 已清除 {ticker} 缓存")
        else:
            # 清除所有缓存
            for file in self.cache_dir.glob('*_prices.csv'):
                file.unlink()
            self.metadata.clear()
            self._save_metadata()
            print(f"✅ 已清除所有缓存")
    
    def get_cache_info(self) -> dict:
        """获取缓存信息"""
        return {
            'cache_dir': str(self.cache_dir),
            'stocks': list(self.metadata.keys()),
            'total_stocks': len(self.metadata),
            'metadata': self.metadata
        }


# 使用示例
if __name__ == '__main__':
    cache = DataCache()
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'date': pd.date_range('2025-01-01', periods=5),
        'open': [100, 101, 102, 103, 104],
        'high': [105, 106, 107, 108, 109],
        'low': [95, 96, 97, 98, 99],
        'close': [102, 103, 104, 105, 106],
        'volume': [1000, 1100, 1200, 1300, 1400]
    })
    
    # 保存到缓存
    cache.set_prices('TEST', test_data)
    
    # 从缓存读取
    loaded_data = cache.get_prices('TEST')
    print("\n加载的数据:")
    print(loaded_data)
    
    # 查看缓存信息
    info = cache.get_cache_info()
    print("\n缓存信息:")
    print(json.dumps(info, indent=2, ensure_ascii=False))
    
    # 清除测试缓存
    cache.clear_cache('TEST')
