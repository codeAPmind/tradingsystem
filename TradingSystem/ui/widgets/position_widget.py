"""
增强版持仓面板
Enhanced Position Widget
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QLabel, QPushButton,
                             QGroupBox, QTableWidgetItem, QHeaderView,
                             QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor


class PositionWidget(QWidget):
    """增强版持仓面板"""
    
    # 信号
    close_position = pyqtSignal(str, int)  # 平仓信号（股票代码，数量）
    add_position = pyqtSignal(str)          # 加仓信号
    
    def __init__(self, trader_manager=None):
        super().__init__()
        self.trader_manager = trader_manager
        self.init_ui()
        
        # 定时刷新（每30秒）
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_positions)
        self.refresh_timer.start(30000)  # 30秒
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title = QLabel("📊 持仓管理")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(title)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_positions)
        title_layout.addWidget(refresh_btn)
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 持仓统计
        stats_group = QGroupBox("持仓统计")
        stats_layout = QHBoxLayout()
        
        self.total_cost_label = QLabel("总成本: $0.00")
        self.total_value_label = QLabel("总市值: $0.00")
        self.total_profit_label = QLabel("浮动盈亏: $0.00 (0.00%)")
        
        stats_layout.addWidget(self.total_cost_label)
        stats_layout.addWidget(self.total_value_label)
        stats_layout.addWidget(self.total_profit_label)
        stats_layout.addStretch()
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # 持仓列表表格
        self.position_table = QTableWidget()
        self.position_table.setColumnCount(10)
        self.position_table.setHorizontalHeaderLabels([
            '股票代码', '股票名称', '持仓数量', '可用数量',
            '成本价', '现价', '市值', '盈亏金额', '盈亏比例', '操作'
        ])
        
        # 自动调整列宽
        header = self.position_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 设置行高
        self.position_table.verticalHeader().setDefaultSectionSize(40)
        
        layout.addWidget(self.position_table)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("📤 导出持仓")
        export_btn.clicked.connect(self.export_positions)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 初始提示
        self.show_empty_message()
    
    def show_empty_message(self):
        """显示空持仓提示"""
        self.position_table.setRowCount(1)
        item = QTableWidgetItem("暂无持仓或未连接交易器")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_table.setSpan(0, 0, 1, 10)
        self.position_table.setItem(0, 0, item)
        
        # 重置统计
        self.total_cost_label.setText("总成本: $0.00")
        self.total_value_label.setText("总市值: $0.00")
        self.total_profit_label.setText("浮动盈亏: $0.00 (0.00%)")
        self.total_profit_label.setStyleSheet("color: gray;")
    
    def refresh_positions(self):
        """刷新持仓"""
        if not self.trader_manager:
            self.show_empty_message()
            return
        
        try:
            positions = self.trader_manager.get_all_positions()
            self.update_positions(positions)
        except Exception as e:
            print(f"刷新持仓失败: {e}")
            self.show_empty_message()
    
    def update_positions(self, positions):
        """
        更新持仓数据
        
        Parameters:
        -----------
        positions : list
            持仓列表
        """
        # 清空表格
        self.position_table.setRowCount(0)
        self.position_table.clearSpans()
        
        if not positions or len(positions) == 0:
            self.show_empty_message()
            return
        
        total_cost = 0
        total_value = 0
        
        for position in positions:
            row = self.position_table.rowCount()
            self.position_table.insertRow(row)
            
            # 提取数据（处理不同数据源）
            code = position.get('code', '')
            name = position.get('stock_name', '')
            qty = position.get('qty', 0)
            
            # 可用数量（不同API返回字段不同）
            available_qty = position.get('can_sell_qty', 
                           position.get('available_qty', qty))
            
            cost_price = position.get('cost_price', 0)
            
            # 现价（优先使用last_price）
            current_price = position.get('last_price', 
                           position.get('current_price', 
                           position.get('market_price', cost_price)))
            
            # 市值
            market_value = position.get('market_val', current_price * qty)
            
            # 盈亏
            profit = position.get('pl_val', market_value - cost_price * qty)
            
            # 盈亏比例
            if cost_price > 0 and qty > 0:
                profit_rate = position.get('pl_ratio', 
                             (profit / (cost_price * qty) * 100))
            else:
                profit_rate = 0
            
            # 货币符号
            currency = 'HK$' if code.startswith('HK.') else '$'
            
            # 填充表格
            self.position_table.setItem(row, 0, QTableWidgetItem(code))
            self.position_table.setItem(row, 1, QTableWidgetItem(name))
            self.position_table.setItem(row, 2, QTableWidgetItem(str(int(qty))))
            self.position_table.setItem(row, 3, QTableWidgetItem(str(int(available_qty))))
            self.position_table.setItem(row, 4, QTableWidgetItem(f"{currency}{cost_price:.2f}"))
            self.position_table.setItem(row, 5, QTableWidgetItem(f"{currency}{current_price:.2f}"))
            self.position_table.setItem(row, 6, QTableWidgetItem(f"{currency}{market_value:,.2f}"))
            
            # 盈亏金额
            profit_item = QTableWidgetItem(f"{currency}{profit:+,.2f}")
            profit_item.setForeground(QColor('green' if profit > 0 else 'red'))
            profit_item.setFont(profit_item.font())
            font = profit_item.font()
            font.setBold(True)
            profit_item.setFont(font)
            self.position_table.setItem(row, 7, profit_item)
            
            # 盈亏比例
            profit_rate_item = QTableWidgetItem(f"{profit_rate:+.2f}%")
            profit_rate_item.setForeground(QColor('green' if profit_rate > 0 else 'red'))
            font = profit_rate_item.font()
            font.setBold(True)
            profit_rate_item.setFont(font)
            self.position_table.setItem(row, 8, profit_rate_item)
            
            # 操作按钮
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            button_layout.setSpacing(4)
            
            close_btn = QPushButton("平仓")
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            close_btn.clicked.connect(
                lambda checked, c=code, q=int(available_qty): self.close_position.emit(c, q)
            )
            button_layout.addWidget(close_btn)
            
            add_btn = QPushButton("加仓")
            add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            add_btn.clicked.connect(
                lambda checked, c=code: self.add_position.emit(c)
            )
            button_layout.addWidget(add_btn)
            
            self.position_table.setCellWidget(row, 9, button_widget)
            
            # 统计
            total_cost += cost_price * qty
            total_value += market_value
        
        # 更新统计信息
        total_profit = total_value - total_cost
        profit_rate = (total_profit / total_cost * 100) if total_cost > 0 else 0
        
        self.total_cost_label.setText(f"总成本: ${total_cost:,.2f}")
        self.total_value_label.setText(f"总市值: ${total_value:,.2f}")
        
        profit_text = f"浮动盈亏: ${total_profit:+,.2f} ({profit_rate:+.2f}%)"
        self.total_profit_label.setText(profit_text)
        self.total_profit_label.setStyleSheet(
            f"color: {'green' if total_profit > 0 else 'red'}; font-weight: bold; font-size: 13px;"
        )
    
    def export_positions(self):
        """导出持仓"""
        QMessageBox.information(self, "提示", "导出功能开发中...\n将支持导出为CSV/Excel格式")
    
    def stopTimer(self):
        """停止定时器"""
        if self.refresh_timer:
            self.refresh_timer.stop()
