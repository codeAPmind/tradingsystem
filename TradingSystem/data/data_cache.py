# data/data_cache.py
"""
本地数据缓存
优先使用缓存，减少API调用
"""
import pandas as pd
import os
import json
from datetime import datetime
from pathlib import Path


class DataCache:
    """本地数据缓存管理器"""
    
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
        self.metadata_file = self.cache_dir / 'metadata.json'
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
    
    def get_cache_path(self, stock_code, start_date, end_date):
        """
        生成缓存文件路径
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        start_date : str
            开始日期
        end_date : str
            结束日期
        
        Returns:
        --------
        Path : 缓存文件路径
        """
        # 清理股票代码中的特殊字符
        clean_code = stock_code.replace('.', '_')
        filename = f"{clean_code}_{start_date}_{end_date}.csv"
        return self.cache_dir / filename
    
    def load(self, stock_code, start_date, end_date):
        """
        加载缓存数据
        
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
        cache_path = self.get_cache_path(stock_code, start_date, end_date)
        cache_key = f"{stock_code}_{start_date}_{end_date}"
        
        if not cache_path.exists():
            return None
        
        try:
            # 读取CSV（不使用索引）
            df = pd.read_csv(cache_path)
            
            # 验证数据格式
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                print(f"⚠️  缓存数据格式错误（缺少必需列）: {cache_key}")
                return None
            
            # 确保 date 列是字符串格式
            if df['date'].dtype != 'object':
                df['date'] = df['date'].astype(str)
            
            # 获取缓存时间
            if cache_key in self.metadata:
                cache_time = self.metadata[cache_key].get('cached_at', '')
                print(f"📁 [Cache] 使用缓存: {stock_code} ({len(df)}行) [缓存于 {cache_time}]")
            else:
                print(f"📁 [Cache] 使用缓存: {stock_code} ({len(df)}行)")
            
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
    
    def save(self, stock_code, start_date, end_date, df):
        """
        保存数据到缓存
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        start_date : str
            开始日期
        end_date : str
            结束日期
        df : DataFrame
            数据
        """
        if df is None or len(df) == 0:
            return
        
        try:
            cache_path = self.get_cache_path(stock_code, start_date, end_date)
            cache_key = f"{stock_code}_{start_date}_{end_date}"
            
            # 验证数据格式
            if 'date' not in df.columns:
                print(f"⚠️  数据缺少date列，无法缓存")
                return
            
            # 保存CSV（不使用索引）
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
            
            print(f"💾 [Cache] 已缓存: {stock_code} ({len(df)}行) → {cache_path.name}")
            
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
        
        print(f"\n{'='*80}")
        print(f"缓存列表 ({len(self.metadata)} 项)")
        print(f"{'='*80}")
        print(f"{'股票代码':<15} {'日期范围':<30} {'行数':<8} {'缓存时间':<20}")
        print(f"{'-'*80}")
        
        for cache_key, info in sorted(self.metadata.items()):
            stock = info['stock_code']
            date_range = f"{info['start_date']} ~ {info['end_date']}"
            rows = info['rows']
            cached_at = info['cached_at']
            print(f"{stock:<15} {date_range:<30} {rows:<8} {cached_at:<20}")
        
        print(f"{'='*80}\n")
    
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


# 完整使用示例
if __name__ == '__main__':
    print("\n" + "="*80)
    print("数据缓存测试")
    print("="*80)
    
    # 创建缓存管理器
    cache = DataCache()
    
    # 测试数据
    test_data = pd.DataFrame({
        'date': ['2025-01-20', '2025-01-21', '2025-01-22'],
        'open': [100.0, 101.0, 102.0],
        'high': [105.0, 106.0, 107.0],
        'low': [99.0, 100.0, 101.0],
        'close': [103.0, 104.0, 105.0],
        'volume': [1000000, 1100000, 1200000]
    })
    
    # 1. 保存缓存
    print("\n【测试1】保存缓存")
    print("-"*80)
    cache.save('TEST.STOCK', '2025-01-20', '2025-01-22', test_data)
    
    # 2. 读取缓存
    print("\n【测试2】读取缓存")
    print("-"*80)
    cached = cache.load('TEST.STOCK', '2025-01-20', '2025-01-22')
    if cached is not None:
        print(f"✅ 读取成功: {len(cached)} 行")
        print(cached)
    
    # 3. 列出缓存
    print("\n【测试3】列出所有缓存")
    cache.list_cache()
    
    # 4. 缓存大小
    print(f"【测试4】缓存大小: {cache.get_cache_size()}")
    
    # 5. 清除缓存
    print("\n【测试5】清除测试缓存")
    print("-"*80)
    cache.clear_cache('TEST.STOCK')
    
    print("\n✅ 测试完成\n")
