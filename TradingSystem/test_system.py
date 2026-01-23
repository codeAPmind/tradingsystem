"""
TradingSystem 测试脚本
测试数据获取功能
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.data_manager import DataManager
from config import get_market_type, get_stock_display_name


def test_market_detection():
    """测试市场识别"""
    print("\n" + "="*70)
    print("测试市场识别")
    print("="*70)
    
    test_codes = [
        'TSLA',
        'NVDA',
        'HK.01797',
        'HK.00700',
        '600519',
        '000001',
    ]
    
    for code in test_codes:
        market = get_market_type(code)
        name = get_stock_display_name(code)
        print(f"{code:12} -> 市场: {market:4} | 名称: {name}")


def test_data_fetching():
    """测试数据获取"""
    print("\n" + "="*70)
    print("测试数据获取")
    print("="*70)
    
    manager = DataManager()
    
    test_stocks = [
        ('TSLA', '美股 Tesla'),
        ('HK.01797', '港股 东方甄选'),
        ('600519', 'A股 贵州茅台'),
    ]
    
    for code, name in test_stocks:
        print(f"\n--- 测试 {name} ({code}) ---")
        
        try:
            df = manager.get_kline_data(
                code, 
                '2025-01-15', 
                '2025-01-22',
                use_cache=True
            )
            
            if df is not None:
                print(f"✅ 成功获取 {len(df)} 条数据")
                print(f"\n最新数据:")
                print(df.tail(3))
                
                # 测试获取当前价格
                price = manager.get_current_price(code)
                if price:
                    print(f"\n当前价格: {price:.2f}")
            else:
                print(f"❌ 获取数据失败")
        
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    manager.disconnect()


def test_cache_system():
    """测试缓存系统"""
    print("\n" + "="*70)
    print("测试缓存系统")
    print("="*70)
    
    try:
        from utils.cache import DataCache
        cache = DataCache()
        print("✅ 缓存系统初始化成功")
        
        # 测试缓存信息
        print("\n缓存目录:", cache.cache_dir)
        
    except Exception as e:
        print(f"⚠️  缓存系统不可用: {e}")


def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("TradingSystem 功能测试")
    print("="*70)
    
    # 测试1: 市场识别
    test_market_detection()
    
    # 测试2: 缓存系统
    test_cache_system()
    
    # 测试3: 数据获取
    test_data_fetching()
    
    print("\n" + "="*70)
    print("测试完成！")
    print("="*70)


if __name__ == '__main__':
    main()
