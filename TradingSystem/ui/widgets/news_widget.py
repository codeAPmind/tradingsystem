"""
新闻组件
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTabWidget,
                             QTextEdit, QScrollArea)
from PyQt6.QtCore import Qt


class NewsWidget(QWidget):
    """新闻组件"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("新闻与分析")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # 标签页
        self.tabs = QTabWidget()
        
        # 最新新闻标签页
        news_tab = QWidget()
        news_layout = QVBoxLayout(news_tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        news_content = QTextEdit()
        news_content.setReadOnly(True)
        news_content.setText("""
最新新闻:

1. Tesla发布新车型，股价上涨5%
   来源: 财经网 | 2025-01-22 10:30
   
2. Nvidia AI芯片需求激增
   来源: 科技日报 | 2025-01-22 09:15
   
3. 苹果Q4财报超预期
   来源: 路透社 | 2025-01-22 08:00
        """)
        scroll.setWidget(news_content)
        news_layout.addWidget(scroll)
        
        self.tabs.addTab(news_tab, "最新新闻")
        
        # 基本面分析标签页
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)
        
        scroll2 = QScrollArea()
        scroll2.setWidgetResizable(True)
        scroll2.setStyleSheet("border: none;")
        
        analysis_content = QTextEdit()
        analysis_content.setReadOnly(True)
        analysis_content.setText("""
基本面分析:

✅ 正面因素:
- 营收增长15%
- 净利润增长18%
- 市场份额扩大

❌ 负面因素:
- 估值偏高
- 竞争加剧
- 政策风险

综合评分: 75/100
        """)
        scroll2.setWidget(analysis_content)
        analysis_layout.addWidget(scroll2)
        
        self.tabs.addTab(analysis_tab, "基本面分析")
        
        layout.addWidget(self.tabs)
