"""
统一数据管理器
自动识别美股/港股/A股，调用对应API
优先使用本地缓存
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd

# 确保导入当前项目的config模块
_current_dir = Path(__file__).parent.parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

from config.settings import get_market_type


class DataManager:
    """统一数据管理器（缓存优先）"""
    
    def __init__(self, use_cache=True):
        """
        初始化数据管理器
        
        Parameters:
        -----------
        use_cache : bool
            是否使用缓存（默认True）
        """
        self.use_cache = use_cache
        
        # 初始化缓存
        if use_cache:
            try:
                from data.data_cache import DataCache
                self.cache = DataCache()
                print("✅ 缓存系统已启用")
            except Exception as e:
                print(f"⚠️  缓存系统初始化失败: {e}")
                self.cache = None
                self.use_cache = False
        else:
            self.cache = None
        
        # 延迟导入，避免循环依赖
        try:
            from data.futu_data import FutuDataFetcher
            self.futu_available = True
        except (ImportError, ModuleNotFoundError):
            print("⚠️  Futu未安装，港股数据功能不可用")
            self.futu_available = False
        
        try:
            # 直接导入，避免通过data.__init__导入（可能触发futu导入）
            import importlib.util
            financial_path = Path(__file__).parent.parent / 'data' / 'financial_data.py'
            spec = importlib.util.spec_from_file_location("financial_data", financial_path)
            financial_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(financial_module)
            self.FinancialDatasetsAPI = financial_module.FinancialDatasetsAPI
            self.financial_available = True
        except Exception as e:
            # 如果直接导入失败，尝试常规导入
            try:
                from data.financial_data import FinancialDatasetsAPI
                self.FinancialDatasetsAPI = FinancialDatasetsAPI
                self.financial_available = True
            except Exception as e2:
                print(f"⚠️  FinancialDatasets模块导入失败: {e2}")
                self.financial_available = False
        
        try:
            from data.tushare_data import TushareDataFetcher
            self.tushare_available = True
        except (ImportError, ModuleNotFoundError):
            print("⚠️  Tushare未安装，A股数据功能不可用")
            self.tushare_available = False
        
        # 初始化数据源
        self.futu_fetcher = None
        self.financial_api = None
        self.tushare_fetcher = None
        
        # 连接状态
        self.futu_connected = False
        
        print("✅ 数据管理器已初始化")
    
    def _init_futu(self):
        """初始化Futu连接"""
        if not self.futu_available:
            return False
        
        if self.futu_fetcher is None:
            try:
                from data.futu_data import FutuDataFetcher
                self.futu_fetcher = FutuDataFetcher()
            except (ImportError, ModuleNotFoundError):
                self.futu_available = False
                return False
        
        if not self.futu_connected:
            try:
                self.futu_fetcher.connect()
                self.futu_connected = True
            except Exception as e:
                print(f"❌ Futu连接失败: {e}")
                self.futu_connected = False
                return False
        
        return True
    
    def _init_financial(self):
        """初始化Financial Datasets API"""
        if not self.financial_available:
            return False
        
        if self.financial_api is None:
            try:
                FinancialDatasetsAPI = self.FinancialDatasetsAPI
                self.financial_api = FinancialDatasetsAPI()
                # 检查API密钥是否配置
                if not self.financial_api.api_key:
                    print("⚠️  FINANCIAL_DATASETS_API_KEY未设置，美股数据功能不可用")
                    self.financial_available = False
                    self.financial_api = None
                    return False
            except Exception as e:
                print(f"⚠️  FinancialDatasets初始化失败: {e}")
                self.financial_available = False
                self.financial_api = None
                return False
        
        return True
    
    def _init_tushare(self):
        """初始化Tushare"""
        if self.tushare_available and self.tushare_fetcher is None:
            from data.tushare_data import TushareDataFetcher
            self.tushare_fetcher = TushareDataFetcher()
            return True
        return self.tushare_available
    
    def get_kline_data(
        self, 
        stock_code: str, 
        start_date: str, 
        end_date: str,
        force_update: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        获取K线数据（缓存优先策略）
        
        Parameters:
        -----------
        stock_code : str
            股票代码
            - 港股: HK.01797, HK.00700
            - 美股: TSLA, NVDA, AAPL
            - A股: 600519, 000001
        start_date : str
            开始日期 'YYYY-MM-DD'
        end_date : str
            结束日期 'YYYY-MM-DD'
        force_update : bool
            是否强制从API更新（跳过缓存）
        
        Returns:
        --------
        DataFrame : K线数据
            包含: date, open, high, low, close, volume
            date 列为字符串格式 'YYYY-MM-DD'
        """
        original_code = stock_code.strip()
        
        # 特殊处理：如果用户直接输入数字（常见于港股）
        # 4~5位数字优先按港股处理，自动补全为 HK.xxxxx
        if original_code.isdigit() and 4 <= len(original_code) <= 5:
            stock_code = f"HK.{int(original_code):05d}"
            print(f"🔄 [Manager] 自动格式化: {original_code} → {stock_code}")
        else:
            stock_code = original_code
        
        market = get_market_type(stock_code)
        
        print(f"\n📊 [Manager] 获取 {stock_code} ({market}) K线数据")
        print(f"   日期范围: {start_date} ~ {end_date}")
        print(f"   缓存: {'启用' if self.use_cache and not force_update else '禁用'}")
        
        # === 步骤1: 优先从缓存加载 ===
        if self.use_cache and not force_update and self.cache:
            print(f"   步骤1: 尝试从缓存加载...")
            try:
                cached_data = self.cache.load(stock_code, start_date, end_date)
                if cached_data is not None:
                    print(f"   ✅ 使用缓存数据 ({len(cached_data)}行)")
                    return cached_data
                else:
                    print(f"   ⚪ 缓存未命中")
            except Exception as e:
                print(f"   ⚠️  缓存读取失败: {e}")
        
        # === 步骤2: 从API获取 ===
        print(f"   步骤2: 从API获取数据...")
        df = None
        
        if market == 'HK':
            # 港股 - 使用Futu
            if not self._init_futu():
                print(f"   ❌ Futu初始化失败")
                print(f"   请确保: 1) Futu OpenD已启动 2) 已登录账户")
                return None
            
            df = self.futu_fetcher.get_history_kline(
                stock_code, start_date, end_date
            )
        
        elif market == 'US':
            # 美股 - 使用Financial Datasets
            if not self._init_financial():
                print(f"   ❌ FinancialDatasets初始化失败")
                return None
            
            df = self.financial_api.get_stock_prices(
                stock_code, start_date, end_date
            )
        
        elif market == 'A':
            # A股 - 使用Tushare
            if not self._init_tushare():
                print(f"   ❌ Tushare初始化失败")
                return None
            
            df = self.tushare_fetcher.get_history_kline(
                stock_code, start_date, end_date
            )
        
        # === 步骤3: 保存到缓存 ===
        if df is not None and self.use_cache and self.cache:
            print(f"   步骤3: 保存到缓存...")
            try:
                self.cache.save(stock_code, start_date, end_date, df)
            except Exception as e:
                print(f"   ⚠️  缓存保存失败: {e}")
        
        if df is not None:
            print(f"   ✅ 数据获取完成 ({len(df)}行)\n")
        else:
            print(f"   ❌ 数据获取失败\n")
        
        return df
    
    def get_current_price(self, stock_code: str) -> Optional[float]:
        """
        获取当前价格
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        
        Returns:
        --------
        float : 当前价格
        """
        market = get_market_type(stock_code)
        
        if market == 'HK':
            # 港股实时价格
            if self._init_futu():
                return self.futu_fetcher.get_realtime_price(stock_code)
        
        elif market == 'US':
            # 美股使用最新收盘价
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            df = self.get_kline_data(stock_code, start_date, end_date)
            if df is not None and len(df) > 0:
                return float(df['close'].iloc[-1])
        
        elif market == 'A':
            # A股实时价格（使用东方财富）
            try:
                from data.eastmoney_data import EastMoneyDataFetcher
                em_fetcher = EastMoneyDataFetcher()
                quote = em_fetcher.get_realtime_price(stock_code)
                if quote:
                    return quote['price']
            except Exception as e:
                print(f"⚠️  获取A股实时价格失败: {e}")
        
        return None
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict]:
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
        market = get_market_type(stock_code)
        
        if market == 'A' and self._init_tushare():
            return self.tushare_fetcher.get_stock_basic(stock_code)
        
        return None
    
    def list_cache(self):
        """列出所有缓存"""
        if self.cache:
            self.cache.list_cache()
        else:
            print("⚠️  缓存未启用")
    
    def clear_cache(self, stock_code=None):
        """
        清除缓存
        
        Parameters:
        -----------
        stock_code : str, optional
            如果指定，只清除该股票的缓存；否则清除所有
        """
        if self.cache:
            self.cache.clear_cache(stock_code)
        else:
            print("⚠️  缓存未启用")
    
    def get_cache_size(self):
        """获取缓存大小"""
        if self.cache:
            return self.cache.get_cache_size()
        return "0 B"
    
    def disconnect(self):
        """断开所有连接"""
        if self.futu_connected and self.futu_fetcher:
            self.futu_fetcher.disconnect()
            self.futu_connected = False
        
        print("✅ 数据管理器已断开连接")


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*80)
    print("数据管理器测试（缓存优先）")
    print("="*80)
    
    manager = DataManager(use_cache=True)
    
    # 测试1: 第一次获取港股数据（从API）
    print("\n【测试1】第一次获取港股数据（从API）")
    print("="*80)
    df1 = manager.get_kline_data('HK.01797', '2024-12-01', '2025-01-27')
    if df1 is not None:
        print(f"✅ 成功: {len(df1)} 行")
        print(df1.head())
    
    # 测试2: 第二次获取同样数据（从缓存）
    print("\n【测试2】第二次获取同样数据（应该从缓存）")
    print("="*80)
    df2 = manager.get_kline_data('HK.01797', '2024-12-01', '2025-01-27')
    if df2 is not None:
        print(f"✅ 成功: {len(df2)} 行")
    
    # 测试3: 强制更新（跳过缓存）
    print("\n【测试3】强制更新（跳过缓存）")
    print("="*80)
    df3 = manager.get_kline_data('HK.01797', '2024-12-01', '2025-01-27', force_update=True)
    if df3 is not None:
        print(f"✅ 成功: {len(df3)} 行")
    
    # 测试4: 列出所有缓存
    print("\n【测试4】列出所有缓存")
    print("="*80)
    manager.list_cache()
    
    # 测试5: 缓存大小
    print(f"【测试5】缓存大小: {manager.get_cache_size()}")
    
    manager.disconnect()
    print("\n✅ 测试完成\n")
