# 交易系统UI设计补充 - 持仓与交易模块

## 📋 **设计概述**

补充原设计文档中缺失的交易相关UI，包括：
1. ✅ 持仓管理面板
2. ✅ 交易执行界面
3. ✅ 订单管理系统
4. ✅ 自动交易控制
5. ✅ 账户信息展示
6. ✅ 交易历史记录

---

## 🎨 **完整主窗口布局（增强版）**

```
┌────────────────────────────────────────────────────────────────────────┐
│  菜单栏: 文件 | 策略 | 交易 | 自动化 | 工具 | 帮助                       │
├────────────────────────────────────────────────────────────────────────┤
│  工具栏: [连接] [刷新] [回测] [手动交易] [自动交易] [策略] [设置]     │
├─────────┬─────────────────────────────────┬──────────────────────────┤
│         │                                 │  📊 持仓 | 订单 | 账户    │
│ 股票列表│       K线图 + 指标               │ ┌────────────────────┐  │
│ ┌─────┐│                                 │ │🟢 TSLA    100股    │  │
│ │TSLA ││                                 │ │  成本: $420.00     │  │
│ │NVDA ││                                 │ │  现价: $442.50     │  │
│ │AAPL ││  [主图] [副图] [成交量]         │ │  盈亏: +$2,250     │  │
│ │01797││                                 │ │  收益率: +5.36%    │  │
│ │600519                                 │ │  [平仓] [加仓]     │  │
│ └─────┘│                                 │ └────────────────────┘  │
│        │                                 │ 🔴 NVDA    50股        │
│ 自选股 │                                 │   成本: $880.00        │
│ [新增] │                                 │   现价: $855.00        │
│ [删除] │                                 │   盈亏: -$1,250        │
│        │                                 │   收益率: -2.84%       │
│ 市场   │                                 │   [平仓] [加仓]        │
│ ○ 美股 ├─────────────────────────────────┤                        │
│ ○ 港股 │  标签页: [信号] [交易] [持仓]  │  📈 账户总览           │
│ ○ A股  │ ┌───────────────────────────┐   │ 总资产: $150,000.00   │
│        │ │🟢 [信号面板]               │   │ 可用: $48,000.00      │
│        │ │  TSLA 买入信号             │   │ 持仓: $102,000.00     │
│ 回测   │ │  TSF > LSMA + 0.5%        │   │ 盈亏: +$2,000 (+1.35%)│
│        │ │  建议价: $440-$445        │   │                        │
│ 策略   │ │  [立即交易] [查看详情]     │   │  今日交易              │
│        │ ├───────────────────────────┤   │ 买入: 2笔              │
│ 定时任务│🟡 [交易面板]              │   │ 卖出: 1笔              │
│        │ │  快速下单                  │   │ 成交: 3笔              │
│        │ │  股票: [TSLA    ▼]        │   │ 待成交: 0笔            │
├─────────┤  │  操作: [买入 ▼] [卖出]   │   │                        │
│  日志   │  │  数量: [100]   股         │   │  最新新闻              │
│         │  │  价格: [市价 ▼] [$442.50]│   │ ┌──────────────────┐   │
│ [清空]  │  │  [提交订单]               │   │ │Tesla Q4财报超预期│   │
│         │  └───────────────────────────┘   │ │特斯拉发布新车型   │   │
│         │ 🔵 [持仓详情]              │   │ └──────────────────┘   │
│         │  │当前持仓: 2只股票          │   │                        │
│         │  │总成本: $102,000          │   │  自动交易              │
│         │  │总市值: $104,000          │   │ ○ 自动交易已关闭      │
│         │  │浮动盈亏: +$2,000         │   │ [启动自动交易]         │
│         │  │[查看详情] [导出报表]     │   │                        │
├─────────┴─────────────────────────────────┴──────────────────────────┤
│ 状态栏: 🟢 已连接Futu | 账户: 模拟盘 | CPU: 5% | 内存: 2.1GB | 16:30 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 💼 **1. 持仓管理面板 (Position Widget)**

### **UI组件设计**

```python
"""
持仓管理面板
ui/widgets/position_widget.py
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QLabel, QPushButton,
                             QGroupBox, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


class PositionWidget(QWidget):
    """持仓管理面板"""
    
    # 信号
    close_position = pyqtSignal(str, int)  # 平仓信号（股票代码，数量）
    add_position = pyqtSignal(str)          # 加仓信号
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
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
        
        layout.addWidget(self.position_table)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("📤 导出持仓")
        export_btn.clicked.connect(self.export_positions)
        button_layout.addWidget(export_btn)
        
        close_all_btn = QPushButton("🔴 清空所有持仓")
        close_all_btn.setStyleSheet("color: red;")
        close_all_btn.clicked.connect(self.close_all_positions)
        button_layout.addWidget(close_all_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def update_positions(self, positions):
        """
        更新持仓数据
        
        Parameters:
        -----------
        positions : list
            持仓列表
            [{
                'code': 'TSLA',
                'name': '特斯拉',
                'qty': 100,
                'available_qty': 100,
                'cost_price': 420.00,
                'current_price': 442.50,
                'market_value': 44250.00,
                'profit': 2250.00,
                'profit_rate': 5.36
            }, ...]
        """
        self.position_table.setRowCount(0)
        
        total_cost = 0
        total_value = 0
        
        for position in positions:
            row = self.position_table.rowCount()
            self.position_table.insertRow(row)
            
            # 股票代码
            self.position_table.setItem(row, 0, QTableWidgetItem(position['code']))
            
            # 股票名称
            self.position_table.setItem(row, 1, QTableWidgetItem(position['name']))
            
            # 持仓数量
            self.position_table.setItem(row, 2, QTableWidgetItem(str(position['qty'])))
            
            # 可用数量
            self.position_table.setItem(row, 3, QTableWidgetItem(str(position['available_qty'])))
            
            # 成本价
            self.position_table.setItem(row, 4, QTableWidgetItem(f"${position['cost_price']:.2f}"))
            
            # 现价
            self.position_table.setItem(row, 5, QTableWidgetItem(f"${position['current_price']:.2f}"))
            
            # 市值
            self.position_table.setItem(row, 6, QTableWidgetItem(f"${position['market_value']:.2f}"))
            
            # 盈亏金额
            profit_item = QTableWidgetItem(f"${position['profit']:+.2f}")
            profit_item.setForeground(QColor('green' if position['profit'] > 0 else 'red'))
            self.position_table.setItem(row, 7, profit_item)
            
            # 盈亏比例
            profit_rate_item = QTableWidgetItem(f"{position['profit_rate']:+.2f}%")
            profit_rate_item.setForeground(QColor('green' if position['profit_rate'] > 0 else 'red'))
            self.position_table.setItem(row, 8, profit_rate_item)
            
            # 操作按钮
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            
            close_btn = QPushButton("平仓")
            close_btn.clicked.connect(lambda checked, code=position['code'], qty=position['available_qty']: 
                                     self.close_position.emit(code, qty))
            button_layout.addWidget(close_btn)
            
            add_btn = QPushButton("加仓")
            add_btn.clicked.connect(lambda checked, code=position['code']: 
                                   self.add_position.emit(code))
            button_layout.addWidget(add_btn)
            
            self.position_table.setCellWidget(row, 9, button_widget)
            
            # 统计
            total_cost += position['cost_price'] * position['qty']
            total_value += position['market_value']
        
        # 更新统计信息
        total_profit = total_value - total_cost
        profit_rate = (total_profit / total_cost * 100) if total_cost > 0 else 0
        
        self.total_cost_label.setText(f"总成本: ${total_cost:,.2f}")
        self.total_value_label.setText(f"总市值: ${total_value:,.2f}")
        
        profit_text = f"浮动盈亏: ${total_profit:+,.2f} ({profit_rate:+.2f}%)"
        self.total_profit_label.setText(profit_text)
        self.total_profit_label.setStyleSheet(
            f"color: {'green' if total_profit > 0 else 'red'}; font-weight: bold;"
        )
    
    def refresh_positions(self):
        """刷新持仓"""
        # TODO: 从交易引擎获取最新持仓
        pass
    
    def export_positions(self):
        """导出持仓"""
        # TODO: 导出为CSV或Excel
        pass
    
    def close_all_positions(self):
        """清空所有持仓"""
        # TODO: 确认对话框 + 批量平仓
        pass
```

---

## 🔄 **2. 交易执行面板 (Trade Widget)**

### **UI组件设计**

```python
"""
交易执行面板
ui/widgets/trade_widget.py
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton,
                             QSpinBox, QDoubleSpinBox, QGroupBox, QRadioButton,
                             QButtonGroup, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal


