"""
回测组件
支持参数设置和结果展示
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QComboBox, QDoubleSpinBox,
                             QDateEdit, QTextEdit, QGroupBox, QFormLayout,
                             QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem,
                             QMessageBox, QSplitter)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont
import pandas as pd
from datetime import datetime, timedelta
try:
    import matplotlib
    matplotlib.use('Qt5Agg')  # 使用Qt后端
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  matplotlib未安装，图表功能不可用")

try:
    import backtrader as bt
    BACKTRADER_AVAILABLE = True
except ImportError:
    BACKTRADER_AVAILABLE = False


class BacktestThread(QThread):
    """回测线程"""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, data_manager, strategy_engine, params):
        super().__init__()
        self.data_manager = data_manager
        self.strategy_engine = strategy_engine
        self.params = params
    
    def run(self):
        """执行回测"""
        try:
            from core.backtest_engine import BacktestEngine
            from strategies.backtrader_tsf_lsma import TSFLSMAStrategy
            
            self.progress.emit("正在获取数据...")
            
            # 获取数据
            stock_code = self.params['stock_code']
            start_date = self.params['start_date']
            end_date = self.params['end_date']
            
            df = self.data_manager.get_kline_data(stock_code, start_date, end_date)
            
            if df is None or len(df) < 30:
                self.error.emit("数据不足，无法进行回测（至少需要30条数据）")
                return
            
            self.progress.emit(f"已获取 {len(df)} 条数据，开始回测...")
            
            # 创建回测引擎
            engine = BacktestEngine(
                initial_cash=self.params['initial_cash'],
                commission=self.params['commission']
            )
            
            # 添加数据
            engine.add_data_from_dataframe(df, stock_code)
            
            # 准备策略参数
            strategy_params = {
                'tsf_period': self.params['tsf_period'],
                'lsma_period': self.params['lsma_period'],
                'use_percent': self.params['use_percent'],
                'printlog': False
            }
            
            if self.params['use_percent']:
                strategy_params['buy_threshold_pct'] = self.params['buy_threshold_pct']
                strategy_params['sell_threshold_pct'] = self.params['sell_threshold_pct']
            else:
                strategy_params['buy_threshold'] = self.params['buy_threshold']
                strategy_params['sell_threshold'] = self.params['sell_threshold']
            
            # 添加策略
            engine.add_strategy(TSFLSMAStrategy, **strategy_params)
            
            # 运行回测
            self.progress.emit("回测进行中...")
            result = engine.run()
            
            # 添加额外信息（包括原始K线数据，供前端绘图使用）
            result['stock_code'] = stock_code
            result['start_date'] = start_date
            result['end_date'] = end_date
            result['strategy_params'] = strategy_params
            result['kline_df'] = df
            
            self.finished.emit(result)
            
        except Exception as e:
            import traceback
            error_msg = f"回测失败: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)


class BacktestWidget(QWidget):
    """回测组件"""
    
    def __init__(self, data_manager, strategy_engine):
        super().__init__()
        self.data_manager = data_manager
        self.strategy_engine = strategy_engine
        self.backtest_thread = None
        self.current_result = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建分割器（左侧参数，右侧结果）
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：参数配置
        left_panel = self.create_parameter_panel()
        splitter.addWidget(left_panel)
        
        # 右侧：结果展示
        right_panel = self.create_result_panel()
        splitter.addWidget(right_panel)
        
        # 设置比例
        splitter.setSizes([400, 1000])
        
        layout.addWidget(splitter)
    
    def create_parameter_panel(self):
        """创建参数配置面板"""
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout(panel)
        
        # 标题
        title = QLabel("回测参数")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 基本参数组
        basic_group = QGroupBox("基本参数")
        basic_layout = QFormLayout(basic_group)
        
        # 股票代码
        self.stock_code_input = QLineEdit("TSLA")
        basic_layout.addRow("股票代码:", self.stock_code_input)
        
        # 日期范围
        self.start_date_input = QDateEdit()
        self.start_date_input.setDate(QDate.currentDate().addYears(-1))
        self.start_date_input.setCalendarPopup(True)
        basic_layout.addRow("开始日期:", self.start_date_input)
        
        self.end_date_input = QDateEdit()
        self.end_date_input.setDate(QDate.currentDate())
        self.end_date_input.setCalendarPopup(True)
        basic_layout.addRow("结束日期:", self.end_date_input)
        
        # 初始资金
        self.initial_cash_input = QDoubleSpinBox()
        self.initial_cash_input.setRange(1000, 10000000)
        self.initial_cash_input.setValue(100000)
        self.initial_cash_input.setPrefix("$ ")
        self.initial_cash_input.setDecimals(0)
        basic_layout.addRow("初始资金:", self.initial_cash_input)
        
        # 佣金比例
        self.commission_input = QDoubleSpinBox()
        self.commission_input.setRange(0, 0.01)
        self.commission_input.setValue(0.001)
        self.commission_input.setDecimals(4)
        self.commission_input.setSingleStep(0.0001)
        basic_layout.addRow("佣金比例:", self.commission_input)
        
        layout.addWidget(basic_group)
        
        # 策略参数组
        strategy_group = QGroupBox("策略参数")
        strategy_layout = QFormLayout(strategy_group)
        
        # 策略选择
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(['TSF-LSMA', 'MACD', 'RSI'])
        self.strategy_combo.currentTextChanged.connect(self.on_strategy_changed)
        strategy_layout.addRow("策略:", self.strategy_combo)
        
        # TSF周期
        self.tsf_period_input = QDoubleSpinBox()
        self.tsf_period_input.setRange(3, 50)
        self.tsf_period_input.setValue(9)
        self.tsf_period_input.setDecimals(0)
        strategy_layout.addRow("TSF周期:", self.tsf_period_input)
        
        # LSMA周期
        self.lsma_period_input = QDoubleSpinBox()
        self.lsma_period_input.setRange(5, 100)
        self.lsma_period_input.setValue(20)
        self.lsma_period_input.setDecimals(0)
        strategy_layout.addRow("LSMA周期:", self.lsma_period_input)
        
        # 阈值类型
        self.use_percent_check = QComboBox()
        self.use_percent_check.addItems(['绝对值', '百分比'])
        self.use_percent_check.currentIndexChanged.connect(self.on_threshold_type_changed)
        strategy_layout.addRow("阈值类型:", self.use_percent_check)
        
        # 买入阈值
        self.buy_threshold_input = QDoubleSpinBox()
        self.buy_threshold_input.setRange(0, 100)
        self.buy_threshold_input.setValue(0.5)
        self.buy_threshold_input.setDecimals(2)
        strategy_layout.addRow("买入阈值:", self.buy_threshold_input)
        
        # 卖出阈值
        self.sell_threshold_input = QDoubleSpinBox()
        self.sell_threshold_input.setRange(0, 100)
        self.sell_threshold_input.setValue(0.5)
        self.sell_threshold_input.setDecimals(2)
        strategy_layout.addRow("卖出阈值:", self.sell_threshold_input)
        
        layout.addWidget(strategy_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.run_btn = QPushButton("开始回测")
        self.run_btn.clicked.connect(self.start_backtest)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        button_layout.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_backtest)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)  # 不确定进度
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #9E9E9E;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        return panel
    
    def create_result_panel(self):
        """创建结果展示面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title = QLabel("回测结果")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 标签页
        self.result_tabs = QTabWidget()
        
        # 图表标签页
        self.chart_tab = QWidget()
        chart_layout = QVBoxLayout(self.chart_tab)
        
        # Matplotlib图表
        if MATPLOTLIB_AVAILABLE:
            self.figure = Figure(figsize=(10, 6), facecolor='#2d2d2d')
            self.canvas = FigureCanvas(self.figure)
            chart_layout.addWidget(self.canvas)
        else:
            chart_label = QLabel("matplotlib未安装，无法显示图表\n请运行: pip install matplotlib")
            chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chart_layout.addWidget(chart_label)
            self.figure = None
            self.canvas = None
        
        self.result_tabs.addTab(self.chart_tab, "收益曲线")
        
        # 性能指标标签页
        self.metrics_tab = QWidget()
        metrics_layout = QVBoxLayout(self.metrics_tab)
        
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        metrics_layout.addWidget(self.metrics_text)
        
        self.result_tabs.addTab(self.metrics_tab, "性能指标")
        
        # 交易记录标签页
        self.trades_tab = QWidget()
        trades_layout = QVBoxLayout(self.trades_tab)
        
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(5)
        self.trades_table.setHorizontalHeaderLabels(['日期', '类型', '价格', '数量', '金额'])
        trades_layout.addWidget(self.trades_table)
        
        self.result_tabs.addTab(self.trades_tab, "交易记录")
        
        layout.addWidget(self.result_tabs)
        
        return panel
    
    def on_strategy_changed(self, strategy_name):
        """策略改变回调"""
        # 根据策略显示/隐藏相关参数
        if strategy_name == 'TSF-LSMA':
            self.tsf_period_input.setEnabled(True)
            self.lsma_period_input.setEnabled(True)
        elif strategy_name == 'MACD':
            self.tsf_period_input.setEnabled(False)
            self.lsma_period_input.setEnabled(False)
        # TODO: 其他策略
    
    def on_threshold_type_changed(self, index):
        """阈值类型改变"""
        if index == 0:  # 绝对值
            self.buy_threshold_input.setSuffix("")
            self.sell_threshold_input.setSuffix("")
        else:  # 百分比
            self.buy_threshold_input.setSuffix("%")
            self.sell_threshold_input.setSuffix("%")
    
    def start_backtest(self):
        """开始回测"""
        if not BACKTRADER_AVAILABLE:
            QMessageBox.warning(self, "错误", "backtrader未安装，无法进行回测\n请运行: pip install backtrader")
            return
        
        # 收集参数
        params = {
            'stock_code': self.stock_code_input.text().strip().upper(),
            'start_date': self.start_date_input.date().toString('yyyy-MM-dd'),
            'end_date': self.end_date_input.date().toString('yyyy-MM-dd'),
            'initial_cash': self.initial_cash_input.value(),
            'commission': self.commission_input.value(),
            'strategy': self.strategy_combo.currentText(),
            'tsf_period': int(self.tsf_period_input.value()),
            'lsma_period': int(self.lsma_period_input.value()),
            'use_percent': self.use_percent_check.currentIndex() == 1,
            'buy_threshold': self.buy_threshold_input.value(),
            'sell_threshold': self.sell_threshold_input.value(),
            'buy_threshold_pct': self.buy_threshold_input.value(),
            'sell_threshold_pct': self.sell_threshold_input.value(),
        }
        
        # 验证参数
        if not params['stock_code']:
            QMessageBox.warning(self, "错误", "请输入股票代码")
            return
        
        if params['start_date'] >= params['end_date']:
            QMessageBox.warning(self, "错误", "开始日期必须早于结束日期")
            return
        
        # 禁用按钮
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.show()
        self.status_label.setText("回测进行中...")
        
        # 创建回测线程
        self.backtest_thread = BacktestThread(self.data_manager, self.strategy_engine, params)
        self.backtest_thread.finished.connect(self.on_backtest_finished)
        self.backtest_thread.error.connect(self.on_backtest_error)
        self.backtest_thread.progress.connect(self.on_backtest_progress)
        self.backtest_thread.start()
    
    def stop_backtest(self):
        """停止回测"""
        if self.backtest_thread and self.backtest_thread.isRunning():
            self.backtest_thread.terminate()
            self.backtest_thread.wait()
        
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.hide()
        self.status_label.setText("已停止")
    
    def on_backtest_progress(self, message):
        """回测进度更新"""
        self.status_label.setText(message)
    
    def on_backtest_finished(self, result):
        """回测完成"""
        self.current_result = result
        
        # 更新UI
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.hide()
        self.status_label.setText("回测完成")
        
        # 显示结果
        self.display_results(result)
    
    def on_backtest_error(self, error_msg):
        """回测错误"""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.hide()
        self.status_label.setText("回测失败")
        
        QMessageBox.critical(self, "回测错误", error_msg)
    
    def display_results(self, result):
        """显示回测结果"""
        # 更新性能指标
        analysis = result['analysis']
        
        # 预先计算年化收益率字符串，避免嵌套f-string
        annual_return_str = 'N/A'
        if analysis.get('annual_return') is not None:
            annual_return_str = f"{analysis['annual_return']:.2f}%"
        
        # 预先计算夏普比率字符串
        sharpe_ratio_str = 'N/A'
        if analysis.get('sharpe_ratio') is not None:
            sharpe_ratio_str = f"{analysis['sharpe_ratio']:.4f}"
        
        metrics_text = f"""
回测结果
{'='*50}

基本信息:
  股票代码: {result['stock_code']}
  回测期间: {result['start_date']} 至 {result['end_date']}
  初始资金: ${result['initial_cash']:,.2f}
  最终资金: ${result['final_value']:,.2f}
  总收益: ${result['profit']:,.2f}
  收益率: {result['profit_pct']:+.2f}%

性能指标:
  夏普比率: {sharpe_ratio_str}
  最大回撤: {analysis['max_drawdown']:.2f}%
  年化收益率: {annual_return_str}

交易统计:
  总交易次数: {analysis['total_trades']}
  盈利次数: {analysis['won_trades']}
  亏损次数: {analysis['lost_trades']}
  胜率: {analysis['win_rate']:.2f}%

策略参数:
  TSF周期: {result['strategy_params']['tsf_period']}
  LSMA周期: {result['strategy_params']['lsma_period']}
"""
        self.metrics_text.setPlainText(metrics_text)
        
        # 绘制图表（K线 + 收益曲线 + 买卖信号）
        self.plot_backtest_chart(result)
    
    def plot_backtest_chart(self, result):
        """绘制回测图表：K线 + 买卖信号 + 收益曲线"""
        if not MATPLOTLIB_AVAILABLE or self.figure is None:
            return
        
        self.figure.clear()
        # 上面：K线 + 指标 + 买卖信号；下面：收益曲线
        ax_price, ax_equity = self.figure.subplots(
            2, 1,
            gridspec_kw={'height_ratios': [3, 1]},
            sharex=True
        )
        self.figure.patch.set_facecolor('#2d2d2d')
        ax_price.set_facecolor('#2d2d2d')
        ax_equity.set_facecolor('#2d2d2d')

        # 1) 准备K线数据（优先使用回测时的原始DataFrame）
        df = result.get('kline_df')
        if df is not None and len(df) > 0:
            df_plot = df.copy()
            if 'date' in df_plot.columns:
                df_plot['date'] = pd.to_datetime(df_plot['date'])
            else:
                df_plot = df_plot.reset_index().rename(columns={'index': 'date'})
                df_plot['date'] = pd.to_datetime(df_plot['date'])
            df_plot = df_plot.sort_values('date')

            dates = df_plot['date'].tolist()
            opens = df_plot['open'].astype(float).tolist()
            highs = df_plot['high'].astype(float).tolist()
            lows = df_plot['low'].astype(float).tolist()
            closes = df_plot['close'].astype(float).tolist()

            # 绘制K线
            for i, d in enumerate(dates):
                color = '#4CAF50' if closes[i] >= opens[i] else '#F44336'
                # 影线
                ax_price.plot(
                    [d, d],
                    [lows[i], highs[i]],
                    color=color,
                    linewidth=1,
                    alpha=0.6,
                )
                # 实体
                body_height = abs(closes[i] - opens[i])
                bottom = min(opens[i], closes[i])
                rect = Rectangle(
                    (mdates.date2num(d) - 0.3, bottom),
                    0.6,
                    body_height if body_height > 0 else 0.001,
                    facecolor=color,
                    edgecolor=color,
                    alpha=0.9,
                )
                ax_price.add_patch(rect)

            # 买卖信号标注
            buy_signals = result.get('buy_signals', [])
            sell_signals = result.get('sell_signals', [])

            for i, (d, price) in enumerate(buy_signals):
                d_ts = pd.to_datetime(d)
                ax_price.scatter(
                    d_ts,
                    price,
                    color='lime',
                    marker='^',
                    s=120,
                    zorder=5,
                    label='买入' if i == 0 else '',
                )

            for i, (d, price) in enumerate(sell_signals):
                d_ts = pd.to_datetime(d)
                ax_price.scatter(
                    d_ts,
                    price,
                    color='red',
                    marker='v',
                    s=120,
                    zorder=5,
                    label='卖出' if i == 0 else '',
                )

            ax_price.set_ylabel('价格', color='white')
            ax_price.set_title(
                f"{result['stock_code']} 回测K线（含买卖信号）",
                color='white',
                fontsize=14,
                fontweight='bold',
            )
            ax_price.legend(loc='upper left')
            ax_price.grid(True, alpha=0.3, color='gray')
            ax_price.tick_params(colors='white')
            ax_price.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

        # 2) 收益曲线
        equity_ax = ax_equity
        if 'equity_curve' in result and result['equity_curve']:
            equity_curve = result['equity_curve']
            eq_dates = [
                pd.to_datetime(item['date'])
                if isinstance(item['date'], str)
                else item['date']
                for item in equity_curve
            ]
            eq_values = [item['value'] for item in equity_curve]
        else:
            start_date = pd.to_datetime(result['start_date'])
            end_date = pd.to_datetime(result['end_date'])
            eq_dates = [start_date, end_date]
            eq_values = [result['initial_cash'], result['final_value']]

        equity_ax.plot(
            eq_dates,
            eq_values,
            color='#4CAF50',
            linewidth=2,
            label='资产曲线',
        )
        equity_ax.axhline(
            y=result['initial_cash'],
            color='#9E9E9E',
            linestyle='--',
            label='初始资金',
        )
        equity_ax.set_xlabel('日期', color='white')
        equity_ax.set_ylabel('资产 ($)', color='white')
        equity_ax.set_title('收益曲线', color='white', fontsize=12)
        equity_ax.legend()
        equity_ax.grid(True, alpha=0.3, color='gray')
        equity_ax.tick_params(colors='white')
        equity_ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

        # 统一设置坐标轴颜色
        for ax in (ax_price, equity_ax):
            for spine in ax.spines.values():
                spine.set_color('white')

        self.figure.tight_layout()

        if self.canvas:
            self.canvas.draw()
