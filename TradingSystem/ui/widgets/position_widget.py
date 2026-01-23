"""
持仓组件
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt


class PositionWidget(QWidget):
    """持仓组件"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("持仓信息")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # 账户总览
        account_label = QLabel("账户总览")
        account_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(account_label)
        
        self.total_asset_label = QLabel("总资产: $0.00")
        layout.addWidget(self.total_asset_label)
        
        self.available_label = QLabel("可用资金: $0.00")
        layout.addWidget(self.available_label)
        
        self.position_value_label = QLabel("持仓市值: $0.00")
        layout.addWidget(self.position_value_label)
        
        self.profit_label = QLabel("总盈亏: $0.00 (0.00%)")
        layout.addWidget(self.profit_label)
        
        # 持仓列表
        positions_label = QLabel("持仓列表")
        positions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(positions_label)
        
        self.position_table = QTableWidget()
        self.position_table.setColumnCount(5)
        self.position_table.setHorizontalHeaderLabels(['股票', '数量', '成本价', '当前价', '盈亏'])
        self.position_table.setColumnWidth(0, 80)
        self.position_table.setColumnWidth(1, 60)
        self.position_table.setColumnWidth(2, 70)
        self.position_table.setColumnWidth(3, 70)
        self.position_table.setColumnWidth(4, 100)
        layout.addWidget(self.position_table)
        
        # 初始化数据（示例）
        self.update_demo_data()
    
    def update_demo_data(self):
        """更新示例数据"""
        self.total_asset_label.setText("总资产: $100,000.00")
        self.available_label.setText("可用资金: $50,000.00")
        self.position_value_label.setText("持仓市值: $50,000.00")
        self.profit_label.setText("总盈亏: $2,500.00 (+5.00%)")
        
        # 示例持仓
        positions = [
            ('TSLA', 100, 420.0, 441.0, 2100.0, 5.0),
            ('NVDA', 50, 500.0, 520.0, 1000.0, 4.0),
        ]
        
        self.position_table.setRowCount(len(positions))
        for i, (stock, qty, cost, current, profit, profit_pct) in enumerate(positions):
            self.position_table.setItem(i, 0, QTableWidgetItem(stock))
            self.position_table.setItem(i, 1, QTableWidgetItem(str(qty)))
            self.position_table.setItem(i, 2, QTableWidgetItem(f"${cost:.2f}"))
            self.position_table.setItem(i, 3, QTableWidgetItem(f"${current:.2f}"))
            
            profit_item = QTableWidgetItem(f"${profit:.2f} ({profit_pct:+.2f}%)")
            if profit >= 0:
                profit_item.setForeground(Qt.GlobalColor.green)
            else:
                profit_item.setForeground(Qt.GlobalColor.red)
            self.position_table.setItem(i, 4, profit_item)
