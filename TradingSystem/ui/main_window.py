"""
主窗口
量化交易系统主界面
"""
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QMenuBar, QToolBar, QStatusBar,
                             QSplitter, QLabel, QPushButton, QMessageBox, QTabWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QFont

from .widgets.stock_list import StockListWidget
from .widgets.chart_widget import ChartWidget
from .widgets.signal_panel import SignalPanel
from .widgets.position_widget import PositionWidget
from .widgets.news_widget import NewsWidget
from config import THEME, WINDOW_SIZE


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, data_manager, strategy_engine, scheduler, ai_analyzer):
        """
        初始化主窗口
        
        Parameters:
        -----------
        data_manager : DataManager
            数据管理器
        strategy_engine : StrategyEngine
            策略引擎
        scheduler : TaskScheduler
            任务调度器
        ai_analyzer : AIAnalyzer
            AI分析器
        """
        super().__init__()
        
        self.data_manager = data_manager
        self.strategy_engine = strategy_engine
        self.scheduler = scheduler
        self.ai_analyzer = ai_analyzer
        
        # 当前选中的股票
        self.current_stock = None
        
        # 初始化UI
        self.init_ui()
        
        # 设置定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(60000)  # 每分钟更新一次
        
        # 连接信号
        self.connect_signals()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("量化交易系统 - TradingSystem")
        self.setGeometry(100, 100, WINDOW_SIZE[0], WINDOW_SIZE[1])
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建中央区域
        self.create_central_widget()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 应用主题
        self.apply_theme()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 策略菜单
        strategy_menu = menubar.addMenu('策略')
        
        strategy_config_action = QAction('策略配置', self)
        strategy_config_action.triggered.connect(self.show_strategy_config)
        strategy_menu.addAction(strategy_config_action)
        
        # 交易菜单
        trade_menu = menubar.addMenu('交易')
        
        connect_action = QAction('连接交易账户', self)
        connect_action.triggered.connect(self.connect_trade_account)
        trade_menu.addAction(connect_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具')
        
        scheduler_action = QAction('任务调度', self)
        scheduler_action.triggered.connect(self.show_scheduler)
        tools_menu.addAction(scheduler_action)
        
        settings_action = QAction('设置', self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 连接按钮
        self.connect_btn = QPushButton("连接")
        self.connect_btn.clicked.connect(self.connect_trade_account)
        toolbar.addWidget(self.connect_btn)
        
        toolbar.addSeparator()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar.addWidget(refresh_btn)
        
        toolbar.addSeparator()
        
        # 回测按钮
        backtest_btn = QPushButton("回测")
        backtest_btn.clicked.connect(self.show_backtest)
        toolbar.addWidget(backtest_btn)
        
        # 交易按钮
        trade_btn = QPushButton("交易")
        trade_btn.clicked.connect(self.show_trade)
        toolbar.addWidget(trade_btn)
        
        # 策略按钮
        strategy_btn = QPushButton("策略")
        strategy_btn.clicked.connect(self.show_strategy_config)
        toolbar.addWidget(strategy_btn)
        
        # 设置按钮
        settings_btn = QPushButton("设置")
        settings_btn.clicked.connect(self.show_settings)
        toolbar.addWidget(settings_btn)
    
    def create_central_widget(self):
        """创建中央区域"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：股票列表
        self.stock_list = StockListWidget()
        self.stock_list.setMaximumWidth(250)
        main_splitter.addWidget(self.stock_list)
        
        # 中间：回测界面（主要）和K线图/信号（标签页）
        center_tabs = QTabWidget()
        
        # 回测标签页（默认显示）
        from .widgets.backtest_widget import BacktestWidget
        self.backtest_widget = BacktestWidget(self.data_manager, self.strategy_engine)
        center_tabs.addTab(self.backtest_widget, "回测")
        
        # K线图和信号标签页
        center_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # K线图
        self.chart_widget = ChartWidget()
        center_splitter.addWidget(self.chart_widget)
        
        # 信号面板
        self.signal_panel = SignalPanel()
        center_splitter.addWidget(self.signal_panel)
        
        center_splitter.setSizes([600, 200])
        center_tabs.addTab(center_splitter, "K线图")
        
        main_splitter.addWidget(center_tabs)
        
        # 右侧：持仓和新闻
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 持仓
        self.position_widget = PositionWidget()
        right_splitter.addWidget(self.position_widget)
        
        # 新闻
        self.news_widget = NewsWidget()
        right_splitter.addWidget(self.news_widget)
        
        right_splitter.setSizes([300, 200])
        right_splitter.setMaximumWidth(300)
        main_splitter.addWidget(right_splitter)
        
        # 设置分割器比例
        main_splitter.setSizes([250, 1000, 300])
        
        main_layout.addWidget(main_splitter)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 连接状态
        self.connection_label = QLabel("未连接")
        self.status_bar.addWidget(self.connection_label)
        
        self.status_bar.addPermanentWidget(QLabel("|"))
        
        # 最后更新时间
        self.update_time_label = QLabel("最后更新: --")
        self.status_bar.addPermanentWidget(self.update_time_label)
    
    def apply_theme(self):
        """应用主题"""
        if THEME == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QWidget {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3d3d3d;
                    border: 1px solid #4d4d4d;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #4d4d4d;
                }
                QPushButton:pressed {
                    background-color: #2d2d2d;
                }
                QListWidget {
                    background-color: #2d2d2d;
                    border: 1px solid #3d3d3d;
                }
                QTextEdit {
                    background-color: #2d2d2d;
                    border: 1px solid #3d3d3d;
                }
                QStatusBar {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
            """)
    
    def connect_signals(self):
        """连接信号"""
        # 股票列表选择信号
        self.stock_list.stock_selected.connect(self.on_stock_selected)
        
        # 调度器信号回调
        self.scheduler.set_signal_callback(self.on_signal_received)
    
    def on_stock_selected(self, stock_code: str):
        """股票选择回调"""
        self.current_stock = stock_code
        self.load_stock_data(stock_code)
    
    def load_stock_data(self, stock_code: str):
        """加载股票数据"""
        from datetime import datetime, timedelta
        
        # 获取最近60天的数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        df = self.data_manager.get_kline_data(stock_code, start_date, end_date)
        
        if df is not None:
            # 更新图表
            self.chart_widget.update_data(df, stock_code)
            
            # 生成信号
            self.strategy_engine.activate_strategy(stock_code, 'TSF-LSMA')
            signals = self.strategy_engine.generate_signal(stock_code, df)
            
            # 更新信号面板
            if signals:
                for signal in signals:
                    self.signal_panel.add_signal(signal)
            
            # 更新状态栏
            self.update_time_label.setText(f"最后更新: {datetime.now().strftime('%H:%M:%S')}")
    
    def on_signal_received(self, signal: dict):
        """收到信号回调"""
        self.signal_panel.add_signal(signal)
        
        # 显示通知
        if signal['type'] != 'HOLD':
            QMessageBox.information(
                self,
                "交易信号",
                f"{signal['stock']} - {signal['type']}\n{signal['reason']}"
            )
    
    def refresh_data(self):
        """刷新数据"""
        if self.current_stock:
            self.load_stock_data(self.current_stock)
    
    def update_data(self):
        """定时更新数据"""
        if self.current_stock:
            self.load_stock_data(self.current_stock)
    
    def connect_trade_account(self):
        """连接交易账户"""
        QMessageBox.information(self, "提示", "交易账户连接功能待实现")
    
    def show_strategy_config(self):
        """显示策略配置"""
        QMessageBox.information(self, "提示", "策略配置功能待实现")
    
    def show_backtest(self):
        """显示回测界面"""
        QMessageBox.information(self, "提示", "回测功能待实现")
    
    def show_trade(self):
        """显示交易界面"""
        QMessageBox.information(self, "提示", "交易功能待实现")
    
    def show_scheduler(self):
        """显示任务调度界面"""
        QMessageBox.information(self, "提示", "任务调度功能待实现")
    
    def show_settings(self):
        """显示设置界面"""
        QMessageBox.information(self, "提示", "设置功能待实现")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "量化交易系统 v1.0\n\n"
            "基于PyQt6开发的量化交易系统\n"
            "支持美股、港股、A股三个市场\n"
            "集成多种交易策略和AI分析"
        )
    
    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self,
            '确认退出',
            '确定要退出吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 停止定时器
            self.update_timer.stop()
            
            # 断开连接
            self.data_manager.disconnect()
            
            event.accept()
        else:
            event.ignore()
