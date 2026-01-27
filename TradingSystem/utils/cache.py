# utils/cache.py
"""
数据缓存模块
优先使用本地缓存，减少API调用
"""
import pandas as pd
import os
import json
from datetime import datetime
from pathlib import Path


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, cache_dir='data_cache'):
        """
        初始化缓存管理器
        
        Parameters:
        -----------
        cache_dir : str
            缓存目录路径
        """
        self.cache_dir = Path(cache_dir)
        
        # 创建缓存目录
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ 创建缓存目录: {self.cache_dir}")
        
        # 元数据文件
        self.metadata_file = self.cache_dir / 'cache_metadata.json'
        self.metadata = self._load_metadata()
    
    def _load_metadata(self):
        """加载缓存元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  加载元数据失败: {e}")
                return {}
        return {}
    
    def _save_metadata(self):
        """保存缓存元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  保存元数据失败: {e}")
    
    def _get_cache_key(self, stock_code, start_date, end_date):
        """生成缓存键"""
        return f"{stock_code}_{start_date}_{end_date}"
    
    def _get_cache_path(self, stock_code, start_date, end_date):
        """生成缓存文件路径"""
        cache_key = self._get_cache_key(stock_code, start_date, end_date)
        filename = f"{cache_key}.csv"
        return self.cache_dir / filename
    
    def get_prices(self, stock_code, start_date, end_date):
        """
        从缓存加载价格数据
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        start_date : str
            开始日期 'YYYY-MM-DD'
        end_date : str
            结束日期 'YYYY-MM-DD'
        
        Returns:
        --------
        DataFrame or None : 缓存的数据，如果不存在返回None
        """
        cache_path = self._get_cache_path(stock_code, start_date, end_date)
        cache_key = self._get_cache_key(stock_code, start_date, end_date)
        
        if not cache_path.exists():
            return None
        
        try:
            # 读取CSV
            df = pd.read_csv(cache_path)
            
            # 验证数据完整性
            if 'date' not in df.columns:
                print(f"⚠️  缓存数据格式错误（缺少date列）: {cache_key}")
                return None
            
            # 检查缓存时间
            if cache_key in self.metadata:
                cache_time = self.metadata[cache_key].get('cached_at', '')
                rows = len(df)
                print(f"📁 使用缓存: {stock_code} ({rows}行) [缓存于 {cache_time}]")
            else:
                print(f"📁 使用缓存: {stock_code} ({len(df)}行)")
            
            return df
            
        except Exception as e:
            print(f"⚠️  读取缓存失败: {e}")
            # 删除损坏的缓存
            try:
                cache_path.unlink()
                if cache_key in self.metadata:
                    del self.metadata[cache_key]
                    self._save_metadata()
            except:
                pass
            return None
    
    def set_prices(self, stock_code, df, start_date=None, end_date=None):
        """
        保存价格数据到缓存
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        df : DataFrame
            价格数据
        start_date : str, optional
            开始日期（如果None，从数据中提取）
        end_date : str, optional
            结束日期（如果None，从数据中提取）
        """
        if df is None or len(df) == 0:
            return
        
        try:
            # 验证数据格式
            if 'date' not in df.columns:
                print(f"⚠️  数据缺少date列，无法缓存")
                return
            
            # 从数据中提取日期范围
            if start_date is None:
                start_date = df['date'].iloc[0]
            if end_date is None:
                end_date = df['date'].iloc[-1]
            
            cache_path = self._get_cache_path(stock_code, start_date, end_date)
            cache_key = self._get_cache_key(stock_code, start_date, end_date)
            
            # 保存CSV
            df.to_csv(cache_path, index=False)
            
            # 更新元数据
            self.metadata[cache_key] = {
                'stock_code': stock_code,
                'start_date': start_date,
                'end_date': end_date,
                'rows': len(df),
                'cached_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'file_path': str(cache_path)
            }
            self._save_metadata()
            
            print(f"💾 已缓存: {stock_code} ({len(df)}行) → {cache_path.name}")
            
        except Exception as e:
            print(f"⚠️  保存缓存失败: {e}")
    
    def clear_cache(self, stock_code=None):
        """
        清除缓存
        
        Parameters:
        -----------
        stock_code : str, optional
            如果指定，只清除该股票的缓存；否则清除所有
        """
        if stock_code:
            # 清除特定股票的缓存
            removed = 0
            for cache_key in list(self.metadata.keys()):
                if self.metadata[cache_key]['stock_code'] == stock_code:
                    file_path = Path(self.metadata[cache_key]['file_path'])
                    if file_path.exists():
                        file_path.unlink()
                    del self.metadata[cache_key]
                    removed += 1
            
            if removed > 0:
                self._save_metadata()
                print(f"✅ 已清除 {stock_code} 的 {removed} 个缓存")
            else:
                print(f"⚠️  未找到 {stock_code} 的缓存")
        else:
            # 清除所有缓存
            count = 0
            for file in self.cache_dir.glob('*.csv'):
                file.unlink()
                count += 1
            
            self.metadata.clear()
            self._save_metadata()
            print(f"✅ 已清除所有缓存 ({count} 个文件)")
    
    def list_cache(self):
        """列出所有缓存"""
        if not self.metadata:
            print("📭 缓存为空")
            return
        
        print(f"\n{'='*70}")
        print(f"缓存列表 ({len(self.metadata)} 项)")
        print(f"{'='*70}")
        print(f"{'股票代码':<15} {'日期范围':<25} {'行数':<8} {'缓存时间':<20}")
        print(f"{'-'*70}")
        
        for cache_key, info in sorted(self.metadata.items()):
            stock = info['stock_code']
            date_range = f"{info['start_date']} ~ {info['end_date']}"
            rows = info['rows']
            cached_at = info['cached_at']
            print(f"{stock:<15} {date_range:<25} {rows:<8} {cached_at:<20}")
        
        print(f"{'='*70}\n")
    
    def get_cache_size(self):
        """获取缓存总大小"""
        total_size = 0
        for file in self.cache_dir.glob('*.csv'):
            total_size += file.stat().st_size
        
        # 转换为可读格式
        if total_size < 1024:
            return f"{total_size} B"
        elif total_size < 1024 * 1024:
            return f"{total_size / 1024:.2f} KB"
        else:
            return f"{total_size / (1024 * 1024):.2f} MB"


# 使用示例
if __name__ == '__main__':
    cache = DataCache()
    
    print("\n" + "="*70)
    print("数据缓存测试")
    print("="*70)
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'date': ['2025-01-20', '2025-01-21', '2025-01-22'],
        'open': [100.0, 101.0, 102.0],
        'high': [105.0, 106.0, 107.0],
        'low': [99.0, 100.0, 101.0],
        'close': [103.0, 104.0, 105.0],
        'volume': [1000000, 1100000, 1200000]
    })
    
    # 测试保存
    print("\n1. 测试保存缓存")
    cache.set_prices('TEST.STOCK', test_data, '2025-01-20', '2025-01-22')
    
    # 测试读取
    print("\n2. 测试读取缓存")
    cached_data = cache.get_prices('TEST.STOCK', '2025-01-20', '2025-01-22')
    if cached_data is not None:
        print(f"   读取成功: {len(cached_data)} 行")
        print(cached_data)
    
    # 列出缓存
    print("\n3. 列出所有缓存")
    cache.list_cache()
    
    # 缓存大小
    print(f"4. 缓存总大小: {cache.get_cache_size()}")
    
    # 清除测试缓存
    print("\n5. 清除测试缓存")
    cache.clear_cache('TEST.STOCK')
    
    print("\n✅ 测试完成\n")