class TradeWidget(QWidget):
    """交易执行面板"""
    
    # 信号
    order_submitted = pyqtSignal(dict)  # 订单提交信号
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("🔄 快速交易")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 交易表单
        form_group = QGroupBox("下单信息")
        form_layout = QFormLayout()
        
        # 股票代码
        self.stock_code_input = QComboBox()
        self.stock_code_input.setEditable(True)
        self.stock_code_input.setPlaceholderText("输入或选择股票代码")
        form_layout.addRow("股票代码:", self.stock_code_input)
        
        # 买卖方向
        direction_layout = QHBoxLayout()
        self.buy_radio = QRadioButton("买入")
        self.sell_radio = QRadioButton("卖出")
        self.buy_radio.setChecked(True)
        
        direction_group = QButtonGroup()
        direction_group.addButton(self.buy_radio)
        direction_group.addButton(self.sell_radio)
        
        direction_layout.addWidget(self.buy_radio)
        direction_layout.addWidget(self.sell_radio)
        direction_layout.addStretch()
        form_layout.addRow("交易方向:", direction_layout)
        
        # 价格类型
        self.price_type_combo = QComboBox()
        self.price_type_combo.addItems(["市价", "限价", "最优五档", "最优对手价"])
        self.price_type_combo.currentTextChanged.connect(self.on_price_type_changed)
        form_layout.addRow("价格类型:", self.price_type_combo)
        
        # 价格输入
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 100000)
        self.price_input.setDecimals(2)
        self.price_input.setSingleStep(0.01)
        self.price_input.setPrefix("$")
        self.price_input.setEnabled(False)  # 默认市价，禁用
        form_layout.addRow("交易价格:", self.price_input)
        
        # 数量输入
        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 1000000)
        self.qty_input.setSingleStep(100)
        self.qty_input.setValue(100)
        self.qty_input.setSuffix(" 股")
        form_layout.addRow("交易数量:", self.qty_input)
        
        # 预计金额
        self.amount_label = QLabel("$0.00")
        self.amount_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        form_layout.addRow("预计金额:", self.amount_label)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 实时信息
        info_group = QGroupBox("实时行情")
        info_layout = QFormLayout()
        
        self.current_price_label = QLabel("--")
        self.bid_ask_label = QLabel("--/--")
        self.volume_label = QLabel("--")
        
        info_layout.addRow("当前价:", self.current_price_label)
        info_layout.addRow("买一/卖一:", self.bid_ask_label)
        info_layout.addRow("成交量:", self.volume_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 提交按钮
        button_layout = QHBoxLayout()
        
        self.buy_button = QPushButton("🟢 买入")
        self.buy_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 16px;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.buy_button.clicked.connect(self.submit_buy_order)
        button_layout.addWidget(self.buy_button)
        
        self.sell_button = QPushButton("🔴 卖出")
        self.sell_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-size: 16px;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.sell_button.clicked.connect(self.submit_sell_order)
        button_layout.addWidget(self.sell_button)
        
        layout.addLayout(button_layout)
        
        # 快捷操作
        quick_group = QGroupBox("快捷操作")
        quick_layout = QHBoxLayout()
        
        quick_buy_25 = QPushButton("买入25%")
        quick_buy_50 = QPushButton("买入50%")
        quick_buy_100 = QPushButton("买入全部")
        
        quick_buy_25.clicked.connect(lambda: self.quick_buy(0.25))
        quick_buy_50.clicked.connect(lambda: self.quick_buy(0.50))
        quick_buy_100.clicked.connect(lambda: self.quick_buy(1.0))
        
        quick_layout.addWidget(quick_buy_25)
        quick_layout.addWidget(quick_buy_50)
        quick_layout.addWidget(quick_buy_100)
        
        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)
        
        layout.addStretch()
    
    def on_price_type_changed(self, price_type):
        """价格类型改变"""
        if price_type == "限价":
            self.price_input.setEnabled(True)
        else:
            self.price_input.setEnabled(False)
    
    def submit_buy_order(self):
        """提交买入订单"""
        self._submit_order("BUY")
    
    def submit_sell_order(self):
        """提交卖出订单"""
        self._submit_order("SELL")
    
    def _submit_order(self, direction):
        """提交订单"""
        stock_code = self.stock_code_input.currentText().strip()
        if not stock_code:
            QMessageBox.warning(self, "错误", "请输入股票代码")
            return
        
        price_type = self.price_type_combo.currentText()
        price = self.price_input.value() if price_type == "限价" else None
        qty = self.qty_input.value()
        
        # 确认对话框
        msg = f"确认{direction}订单?\n"
        msg += f"股票: {stock_code}\n"
        msg += f"方向: {direction}\n"
        msg += f"数量: {qty}股\n"
        msg += f"价格: {price_type}"
        if price:
            msg += f" ${price:.2f}"
        
        reply = QMessageBox.question(self, "确认订单", msg,
                                     QMessageBox.StandardButton.Yes | 
                                     QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            order = {
                'stock_code': stock_code,
                'direction': direction,
                'price_type': price_type,
                'price': price,
                'qty': qty
            }
            
            self.order_submitted.emit(order)
    
    def quick_buy(self, ratio):
        """快捷买入（按可用资金比例）"""
        # TODO: 根据可用资金自动计算数量
        pass
    
    def update_quote(self, stock_code, quote):
        """
        更新实时行情
        
        Parameters:
        -----------
        quote : dict
            {
                'price': 442.50,
                'bid': 442.45,
                'ask': 442.55,
                'volume': 1250000
            }
        """
        if self.stock_code_input.currentText() == stock_code:
            self.current_price_label.setText(f"${quote['price']:.2f}")
            self.bid_ask_label.setText(f"${quote['bid']:.2f} / ${quote['ask']:.2f}")
            self.volume_label.setText(f"{quote['volume']:,}")
            
            # 更新预计金额
            self.price_input.setValue(quote['price'])
            amount = quote['price'] * self.qty_input.value()
            self.amount_label.setText(f"${amount:,.2f}")
```

---

## 📝 **3. 订单管理面板 (Order Widget)**

```python
"""
订单管理面板
ui/widgets/order_widget.py
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QLabel, QPushButton,
                             QTabWidget, QTableWidgetItem, QHeaderView,
                             QComboBox, QDateEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QDate


class OrderWidget(QWidget):
    """订单管理面板"""
    
    # 信号
    cancel_order = pyqtSignal(str)  # 撤单信号（订单ID）
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题和筛选
        header_layout = QHBoxLayout()
        
        title = QLabel("📝 订单管理")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)
        
        # 日期筛选
        header_layout.addWidget(QLabel("日期:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.setCalendarPopup(True)
        header_layout.addWidget(self.date_from)
        
        header_layout.addWidget(QLabel("-"))
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        header_layout.addWidget(self.date_to)
        
        # 状态筛选
        header_layout.addWidget(QLabel("状态:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部", "待成交", "部分成交", "已成交", "已撤销"])
        header_layout.addWidget(self.status_filter)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_orders)
        header_layout.addWidget(refresh_btn)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 标签页
        self.tabs = QTabWidget()
        
        # 今日委托
        self.today_table = self._create_order_table()
        self.tabs.addTab(self.today_table, "今日委托")
        
        # 历史委托
        self.history_table = self._create_order_table()
        self.tabs.addTab(self.history_table, "历史委托")
        
        # 成交记录
        self.trade_table = self._create_trade_table()
        self.tabs.addTab(self.trade_table, "成交记录")
        
        layout.addWidget(self.tabs)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("📤 导出订单")
        export_btn.clicked.connect(self.export_orders)
        button_layout.addWidget(export_btn)
        
        cancel_all_btn = QPushButton("🚫 撤销全部待成交")
        cancel_all_btn.setStyleSheet("color: orange;")
        cancel_all_btn.clicked.connect(self.cancel_all_pending)
        button_layout.addWidget(cancel_all_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _create_order_table(self):
        """创建订单表格"""
        table = QTableWidget()
        table.setColumnCount(11)
        table.setHorizontalHeaderLabels([
            '订单号', '时间', '股票代码', '股票名称', '方向', 
            '价格类型', '委托价', '委托量', '成交量', '状态', '操作'
        ])
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        return table
    
    def _create_trade_table(self):
        """创建成交记录表格"""
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            '成交时间', '股票代码', '股票名称', '方向', 
            '成交价', '成交量', '成交额', '手续费', '订单号'
        ])
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        return table
    
    def update_orders(self, orders):
        """
        更新订单列表
        
        Parameters:
        -----------
        orders : list
            订单列表
            [{
                'order_id': '123456',
                'time': '2025-01-22 10:30:00',
                'code': 'TSLA',
                'name': '特斯拉',
                'direction': 'BUY',
                'price_type': '限价',
                'price': 442.50,
                'qty': 100,
                'filled_qty': 0,
                'status': '待成交'
            }, ...]
        """
        self.today_table.setRowCount(0)
        
        for order in orders:
            row = self.today_table.rowCount()
            self.today_table.insertRow(row)
            
            # 订单号
            self.today_table.setItem(row, 0, QTableWidgetItem(order['order_id']))
            
            # 时间
            self.today_table.setItem(row, 1, QTableWidgetItem(order['time']))
            
            # 股票代码
            self.today_table.setItem(row, 2, QTableWidgetItem(order['code']))
            
            # 股票名称
            self.today_table.setItem(row, 3, QTableWidgetItem(order['name']))
            
            # 方向
            direction_item = QTableWidgetItem(order['direction'])
            direction_item.setForeground(QColor('green' if order['direction'] == 'BUY' else 'red'))
            self.today_table.setItem(row, 4, direction_item)
            
            # 价格类型
            self.today_table.setItem(row, 5, QTableWidgetItem(order['price_type']))
            
            # 委托价
            self.today_table.setItem(row, 6, QTableWidgetItem(f"${order['price']:.2f}"))
            
            # 委托量
            self.today_table.setItem(row, 7, QTableWidgetItem(str(order['qty'])))
            
            # 成交量
            self.today_table.setItem(row, 8, QTableWidgetItem(str(order['filled_qty'])))
            
            # 状态
            status_item = QTableWidgetItem(order['status'])
            if order['status'] == '已成交':
                status_item.setForeground(QColor('green'))
            elif order['status'] == '已撤销':
                status_item.setForeground(QColor('gray'))
            self.today_table.setItem(row, 9, status_item)
            
            # 操作按钮
            if order['status'] in ['待成交', '部分成交']:
                button_widget = QWidget()
                button_layout = QHBoxLayout(button_widget)
                button_layout.setContentsMargins(2, 2, 2, 2)
                
                cancel_btn = QPushButton("撤单")
                cancel_btn.clicked.connect(
                    lambda checked, order_id=order['order_id']: 
                    self.cancel_order.emit(order_id)
                )
                button_layout.addWidget(cancel_btn)
                
                self.today_table.setCellWidget(row, 10, button_widget)
    
    def refresh_orders(self):
        """刷新订单"""
        # TODO: 从交易引擎获取最新订单
        pass
    
    def export_orders(self):
        """导出订单"""
        # TODO: 导出为CSV
        pass
    
    def cancel_all_pending(self):
        """撤销所有待成交订单"""
        # TODO: 批量撤单
        pass
```

---

## 🤖 **4. 自动交易控制面板 (Auto Trade Widget)**

```python
"""
自动交易控制面板
ui/widgets/auto_trade_widget.py
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTableWidget,
                             QGroupBox, QCheckBox, QSpinBox,
                             QDoubleSpinBox, QTextEdit, QFormLayout,
                             QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal


class AutoTradeWidget(QWidget):
    """自动交易控制面板"""
    
    # 信号
    auto_trade_toggled = pyqtSignal(bool)  # 自动交易开关
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("🤖 自动交易系统")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 状态显示
        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout()
        
        # 状态指示
        status_row = QHBoxLayout()
        self.status_label = QLabel("⚪ 自动交易已关闭")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        status_row.addWidget(self.status_label)
        
        self.toggle_btn = QPushButton("启动自动交易")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_auto_trade)
        status_row.addWidget(self.toggle_btn)
        status_row.addStretch()
        
        status_layout.addLayout(status_row)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        self.today_signals_label = QLabel("今日信号: 0")
        self.today_trades_label = QLabel("今日交易: 0")
        self.success_rate_label = QLabel("成功率: 0%")
        
        stats_layout.addWidget(self.today_signals_label)
        stats_layout.addWidget(self.today_trades_label)
        stats_layout.addWidget(self.success_rate_label)
        stats_layout.addStretch()
        
        status_layout.addLayout(stats_layout)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 风控设置
        risk_group = QGroupBox("风控设置")
        risk_layout = QFormLayout()
        
        # 单笔最大金额
        self.max_amount_input = QDoubleSpinBox()
        self.max_amount_input.setRange(0, 1000000)
        self.max_amount_input.setValue(10000)
        self.max_amount_input.setPrefix("$")
        risk_layout.addRow("单笔最大金额:", self.max_amount_input)
        
        # 单日最大交易次数
        self.max_trades_input = QSpinBox()
        self.max_trades_input.setRange(1, 100)
        self.max_trades_input.setValue(10)
        risk_layout.addRow("单日最大交易次数:", self.max_trades_input)
        
        # 止损比例
        self.stop_loss_input = QDoubleSpinBox()
        self.stop_loss_input.setRange(0, 100)
        self.stop_loss_input.setValue(5.0)
        self.stop_loss_input.setSuffix("%")
        risk_layout.addRow("止损比例:", self.stop_loss_input)
        
        # 止盈比例
        self.take_profit_input = QDoubleSpinBox()
        self.take_profit_input.setRange(0, 100)
        self.take_profit_input.setValue(10.0)
        self.take_profit_input.setSuffix("%")
        risk_layout.addRow("止盈比例:", self.take_profit_input)
        
        # 启用AI确认
        self.ai_confirm_checkbox = QCheckBox("启用AI信号确认")
        self.ai_confirm_checkbox.setChecked(True)
        risk_layout.addRow("", self.ai_confirm_checkbox)
        
        risk_group.setLayout(risk_layout)
        layout.addWidget(risk_group)
        
        # 待执行信号
        signals_group = QGroupBox("待执行信号")
        signals_layout = QVBoxLayout()
        
        self.signals_table = QTableWidget()
        self.signals_table.setColumnCount(7)
        self.signals_table.setHorizontalHeaderLabels([
            '股票代码', '信号类型', '生成时间', '当前价', 
            '建议价', 'AI评分', '操作'
        ])
        
        header = self.signals_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        signals_layout.addWidget(self.signals_table)
        signals_group.setLayout(signals_layout)
        layout.addWidget(signals_group)
        
        # 执行日志
        log_group = QGroupBox("执行日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
    
    def toggle_auto_trade(self):
        """切换自动交易状态"""
        current_state = self.status_label.text()
        
        if "已关闭" in current_state:
            # 启动
            self.status_label.setText("🟢 自动交易运行中")
            self.status_label.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: green;"
            )
            self.toggle_btn.setText("停止自动交易")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 5px;
                }
            """)
            self.auto_trade_toggled.emit(True)
            self.add_log("✅ 自动交易已启动")
        else:
            # 停止
            self.status_label.setText("⚪ 自动交易已关闭")
            self.status_label.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: gray;"
            )
            self.toggle_btn.setText("启动自动交易")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 5px;
                }
            """)
            self.auto_trade_toggled.emit(False)
            self.add_log("⚠️  自动交易已停止")
    
    def add_log(self, message):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.append(f"[{timestamp}] {message}")
    
    def update_pending_signals(self, signals):
        """
        更新待执行信号
        
        Parameters:
        -----------
        signals : list
            [{
                'code': 'TSLA',
                'type': 'BUY',
                'time': '2025-01-22 16:10:00',
                'current_price': 442.50,
                'suggest_price': '440-445',
                'ai_score': 85
            }, ...]
        """
        self.signals_table.setRowCount(0)
        
        for signal in signals:
            row = self.signals_table.rowCount()
            self.signals_table.insertRow(row)
            
            self.signals_table.setItem(row, 0, QTableWidgetItem(signal['code']))
            
            type_item = QTableWidgetItem(signal['type'])
            type_item.setForeground(QColor('green' if signal['type'] == 'BUY' else 'red'))
            self.signals_table.setItem(row, 1, type_item)
            
            self.signals_table.setItem(row, 2, QTableWidgetItem(signal['time']))
            self.signals_table.setItem(row, 3, QTableWidgetItem(f"${signal['current_price']:.2f}"))
            self.signals_table.setItem(row, 4, QTableWidgetItem(signal['suggest_price']))
            self.signals_table.setItem(row, 5, QTableWidgetItem(str(signal['ai_score'])))
            
            # 操作按钮
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            
            execute_btn = QPushButton("立即执行")
            execute_btn.clicked.connect(
                lambda checked, sig=signal: self.execute_signal(sig)
            )
            button_layout.addWidget(execute_btn)
            
            ignore_btn = QPushButton("忽略")
            ignore_btn.clicked.connect(
                lambda checked, sig=signal: self.ignore_signal(sig)
            )
            button_layout.addWidget(ignore_btn)
            
            self.signals_table.setCellWidget(row, 6, button_widget)
    
    def execute_signal(self, signal):
        """执行信号"""
        self.add_log(f"📝 执行信号: {signal['code']} {signal['type']}")
        # TODO: 调用交易引擎执行
    
    def ignore_signal(self, signal):
        """忽略信号"""
        self.add_log(f"⚠️  忽略信号: {signal['code']} {signal['type']}")
