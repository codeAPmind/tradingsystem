"""
数据模块初始化
"""
# 延迟导入，避免futu模块不存在时影响其他模块
try:
    from .futu_data import FutuDataFetcher
except (ImportError, ModuleNotFoundError):
    FutuDataFetcher = None

from .financial_data import FinancialDatasetsAPI

try:
    from .tushare_data import TushareDataFetcher
except (ImportError, ModuleNotFoundError):
    TushareDataFetcher = None

try:
    from .eastmoney_data import EastMoneyDataFetcher
except (ImportError, ModuleNotFoundError):
    EastMoneyDataFetcher = None

__all__ = [
    'FutuDataFetcher',
    'FinancialDatasetsAPI',
    'TushareDataFetcher',
    'EastMoneyDataFetcher',
]
