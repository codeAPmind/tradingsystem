"""
UI组件
"""
from .stock_list import StockListWidget
from .chart_widget import ChartWidget
from .signal_panel import SignalPanel
from .position_widget import PositionWidget
from .news_widget import NewsWidget
from .backtest_widget import BacktestWidget

__all__ = [
    'StockListWidget',
    'ChartWidget',
    'SignalPanel',
    'PositionWidget',
    'NewsWidget',
    'BacktestWidget'
]
