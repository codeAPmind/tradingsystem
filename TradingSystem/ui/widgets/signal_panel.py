"""
信号面板组件
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextEdit,
                             QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from datetime import datetime


class SignalPanel(QWidget):
    """信号面板组件"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.signals = []
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("交易信号")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        # 信号容器
        self.signal_container = QWidget()
        self.signal_layout = QVBoxLayout(self.signal_container)
        self.signal_layout.addStretch()
        
        scroll.setWidget(self.signal_container)
        layout.addWidget(scroll)
    
    def add_signal(self, signal: dict):
        """
        添加信号
        
        Parameters:
        -----------
        signal : dict
            信号字典
        """
        # 创建信号卡片
        card = QFrame()
        card.setFrameShape(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        
        # 信号类型和股票
        signal_type = signal.get('type', 'HOLD')
        stock_code = signal.get('stock', 'N/A')
        
        # 根据信号类型设置颜色
        if signal_type == 'BUY':
            color = "#4CAF50"  # 绿色
            icon = "🟢"
        elif signal_type == 'SELL':
            color = "#f44336"  # 红色
            icon = "🔴"
        else:
            color = "#9E9E9E"  # 灰色
            icon = "⚪"
        
        header = QLabel(f"{icon} {signal_type} - {stock_code}")
        header.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px;")
        card_layout.addWidget(header)
        
        # 原因
        reason = signal.get('reason', '')
        reason_label = QLabel(f"原因: {reason}")
        reason_label.setWordWrap(True)
        card_layout.addWidget(reason_label)
        
        # 价格信息
        current_price = signal.get('current_price', 0)
        price_label = QLabel(f"当前价: ${current_price:.2f}")
        card_layout.addWidget(price_label)
        
        # 建议价格
        suggest_min = signal.get('suggest_price_min', 0)
        suggest_max = signal.get('suggest_price_max', 0)
        suggest_label = QLabel(f"建议价: ${suggest_min:.2f} - ${suggest_max:.2f}")
        card_layout.addWidget(suggest_label)
        
        # 时间
        time_str = signal.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        time_label = QLabel(f"时间: {time_str}")
        time_label.setStyleSheet("color: #9E9E9E; font-size: 10px;")
        card_layout.addWidget(time_label)
        
        # 添加到布局（插入到最前面）
        self.signal_layout.insertWidget(0, card)
        
        # 限制最多显示10个信号
        while self.signal_layout.count() > 11:  # 10个信号 + 1个stretch
            item = self.signal_layout.takeAt(self.signal_layout.count() - 2)
            if item:
                item.widget().deleteLater()
        
        # 保存信号
        self.signals.insert(0, signal)
        if len(self.signals) > 10:
            self.signals.pop()