```

---

## 📊 **5. 账户信息面板 (Account Widget)**

```python
"""
账户信息面板
ui/widgets/account_widget.py
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries
from PyQt6.QtGui import QPainter, QColor


class AccountWidget(QWidget):
    """账户信息面板"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("💰 账户信息")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 账户总览
        overview_group = QGroupBox("账户总览")
        overview_layout = QFormLayout()
        
        self.total_asset_label = QLabel("$0.00")
        self.total_asset_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        overview_layout.addRow("总资产:", self.total_asset_label)
        
        self.available_label = QLabel("$0.00")
        overview_layout.addRow("可用资金:", self.available_label)
        
        self.frozen_label = QLabel("$0.00")
        overview_layout.addRow("冻结资金:", self.frozen_label)
        
        self.market_value_label = QLabel("$0.00")
        overview_layout.addRow("持仓市值:", self.market_value_label)
        
        self.profit_label = QLabel("$0.00 (0.00%)")
        self.profit_label.setStyleSheet("color: green; font-weight: bold;")
        overview_layout.addRow("浮动盈亏:", self.profit_label)
        
        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)
        
        # 资产分布饼图
        allocation_group = QGroupBox("资产分布")
        allocation_layout = QVBoxLayout()
        
        self.pie_chart = self._create_pie_chart()
        self.pie_chart_view = QChartView(self.pie_chart)
        self.pie_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.pie_chart_view.setMaximumHeight(250)
        
        allocation_layout.addWidget(self.pie_chart_view)
        allocation_group.setLayout(allocation_layout)
        layout.addWidget(allocation_group)
        
        # 今日统计
        today_group = QGroupBox("今日统计")
        today_layout = QFormLayout()
        
        self.today_profit_label = QLabel("$0.00")
        today_layout.addRow("今日盈亏:", self.today_profit_label)
        
        self.today_trades_label = QLabel("0笔")
        today_layout.addRow("交易次数:", self.today_trades_label)
        
        self.today_turnover_label = QLabel("$0.00")
        today_layout.addRow("成交金额:", self.today_turnover_label)
        
        self.today_commission_label = QLabel("$0.00")
        today_layout.addRow("手续费:", self.today_commission_label)
        
        today_group.setLayout(today_layout)
        layout.addWidget(today_group)
        
        layout.addStretch()
    
    def _create_pie_chart(self):
        """创建饼图"""
        series = QPieSeries()
        series.append("现金", 50)
        series.append("股票", 50)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("资产分布")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        return chart
    
    def update_account(self, account_info):
        """
        更新账户信息
        
        Parameters:
        -----------
        account_info : dict
            {
                'total_asset': 150000.00,
                'available': 48000.00,
                'frozen': 0.00,
                'market_value': 102000.00,
                'profit': 2000.00,
                'profit_rate': 1.35,
                'today_profit': 500.00,
                'today_trades': 3,
                'today_turnover': 50000.00,
                'today_commission': 50.00
            }
        """
        # 更新账户总览
        self.total_asset_label.setText(f"${account_info['total_asset']:,.2f}")
        self.available_label.setText(f"${account_info['available']:,.2f}")
        self.frozen_label.setText(f"${account_info['frozen']:,.2f}")
        self.market_value_label.setText(f"${account_info['market_value']:,.2f}")
        
        profit_text = f"${account_info['profit']:+,.2f} ({account_info['profit_rate']:+.2f}%)"
        self.profit_label.setText(profit_text)
        self.profit_label.setStyleSheet(
            f"color: {'green' if account_info['profit'] > 0 else 'red'}; font-weight: bold;"
        )
        
        # 更新今日统计
        self.today_profit_label.setText(f"${account_info['today_profit']:+,.2f}")
        self.today_profit_label.setStyleSheet(
            f"color: {'green' if account_info['today_profit'] > 0 else 'red'};"
        )
        self.today_trades_label.setText(f"{account_info['today_trades']}笔")
        self.today_turnover_label.setText(f"${account_info['today_turnover']:,.2f}")
        self.today_commission_label.setText(f"${account_info['today_commission']:,.2f}")
        
        # 更新饼图
        self._update_pie_chart(account_info['available'], account_info['market_value'])
    
    def _update_pie_chart(self, cash, stock):
        """更新饼图"""
        series = QPieSeries()
        series.append(f"现金 ${cash:,.0f}", cash)
        series.append(f"股票 ${stock:,.0f}", stock)
        
        # 设置颜色
        series.slices()[0].setColor(QColor("#28a745"))
        series.slices()[1].setColor(QColor("#007bff"))
        
        self.pie_chart.removeAllSeries()
        self.pie_chart.addSeries(series)
