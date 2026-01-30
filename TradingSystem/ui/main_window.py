"""
主窗口 - 增强版
量化交易系统主界面（集成交易功能）
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
from .widgets.trade_widget import TradeWidget
from config import THEME, WINDOW_SIZE

# 导入交易管理器
from live_trading.trader_manager import TraderManager


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
        
        # 初始化交易管理器（模拟盘）
        self.trader_manager = TraderManager(use_simulate=True)
        self.is_connected = False
        
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
        
        disconnect_action = QAction('断开连接', self)
        disconnect_action.triggered.connect(self.disconnect_trade_account)
        trade_menu.addAction(disconnect_action)
        
        trade_menu.addSeparator()
        
        refresh_pos_action = QAction('刷新持仓', self)
        refresh_pos_action.triggered.connect(self.refresh_positions)
        trade_menu.addAction(refresh_pos_action)
        
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
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
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
        
        # 中间：标签页（回测/K线图/交易）
        self.center_tabs = QTabWidget()
        
        # 回测标签页
        from .widgets.backtest_widget import BacktestWidget
        self.backtest_widget = BacktestWidget(self.data_manager, self.strategy_engine)
        self.center_tabs.addTab(self.backtest_widget, "📊 回测")
        
        # K线图和信号标签页
        center_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # K线图
        self.chart_widget = ChartWidget()
        center_splitter.addWidget(self.chart_widget)
        
        # 信号面板
        self.signal_panel = SignalPanel()
        center_splitter.addWidget(self.signal_panel)
        
        center_splitter.setSizes([600, 200])
        self.center_tabs.addTab(center_splitter, "📈 K线图")
        
        # 交易面板（新增）
        self.trade_widget = TradeWidget(self.trader_manager)
        self.center_tabs.addTab(self.trade_widget, "🔄 交易")
        
        main_splitter.addWidget(self.center_tabs)
        
        # 右侧：持仓和新闻
        self.right_tabs = QTabWidget()
        
        # 持仓（增强版）
        self.position_widget = PositionWidget(self.trader_manager)
        self.right_tabs.addTab(self.position_widget, "📊 持仓")
        
        # 新闻
        self.news_widget = NewsWidget()
        self.right_tabs.addTab(self.news_widget, "📰 新闻")
        
        self.right_tabs.setMaximumWidth(350)
        main_splitter.addWidget(self.right_tabs)
        
        # 设置分割器比例
        main_splitter.setSizes([250, 1000, 350])
        
        main_layout.addWidget(main_splitter)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 连接状态
        self.connection_label = QLabel("⚪ 未连接")
        self.status_bar.addWidget(self.connection_label)
        
        self.status_bar.addPermanentWidget(QLabel("|"))
        
        # 账户类型
        self.account_label = QLabel("账户: 模拟盘")
        self.status_bar.addPermanentWidget(self.account_label)
        
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
                QTabWidget::pane {
                    border: 1px solid #3d3d3d;
                }
            """)
    
    def connect_signals(self):
        """连接信号"""
        # 股票列表选择信号
        self.stock_list.stock_selected.connect(self.on_stock_selected)
        
        # 调度器信号回调
        self.scheduler.set_signal_callback(self.on_signal_received)
        
        # 交易面板信号
        self.trade_widget.order_submitted.connect(self.on_order_submitted)
        
        # 持仓面板信号
        self.position_widget.close_position.connect(self.on_close_position)
        self.position_widget.add_position.connect(self.on_add_position)
    
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
        
        # 更新新闻组件（无论是否获取到数据都尝试更新）
        self.news_widget.update_news(stock_code)
    
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
    
    def on_order_submitted(self, order: dict):
        """订单提交回调"""
        print(f"[主窗口] 订单已提交: {order}")
        
        # 刷新持仓
        QTimer.singleShot(2000, self.refresh_positions)  # 2秒后刷新
    
    def on_close_position(self, stock_code: str, qty: int):
        """平仓回调"""
        print(f"[主窗口] 平仓请求: {stock_code} {qty}股")
        
        # 切换到交易面板
        self.center_tabs.setCurrentWidget(self.trade_widget)
        
        # 预填信息
        self.trade_widget.set_stock_code(stock_code)
        self.trade_widget.set_direction('SELL')
        self.trade_widget.set_quantity(qty)
    
    def on_add_position(self, stock_code: str):
        """加仓回调"""
        print(f"[主窗口] 加仓请求: {stock_code}")
        
        # 切换到交易面板
        self.center_tabs.setCurrentWidget(self.trade_widget)
        
        # 预填信息
        self.trade_widget.set_stock_code(stock_code)
        self.trade_widget.set_direction('BUY')
    
    def refresh_data(self):
        """刷新数据"""
        if self.current_stock:
            self.load_stock_data(self.current_stock)
        
        # 刷新持仓
        if self.is_connected:
            self.refresh_positions()
    
    def refresh_positions(self):
        """刷新持仓"""
        self.position_widget.refresh_positions()
    
    def update_data(self):
        """定时更新数据"""
        if self.current_stock:
            self.load_stock_data(self.current_stock)
    
    def connect_trade_account(self):
        """连接交易账户"""
        if self.is_connected:
            QMessageBox.information(self, "提示", "已经连接")
            return
        
        # 显示连接中
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("连接中...")
        self.connection_label.setText("🟡 连接中...")
        
        try:
            # 连接所有市场
            success = self.trader_manager.connect_all()
            
            if success:
                self.is_connected = True
                self.connect_btn.setText("已连接")
                self.connect_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        padding: 5px 15px;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                """)
                self.connection_label.setText("🟢 已连接")
                
                # 刷新持仓
                self.refresh_positions()
                
                QMessageBox.information(self, "成功", "交易账户连接成功！")
            else:
                self.connect_btn.setEnabled(True)
                self.connect_btn.setText("连接")
                self.connection_label.setText("⚪ 连接失败")
                
                QMessageBox.warning(
                    self, "失败", 
                    "交易账户连接失败\n\n请检查:\n"
                    "1. Futu OpenD是否已启动\n"
                    "2. 是否已登录账户\n"
                    "3. 是否有交易权限"
                )
        except Exception as e:
            self.connect_btn.setEnabled(True)
            self.connect_btn.setText("连接")
            self.connection_label.setText("⚪ 连接错误")
            
            QMessageBox.critical(self, "错误", f"连接出错:\n{str(e)}")
    
    def disconnect_trade_account(self):
        """断开交易账户连接"""
        if not self.is_connected:
            QMessageBox.information(self, "提示", "未连接")
            return
        
        try:
            self.trader_manager.disconnect()
            self.is_connected = False
            
            self.connect_btn.setEnabled(True)
            self.connect_btn.setText("连接")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    padding: 5px 15px;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            self.connection_label.setText("⚪ 未连接")
            
            QMessageBox.information(self, "成功", "已断开连接")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"断开连接出错:\n{str(e)}")
    
    def show_strategy_config(self):
        """显示策略配置"""
        QMessageBox.information(self, "提示", "策略配置功能待实现")
    
    def show_backtest(self):
        """显示回测界面"""
        self.center_tabs.setCurrentWidget(self.backtest_widget)
    
    def show_trade(self):
        """显示交易界面"""
        self.center_tabs.setCurrentWidget(self.trade_widget)
    
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
            "集成多种交易策略和AI分析\n\n"
            "✅ 实盘交易功能已集成\n"
            "✅ 风控系统已启用\n"
            "✅ 多市场支持"
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
            
            # 停止持仓刷新定时器
            if hasattr(self.position_widget, 'stopTimer'):
                self.position_widget.stopTimer()
            
            # 断开数据管理器
            self.data_manager.disconnect()
            
            # 断开交易管理器
            if self.is_connected:
                self.trader_manager.disconnect()
            
            event.accept()
        else:
            event.ignore()
