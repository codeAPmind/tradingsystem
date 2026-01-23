"""
Futu数据获取器
支持港股数据获取
"""
import sys
from pathlib import Path

# 复用现有的Futu数据模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'futu_backtest_trader'))

try:
    from data.futu_data import FutuDataFetcher as _FutuDataFetcher
    
    class FutuDataFetcher(_FutuDataFetcher):
        """
        Futu数据获取器（继承现有实现）
        """
        pass

except ImportError as e:
    print(f"⚠️  无法导入Futu数据模块: {e}")
    print("   请确保 futu_backtest_trader/data/futu_data.py 存在")
    
    # 提供一个占位类
    class FutuDataFetcher:
        def __init__(self, *args, **kwargs):
            raise ImportError("Futu数据模块不可用")


# 使用示例
if __name__ == '__main__':
    fetcher = FutuDataFetcher()
    fetcher.connect()
    
    # 获取东方甄选数据
    df = fetcher.get_history_kline('HK.01797', '2025-01-01', '2025-01-22')
    if df is not None:
        print(f"获取到 {len(df)} 条数据")
        print(df.head())
    
    fetcher.disconnect()
