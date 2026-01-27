"""
交易执行面板
Trade Widget - 快速下单界面
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QComboBox, QPushButton,
                             QSpinBox, QDoubleSpinBox, QGroupBox, QRadioButton,
                             QButtonGroup, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal

try:
    from futu import OrderType
except ImportError:
    print("⚠️  未安装futu-api，部分功能可能不可用")
    # 创建模拟的OrderType
    class OrderType:
        NORMAL = 0
        MARKET = 1


class TradeWidget(QWidget):
    """交易执行面板"""
    
    # 信号
    order_submitted = pyqtSignal(dict)  # 订单提交信号
    
    def __init__(self, trader_manager=None):
        super().__init__()
        self.trader_manager = trader_manager
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
        self.stock_code_input.setPlaceholderText("输入股票代码 (如TSLA或HK.01797)")
        self.stock_code_input.currentTextChanged.connect(self.on_stock_changed)
        form_layout.addRow("股票代码:", self.stock_code_input)
        
        # 添加常用股票
        self.stock_code_input.addItems([
            'TSLA', 'NVDA', 'AAPL', 'MSFT', 'GOOGL',
            'HK.01797', 'HK.00700', 'HK.09988'
        ])
        
        # 买卖方向
        direction_layout = QHBoxLayout()
        self.buy_radio = QRadioButton("买入")
        self.sell_radio = QRadioButton("卖出")
        self.buy_radio.setChecked(True)
        self.buy_radio.setStyleSheet("color: green; font-weight: bold;")
        self.sell_radio.setStyleSheet("color: red; font-weight: bold;")
        
        direction_group = QButtonGroup()
        direction_group.addButton(self.buy_radio)
        direction_group.addButton(self.sell_radio)
        
        direction_layout.addWidget(self.buy_radio)
        direction_layout.addWidget(self.sell_radio)
        direction_layout.addStretch()
        form_layout.addRow("交易方向:", direction_layout)
        
        # 价格类型
        self.price_type_combo = QComboBox()
        self.price_type_combo.addItems(["限价单", "市价单"])
        self.price_type_combo.currentTextChanged.connect(self.on_price_type_changed)
        form_layout.addRow("价格类型:", self.price_type_combo)
        
        # 价格输入
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 100000)
        self.price_input.setDecimals(2)
        self.price_input.setSingleStep(0.01)
        self.price_input.setPrefix("$")
        self.price_input.valueChanged.connect(self.update_amount)
        form_layout.addRow("交易价格:", self.price_input)
        
        # 数量输入
        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 1000000)
        self.qty_input.setSingleStep(100)
        self.qty_input.setValue(100)
        self.qty_input.valueChanged.connect(self.update_amount)
        form_layout.addRow("交易数量:", self.qty_input)
        
        # 预计金额
        self.amount_label = QLabel("$0.00")
        self.amount_label.setStyleSheet("font-size: 14px; font-weight: bold; color: blue;")
        form_layout.addRow("预计金额:", self.amount_label)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 实时行情
        info_group = QGroupBox("实时行情")
        info_layout = QFormLayout()
        
        self.current_price_label = QLabel("--")
        self.change_label = QLabel("--")
        self.volume_label = QLabel("--")
        
        info_layout.addRow("当前价:", self.current_price_label)
        info_layout.addRow("涨跌幅:", self.change_label)
        info_layout.addRow("成交量:", self.volume_label)
        
        refresh_btn = QPushButton("🔄 刷新行情")
        refresh_btn.clicked.connect(self.refresh_quote)
        info_layout.addRow("", refresh_btn)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 提交按钮
        button_layout = QHBoxLayout()
        
        self.submit_button = QPushButton("📝 提交订单")
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-size: 16px;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        self.submit_button.clicked.connect(self.submit_order)
        button_layout.addWidget(self.submit_button)
        
        layout.addLayout(button_layout)
        
        # 提示信息
        tip_label = QLabel("💡 提示: 港股100股起，美股1股起")
        tip_label.setStyleSheet("color: gray; font-size: 11px; margin-top: 10px;")
        layout.addWidget(tip_label)
        
        layout.addStretch()
    
    def on_stock_changed(self, stock_code):
        """股票代码变化"""
        if not stock_code:
            return
        
        # 根据市场调整数量步长
        if stock_code.startswith('HK.'):
            self.qty_input.setSingleStep(100)
            self.qty_input.setMinimum(100)
            self.price_input.setPrefix("HK$")
        else:
            self.qty_input.setSingleStep(1)
            self.qty_input.setMinimum(1)
            self.price_input.setPrefix("$")
        
        # 刷新行情
        self.refresh_quote()
    
    def on_price_type_changed(self, price_type):
        """价格类型变化"""
        if price_type == "限价单":
            self.price_input.setEnabled(True)
        else:
            self.price_input.setEnabled(False)
            self.price_input.setValue(0)
    
    def refresh_quote(self):
        """刷新行情"""
        stock_code = self.stock_code_input.currentText().strip()
        if not stock_code:
            return
        
        if not self.trader_manager:
            self.current_price_label.setText("未连接交易器")
            return
        
        try:
            # 获取当前价格
            price = self.trader_manager.get_current_price(stock_code)
            if price:
                prefix = "HK$" if stock_code.startswith('HK.') else "$"
                self.current_price_label.setText(f"{prefix}{price:.2f}")
                self.price_input.setValue(price)
                self.update_amount()
                
                # 获取详细行情
                snapshot = self.trader_manager.get_market_snapshot(stock_code)
                if snapshot is not None:
                    change_rate = snapshot.get('change_rate', 0)
                    color = 'green' if change_rate >= 0 else 'red'
                    self.change_label.setText(f"{change_rate:+.2f}%")
                    self.change_label.setStyleSheet(f"color: {color}; font-weight: bold;")
                    
                    volume = snapshot.get('volume', 0)
                    self.volume_label.setText(f"{volume:,.0f}")
            else:
                self.current_price_label.setText("获取失败")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"刷新行情失败: {e}")
            self.current_price_label.setText("错误")
    
    def update_amount(self):
        """更新预计金额"""
        price = self.price_input.value()
        qty = self.qty_input.value()
        amount = price * qty
        
        stock_code = self.stock_code_input.currentText().strip()
        prefix = "HK$" if stock_code.startswith('HK.') else "$"
        
        self.amount_label.setText(f"{prefix}{amount:,.2f}")
    
    def submit_order(self):
        """提交订单"""
        stock_code = self.stock_code_input.currentText().strip()
        if not stock_code:
            QMessageBox.warning(self, "错误", "请输入股票代码")
            return
        
        if not self.trader_manager:
            QMessageBox.warning(self, "错误", "未连接交易器")
            return
        
        direction = 'BUY' if self.buy_radio.isChecked() else 'SELL'
        price_type = self.price_type_combo.currentText()
        price = self.price_input.value()
        qty = self.qty_input.value()
        
        # 港股数量检查
        if stock_code.startswith('HK.') and (qty < 100 or qty % 100 != 0):
            QMessageBox.warning(self, "错误", "港股数量必须>=100且是100的整数倍")
            return
        
        # 市价单价格检查
        if price_type == "市价单":
            price = 0
        
        # 确认对话框
        currency = "HK$" if stock_code.startswith('HK.') else "$"
        msg = f"确认{direction}订单?\n\n"
        msg += f"股票: {stock_code}\n"
        msg += f"方向: {direction}\n"
        msg += f"数量: {qty}股"
        if stock_code.startswith('HK.'):
            msg += f" ({qty//100}手)"
        msg += f"\n价格: {price_type}"
        if price_type == "限价单":
            msg += f" {currency}{price:.2f}"
        msg += f"\n\n预计金额: {currency}{price * qty if price > 0 else '市价'}{'（约）' if price_type == '市价单' else ''}"
        
        reply = QMessageBox.question(
            self, "确认订单", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 确定订单类型
                order_type = OrderType.MARKET if price_type == "市价单" else OrderType.NORMAL
                
                # 提交订单
                if direction == 'BUY':
                    result = self.trader_manager.buy(stock_code, price, qty, order_type)
                else:
                    result = self.trader_manager.sell(stock_code, price, qty, order_type)
                
                if result is not None:
                    QMessageBox.information(self, "成功", "订单提交成功！\n请在订单面板查看")
                    
                    # 发送信号
                    order = {
                        'stock_code': stock_code,
                        'direction': direction,
                        'price_type': price_type,
                        'price': price,
                        'qty': qty
                    }
                    self.order_submitted.emit(order)
                else:
                    QMessageBox.warning(self, "失败", "订单提交失败\n请查看控制台日志")
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"提交订单时出错:\n{str(e)}")
    
    def set_stock_code(self, stock_code):
        """设置股票代码（用于平仓/加仓时预填）"""
        self.stock_code_input.setCurrentText(stock_code)
        self.refresh_quote()
    
    def set_direction(self, direction):
        """设置买卖方向"""
        if direction == 'BUY':
            self.buy_radio.setChecked(True)
        else:
            self.sell_radio.setChecked(True)
    
    def set_quantity(self, qty):
        """设置数量"""
        self.qty_input.setValue(qty)
