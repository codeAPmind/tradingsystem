"""
股票列表组件
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QPushButton,
                             QHBoxLayout, QInputDialog, QLabel)
from PyQt6.QtCore import pyqtSignal, Qt
from config import get_stock_display_name


class StockListWidget(QWidget):
    """股票列表组件"""
    
    stock_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # 默认股票列表
        self.default_stocks = ['TSLA', 'NVDA', 'AAPL', 'HK.01797', '600519']
        self.load_default_stocks()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("自选股")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # 股票列表
        self.stock_list = QListWidget()
        self.stock_list.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.stock_list)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("新增")
        self.add_btn.clicked.connect(self.add_stock)
        button_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("删除")
        self.remove_btn.clicked.connect(self.remove_stock)
        button_layout.addWidget(self.remove_btn)
        
        layout.addLayout(button_layout)
    
    def load_default_stocks(self):
        """加载默认股票"""
        for stock_code in self.default_stocks:
            display_name = get_stock_display_name(stock_code)
            self.stock_list.addItem(f"{stock_code} - {display_name}")
    
    def on_item_clicked(self, item):
        """股票项点击"""
        text = item.text()
        stock_code = text.split(' - ')[0]
        self.stock_selected.emit(stock_code)
    
    def add_stock(self):
        """添加股票"""
        stock_code, ok = QInputDialog.getText(
            self,
            "添加股票",
            "请输入股票代码:\n(美股: TSLA, 港股: HK.01797, A股: 600519)"
        )
        
        if ok and stock_code:
            stock_code = stock_code.strip().upper()
            display_name = get_stock_display_name(stock_code)
            self.stock_list.addItem(f"{stock_code} - {display_name}")
    
    def remove_stock(self):
        """删除股票"""
        current_item = self.stock_list.currentItem()
        if current_item:
            self.stock_list.takeItem(self.stock_list.row(current_item))
