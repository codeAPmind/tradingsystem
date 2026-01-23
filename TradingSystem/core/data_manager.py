"""
统一数据管理器
自动识别美股/港股/A股，调用对应API
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
    """统一数据管理器"""
    
    def __init__(self):
        """初始化数据管理器"""
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
            # API密钥检查在_init_financial()中进行
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
            return
        
        if self.futu_fetcher is None:
            try:
                from data.futu_data import FutuDataFetcher
                self.futu_fetcher = FutuDataFetcher()
            except (ImportError, ModuleNotFoundError):
                self.futu_available = False
                return
        
        if not self.futu_connected:
            try:
                self.futu_fetcher.connect()
                self.futu_connected = True
            except Exception as e:
                print(f"❌ Futu连接失败: {e}")
                self.futu_connected = False
    
    def _init_financial(self):
        """初始化Financial Datasets API"""
        if not self.financial_available:
            return
        
        if self.financial_api is None:
            try:
                FinancialDatasetsAPI = self.FinancialDatasetsAPI
                self.financial_api = FinancialDatasetsAPI()
                # 检查API密钥是否配置
                if not self.financial_api.api_key:
                    print("⚠️  FINANCIAL_DATASETS_API_KEY未设置，美股数据功能不可用")
                    self.financial_available = False
                    self.financial_api = None
                else:
                    print("✅ FinancialDatasets API已初始化（API密钥已配置）")
            except Exception as e:
                print(f"⚠️  FinancialDatasets初始化失败: {e}")
                self.financial_available = False
                self.financial_api = None
    
    def _init_tushare(self):
        """初始化Tushare"""
        if self.tushare_available and self.tushare_fetcher is None:
            from data.tushare_data import TushareDataFetcher
            self.tushare_fetcher = TushareDataFetcher()
    
    def get_kline_data(
        self, 
        stock_code: str, 
        start_date: str, 
        end_date: str,
        use_cache: bool = True,
        force_update: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        获取K线数据（自动识别数据源）
        
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
        use_cache : bool
            是否使用缓存
        force_update : bool
            是否强制更新
        
        Returns:
        --------
        DataFrame : K线数据
            包含: date, open, high, low, close, volume
        """
        original_code = stock_code.strip()
        
        # 特殊处理：如果用户在回测里直接输入数字（常见于港股，例如 1797）
        # 4~5位数字优先按港股处理，自动补全为 HK.xxxxx
        if original_code.isdigit() and 4 <= len(original_code) <= 5:
            stock_code = f"HK.{int(original_code):05d}"
        else:
            stock_code = original_code
        
        market = get_market_type(stock_code)
        
        print(f"📊 获取 {stock_code} ({market}) K线数据...")
        print(f"   日期范围: {start_date} 至 {end_date}")
        
        # 先尝试从缓存加载
        if use_cache and not force_update:
            try:
                from utils.cache import DataCache
                cache = DataCache()
                cached_data = cache.get_prices(stock_code, start_date, end_date)
                if cached_data is not None:
                    return cached_data
            except (ImportError, ModuleNotFoundError, Exception) as e:
                # 缓存不可用时继续，不报错
                pass
        
        # 从API获取
        df = None
        
        if market == 'HK':
            # 港股 - 使用Futu
            self._init_futu()
            if self.futu_connected:
                df = self.futu_fetcher.get_history_kline(
                    stock_code, start_date, end_date
                )
        
        elif market == 'US':
            # 美股 - 使用Financial Datasets
            if not self.financial_available:
                print(f"❌ FinancialDatasets模块不可用，无法获取美股数据")
                return None
            self._init_financial()
            if self.financial_api is None:
                print(f"❌ FinancialDatasets API未初始化（可能缺少API密钥）")
                return None
            df = self.financial_api.get_stock_prices(
                stock_code, start_date, end_date
            )
        
        elif market == 'A':
            # A股 - 使用Tushare
            if self.tushare_available:
                self._init_tushare()
                df = self.tushare_fetcher.get_history_kline(
                    stock_code, start_date, end_date
                )
            else:
                print(f"❌ Tushare未安装，无法获取A股数据")
                return None
        
        # 保存到缓存
        if df is not None and use_cache:
            try:
                from utils.cache import DataCache
                cache = DataCache()
                cache.set_prices(stock_code, df)
            except (ImportError, ModuleNotFoundError, Exception):
                # 缓存不可用时继续，不报错
                pass
        
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
            self._init_futu()
            if self.futu_connected:
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
        
        if market == 'A' and self.tushare_available:
            self._init_tushare()
            return self.tushare_fetcher.get_stock_basic(stock_code)
        
        return None
    
    def disconnect(self):
        """断开所有连接"""
        if self.futu_connected and self.futu_fetcher:
            self.futu_fetcher.disconnect()
            self.futu_connected = False
        
        print("✅ 数据管理器已断开连接")


# 使用示例
if __name__ == '__main__':
    manager = DataManager()
    
    # 测试美股
    print("\n=== 测试美股 ===")
    df = manager.get_kline_data('TSLA', '2025-01-01', '2025-01-22')
    if df is not None:
        print(f"获取到 {len(df)} 条数据")
        print(df.head())
    
    # 测试港股
    print("\n=== 测试港股 ===")
    df = manager.get_kline_data('HK.01797', '2025-01-01', '2025-01-22')
    if df is not None:
        print(f"获取到 {len(df)} 条数据")
        print(df.head())
    
    # 测试A股
    print("\n=== 测试A股 ===")
    df = manager.get_kline_data('600519', '2025-01-01', '2025-01-22')
    if df is not None:
        print(f"获取到 {len(df)} 条数据")
        print(df.head())
    
    manager.disconnect()