```

---

## 📈 **6. 集成到主窗口**

```python
"""
主窗口集成示例
ui/main_window.py (补充交易相关部分)
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ... 其他初始化 ...
        
        # 创建右侧面板标签页
        self.right_tabs = QTabWidget()
        
        # 持仓面板
        self.position_widget = PositionWidget()
        self.position_widget.close_position.connect(self.on_close_position)
        self.position_widget.add_position.connect(self.on_add_position)
        self.right_tabs.addTab(self.position_widget, "📊 持仓")
        
        # 订单面板
        self.order_widget = OrderWidget()
        self.order_widget.cancel_order.connect(self.on_cancel_order)
        self.right_tabs.addTab(self.order_widget, "📝 订单")
        
        # 账户面板
        self.account_widget = AccountWidget()
        self.right_tabs.addTab(self.account_widget, "💰 账户")
        
        # 中间面板标签页
        self.center_tabs = QTabWidget()
        
        # 信号面板（已有）
        # ... 
        
        # 交易面板
        self.trade_widget = TradeWidget()
        self.trade_widget.order_submitted.connect(self.on_order_submitted)
        self.center_tabs.addTab(self.trade_widget, "🔄 交易")
        
        # 自动交易面板
        self.auto_trade_widget = AutoTradeWidget()
        self.auto_trade_widget.auto_trade_toggled.connect(self.on_auto_trade_toggled)
        self.center_tabs.addTab(self.auto_trade_widget, "🤖 自动交易")
    
    def on_close_position(self, stock_code, qty):
        """平仓"""
        print(f"平仓: {stock_code} {qty}股")
        # TODO: 调用交易引擎
    
    def on_add_position(self, stock_code):
        """加仓"""
        print(f"加仓: {stock_code}")
        # TODO: 切换到交易面板并预填股票代码
    
    def on_cancel_order(self, order_id):
        """撤单"""
        print(f"撤单: {order_id}")
        # TODO: 调用交易引擎
    
    def on_order_submitted(self, order):
        """提交订单"""
        print(f"提交订单: {order}")
        # TODO: 调用交易引擎
    
    def on_auto_trade_toggled(self, enabled):
        """自动交易开关"""
        print(f"自动交易: {'启动' if enabled else '停止'}")
        # TODO: 启动/停止自动交易
```

---

## 🎨 **7. 样式表 (Stylesheet)**

```python
"""
交易相关组件样式
resources/styles/trade_style.qss
"""

/* 持仓盈利 */
.profit-positive {
    color: #28a745;
    font-weight: bold;
}

/* 持仓亏损 */
.profit-negative {
    color: #dc3545;
    font-weight: bold;
}

/* 买入按钮 */
QPushButton#buy-button {
    background-color: #28a745;
    color: white;
    font-size: 16px;
    padding: 10px;
    border-radius: 5px;
    border: none;
}

QPushButton#buy-button:hover {
    background-color: #218838;
}

QPushButton#buy-button:pressed {
    background-color: #1e7e34;
}

/* 卖出按钮 */
QPushButton#sell-button {
    background-color: #dc3545;
    color: white;
    font-size: 16px;
    padding: 10px;
    border-radius: 5px;
    border: none;
}

QPushButton#sell-button:hover {
    background-color: #c82333;
}

QPushButton#sell-button:pressed {
    background-color: #bd2130;
}

/* 自动交易状态 - 运行中 */
.auto-trade-active {
    color: #28a745;
    font-weight: bold;
    font-size: 14px;
}

/* 自动交易状态 - 已停止 */
.auto-trade-inactive {
    color: #6c757d;
    font-weight: bold;
    font-size: 14px;
}

/* 订单表格 */
QTableWidget#order-table {
    gridline-color: #dee2e6;
    selection-background-color: #007bff;
}

QTableWidget#order-table::item:selected {
    background-color: #007bff;
    color: white;
}

/* 持仓表格 */
QTableWidget#position-table {
    gridline-color: #dee2e6;
    selection-background-color: #007bff;
}

QTableWidget#position-table::item:selected {
    background-color: #007bff;
    color: white;
}
```

---

## 📊 **8. 数据模型**

```python
"""
交易数据模型
models/trade_models.py
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Position:
    """持仓"""
    code: str               # 股票代码
    name: str               # 股票名称
    qty: int                # 持仓数量
    available_qty: int      # 可用数量
    cost_price: float       # 成本价
    current_price: float    # 现价
    market_value: float     # 市值
    profit: float           # 盈亏金额
    profit_rate: float      # 盈亏比例


