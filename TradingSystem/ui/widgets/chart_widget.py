"""
K线图表组件
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
import pandas as pd
from typing import Optional


class ChartWidget(QWidget):
    """K线图表组件"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.data = None
        self.stock_code = None
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        self.title_label = QLabel("K线图")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(self.title_label)
        
        # 图表区域（暂时用标签代替，后续可以用pyqtgraph实现）
        self.chart_label = QLabel("图表区域\n(使用pyqtgraph实现)")
        self.chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_label.setStyleSheet("""
            background-color: #1e1e1e;
            border: 1px solid #3d3d3d;
            min-height: 400px;
        """)
        layout.addWidget(self.chart_label)
    
    def update_data(self, df: pd.DataFrame, stock_code: str):
        """
        更新数据
        
        Parameters:
        -----------
        df : DataFrame
            K线数据
        stock_code : str
            股票代码
        """
        self.data = df
        self.stock_code = stock_code
        
        # 更新标题
        from config import get_stock_display_name
        display_name = get_stock_display_name(stock_code)
        self.title_label.setText(f"K线图 - {stock_code} ({display_name})")
        
        # 更新图表（暂时显示数据摘要）
        if df is not None and len(df) > 0:
            latest = df.iloc[-1]
            info = f"""
            最新数据:
            日期: {latest.get('date', 'N/A')}
            开盘: {latest.get('open', 0):.2f}
            最高: {latest.get('high', 0):.2f}
            最低: {latest.get('low', 0):.2f}
            收盘: {latest.get('close', 0):.2f}
            成交量: {latest.get('volume', 0):,.0f}
            
            数据点数: {len(df)}
            """
            self.chart_label.setText(info)
        else:
            self.chart_label.setText("无数据")