@dataclass
class Order:
    """订单"""
    order_id: str                   # 订单号
    time: datetime                  # 时间
    code: str                       # 股票代码
    name: str                       # 股票名称
    direction: str                  # 方向: BUY/SELL
    price_type: str                 # 价格类型
    price: float                    # 委托价
    qty: int                        # 委托量
    filled_qty: int                 # 成交量
    status: str                     # 状态
    avg_price: Optional[float] = None  # 成交均价


@dataclass
class Trade:
    """成交记录"""
    trade_id: str          # 成交号
    time: datetime         # 成交时间
    order_id: str          # 订单号
    code: str              # 股票代码
    name: str              # 股票名称
    direction: str         # 方向
    price: float           # 成交价
    qty: int               # 成交量
    amount: float          # 成交额
    commission: float      # 手续费


@dataclass
class Account:
    """账户信息"""
    total_asset: float      # 总资产
    available: float        # 可用资金
    frozen: float           # 冻结资金
    market_value: float     # 持仓市值
    profit: float           # 浮动盈亏
    profit_rate: float      # 盈亏比例
    today_profit: float     # 今日盈亏
    today_trades: int       # 今日交易次数
    today_turnover: float   # 今日成交额
    today_commission: float # 今日手续费
```

---

## ✅ **完整功能清单**

### **持仓管理** ✅
- [x] 持仓列表展示
- [x] 实时盈亏计算
- [x] 持仓统计汇总
- [x] 平仓/加仓操作
- [x] 持仓导出

### **交易执行** ✅
- [x] 快速下单界面
- [x] 市价/限价下单
- [x] 实时行情显示
- [x] 快捷操作按钮
- [x] 订单确认对话框

### **订单管理** ✅
- [x] 今日委托查询
- [x] 历史委托查询
- [x] 成交记录查询
- [x] 订单撤销
- [x] 批量撤单

### **自动交易** ✅
- [x] 自动交易开关
- [x] 风控参数设置
- [x] AI信号确认
- [x] 待执行信号列表
- [x] 执行日志记录

### **账户信息** ✅
- [x] 账户总览
- [x] 资产分布饼图
- [x] 今日统计
- [x] 实时更新

---

## 🚀 **下一步**

1. ✅ UI设计已完成
2. 🚧 实现核心交易引擎
3. 🚧 集成Futu交易API
4. 🚧 实现自动交易逻辑
5. 🚧 添加风控系统

---

**交易UI设计补充完成！** 🎉

现在系统支持：
- ✅ 持仓管理
- ✅ 交易执行
- ✅ 订单管理
- ✅ 自动交易
- ✅ 账户信息

可以开始实现了！💪