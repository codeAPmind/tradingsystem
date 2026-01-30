"""
新闻组件 - 增强版
支持响应自选股点击，自动刷新新闻
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTabWidget,
                             QTextEdit, QScrollArea, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from datetime import datetime
from typing import Dict, List, Optional
import requests


class NewsLoaderThread(QThread):
    """新闻加载线程"""
    
    finished = pyqtSignal(dict)  # 改为dict，包含新闻、情绪、基本面
    error = pyqtSignal(str)
    
    def __init__(self, stock_code):
        super().__init__()
        self.stock_code = stock_code
    
    def run(self):
        """获取新闻数据"""
        try:
            # 导入服务
            from utils.news_service import news_service
            from utils.ai_analyzer import ai_analyzer
            
            # 1. 获取新闻（真实API）
            print(f"📰 正在获取 {self.stock_code} 的新闻...")
            news_list = news_service.get_news(self.stock_code, limit=5)
            
            # 如果没有获取到真实新闻，使用模拟数据
            if not news_list:
                print(f"⚠️  使用模拟新闻数据")
                news_list = self._get_mock_news(self.stock_code)
            
            # 2. AI情绪分析
            print(f"🤖 正在分析情绪...")
            sentiment = ai_analyzer.analyze_sentiment(self.stock_code, news_list)
            
            # 3. 基本面分析
            print(f"📊 正在分析基本面...")
            fundamental = ai_analyzer.analyze_fundamental(self.stock_code)
            
            # 4. 生成交易建议
            print(f"💡 正在生成建议...")
            advice = ai_analyzer.generate_trading_advice(
                self.stock_code, sentiment, fundamental
            )
            
            # 返回完整数据
            result = {
                'news': news_list,
                'sentiment': sentiment,
                'fundamental': fundamental,
                'advice': advice
            }
            
            self.finished.emit(result)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(f"获取新闻失败: {str(e)}")
    
    def _get_mock_news(self, stock_code):
        """获取模拟新闻数据"""
        # 根据股票代码生成不同的新闻
        news_templates = {
            'TSLA': [
                {
                    'title': 'Tesla发布新一代电动车型，续航里程突破800公里',
                    'source': '汽车之家',
                    'time': '2小时前',
                    'summary': 'Tesla今日发布新款Model S Plaid+，续航里程达到837公里，创下电动车新纪录。'
                },
                {
                    'title': 'Elon Musk宣布Cybertruck开始交付',
                    'source': 'TechCrunch',
                    'time': '5小时前',
                    'summary': 'Tesla CEO马斯克在社交媒体宣布，期待已久的Cybertruck将于本月开始交付给预订用户。'
                },
                {
                    'title': 'Tesla Q4财报超预期，股价盘后大涨',
                    'source': '华尔街日报',
                    'time': '1天前',
                    'summary': 'Tesla公布的第四季度财报显示，营收和利润均超过分析师预期，股价盘后上涨8%。'
                }
            ],
            'AAPL': [
                {
                    'title': '苹果发布Vision Pro头显，定价3499美元',
                    'source': 'Apple官网',
                    'time': '1小时前',
                    'summary': '苹果正式发布首款混合现实头显Vision Pro，将于下月上市销售。'
                },
                {
                    'title': 'iPhone 15系列销量创新高',
                    'source': '路透社',
                    'time': '3小时前',
                    'summary': '分析师报告显示，iPhone 15系列手机销量超过预期，特别是Pro系列表现强劲。'
                },
                {
                    'title': '苹果与OpenAI达成战略合作',
                    'source': 'Bloomberg',
                    'time': '6小时前',
                    'summary': '消息人士透露，苹果正与OpenAI商谈在iOS系统中集成AI功能。'
                }
            ],
            'DEFAULT': [
                {
                    'title': f'{stock_code}最新动态：业绩稳定增长',
                    'source': '财经网',
                    'time': '2小时前',
                    'summary': f'{stock_code}公司发布最新业绩报告，各项指标符合预期。'
                },
                {
                    'title': f'分析师上调{stock_code}目标价',
                    'source': '投资者报',
                    'time': '5小时前',
                    'summary': f'多家投行分析师上调{stock_code}目标价，看好公司未来发展。'
                },
                {
                    'title': f'{stock_code}获得重要合同订单',
                    'source': '商业周刊',
                    'time': '1天前',
                    'summary': f'{stock_code}宣布获得大型合同订单，预计将提升公司营收。'
                }
            ]
        }
        
        # 返回对应股票的新闻，如果没有则返回默认新闻
        return news_templates.get(stock_code, news_templates['DEFAULT'])


class NewsWidget(QWidget):
    """新闻组件 - 增强版"""
    
    def __init__(self):
        super().__init__()
        self.current_stock = None
        self.news_loader = None
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题栏
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("新闻与分析")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.refresh_news)
        self.refresh_btn.setMaximumWidth(80)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # 标签页
        self.tabs = QTabWidget()
        
        # === 最新新闻标签页 ===
        news_tab = QWidget()
        news_layout = QVBoxLayout(news_tab)
        
        # 新闻内容区域
        self.news_content = QTextEdit()
        self.news_content.setReadOnly(True)
        self.news_content.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                padding: 10px;
                font-size: 12px;
                line-height: 1.6;
            }
        """)
        self.news_content.setHtml(self._get_default_news())
        news_layout.addWidget(self.news_content)
        
        self.tabs.addTab(news_tab, "📰 最新新闻")
        
        # === 基本面分析标签页 ===
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)
        
        self.analysis_content = QTextEdit()
        self.analysis_content.setReadOnly(True)
        self.analysis_content.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                padding: 10px;
                font-size: 12px;
            }
        """)
        self.analysis_content.setHtml(self._get_default_analysis())
        analysis_layout.addWidget(self.analysis_content)
        
        self.tabs.addTab(analysis_tab, "📊 基本面")
        
        # === AI分析标签页（新增）===
        ai_tab = QWidget()
        ai_layout = QVBoxLayout(ai_tab)
        
        self.ai_content = QTextEdit()
        self.ai_content.setReadOnly(True)
        self.ai_content.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                padding: 10px;
                font-size: 12px;
            }
        """)
        self.ai_content.setHtml(self._get_default_ai_analysis())
        ai_layout.addWidget(self.ai_content)
        
        self.tabs.addTab(ai_tab, "🤖 AI分析")
        
        layout.addWidget(self.tabs)
    
    def update_news(self, stock_code: str):
        """
        更新新闻（响应自选股点击）
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        """
        self.current_stock = stock_code
        
        # 更新标题
        from config import get_stock_display_name
        display_name = get_stock_display_name(stock_code)
        self.title_label.setText(f"新闻与分析 - {stock_code} ({display_name})")
        
        # 显示加载中
        self.news_content.setHtml(self._get_loading_html())
        self.analysis_content.setHtml(self._get_loading_html())
        self.ai_content.setHtml(self._get_loading_html())
        
        # 禁用刷新按钮
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("加载中...")
        
        # 启动新闻加载线程
        self.news_loader = NewsLoaderThread(stock_code)
        self.news_loader.finished.connect(self.on_news_loaded)
        self.news_loader.error.connect(self.on_news_error)
        self.news_loader.start()
    
    def refresh_news(self):
        """刷新新闻"""
        if self.current_stock:
            self.update_news(self.current_stock)
    
    def on_news_loaded(self, result: dict):
        """新闻加载完成"""
        # 解包数据
        news_list = result.get('news', [])
        sentiment = result.get('sentiment', {})
        fundamental = result.get('fundamental', {})
        advice = result.get('advice', {})
        
        # 更新新闻标签页
        news_html = self._format_news_html(news_list)
        self.news_content.setHtml(news_html)
        
        # 更新基本面标签页（使用真实数据）
        analysis_html = self._format_analysis_html(self.current_stock, fundamental)
        self.analysis_content.setHtml(analysis_html)
        
        # 更新AI分析标签页（使用真实数据）
        ai_html = self._format_ai_analysis_html(
            self.current_stock, sentiment, advice
        )
        self.ai_content.setHtml(ai_html)
        
        # 恢复刷新按钮
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新")
    
    def on_news_error(self, error_msg: str):
        """新闻加载失败"""
        error_html = f"""
        <div style='color: #ff5555; padding: 20px; text-align: center;'>
            <h3>⚠️ 加载失败</h3>
            <p>{error_msg}</p>
            <p style='color: #888; font-size: 11px; margin-top: 10px;'>
                请检查网络连接或稍后重试
            </p>
        </div>
        """
        
        self.news_content.setHtml(error_html)
        
        # 恢复刷新按钮
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新")
    
    def _format_news_html(self, news_list: list) -> str:
        """格式化新闻HTML"""
        html = """
        <style>
            .news-item {
                background-color: #3d3d3d;
                border-left: 3px solid #4CAF50;
                padding: 12px;
                margin-bottom: 12px;
                border-radius: 4px;
            }
            .news-title {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 6px;
            }
            .news-meta {
                color: #888888;
                font-size: 11px;
                margin-bottom: 8px;
            }
            .news-summary {
                color: #cccccc;
                font-size: 12px;
                line-height: 1.5;
            }
        </style>
        """
        
        for i, news in enumerate(news_list, 1):
            html += f"""
            <div class='news-item'>
                <div class='news-title'>📌 {news['title']}</div>
                <div class='news-meta'>
                    📰 {news['source']} | ⏰ {news['time']}
                </div>
                <div class='news-summary'>{news['summary']}</div>
            </div>
            """
        
        html += f"""
        <div style='color: #666; font-size: 10px; text-align: center; margin-top: 15px;'>
            更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        """
        
        return html
    
    def _format_analysis_html(self, stock_code: str, fundamental: Dict) -> str:
        """格式化基本面分析HTML"""
        # 使用真实的基本面数据
        metrics = fundamental.get('metrics', {})
        valuation = fundamental.get('valuation', {})
        strengths = fundamental.get('strengths', [])
        risks = fundamental.get('risks', [])
        score = fundamental.get('score', 50)
        
        html = f"""
        <style>
            .section {{
                background-color: #3d3d3d;
                padding: 12px;
                margin-bottom: 10px;
                border-radius: 4px;
            }}
            .section-title {{
                color: #4CAF50;
                font-weight: bold;
                font-size: 13px;
                margin-bottom: 8px;
            }}
            .metric {{
                color: #cccccc;
                font-size: 12px;
                margin: 4px 0;
                padding-left: 10px;
            }}
            .positive {{ color: #4CAF50; }}
            .negative {{ color: #ff5555; }}
        </style>
        
        <div class='section'>
            <div class='section-title'>✅ 财务指标</div>
            <div class='metric'>• 营收增长率: <span class='positive'>+{metrics.get("revenue_growth", 0.15)*100:.1f}%</span></div>
            <div class='metric'>• 净利润增长率: <span class='positive'>+{metrics.get("profit_growth", 0.18)*100:.1f}%</span></div>
            <div class='metric'>• 毛利率: {metrics.get("gross_margin", 0.42)*100:.1f}%</div>
            <div class='metric'>• ROE: {metrics.get("roe", 0.18)*100:.1f}%</div>
        </div>
        
        <div class='section'>
            <div class='section-title'>📈 估值分析</div>
            <div class='metric'>• 市盈率 (P/E): {valuation.get("pe", 0):.1f}</div>
            <div class='metric'>• 市净率 (P/B): {valuation.get("pb", 0):.1f}</div>
            <div class='metric'>• 市销率 (P/S): {valuation.get("ps", 0):.1f}</div>
            <div class='metric'>• PEG比率: {valuation.get("peg", 0):.1f}</div>
        </div>
        
        <div class='section'>
            <div class='section-title'>💡 优势因素</div>
        """
        
        for strength in strengths[:4]:
            html += f"<div class='metric'>• {strength}</div>"
        
        html += """
        </div>
        
        <div class='section'>
            <div class='section-title'>⚠️ 风险因素</div>
        """
        
        for risk in risks[:4]:
            html += f"<div class='metric'>• {risk}</div>"
        
        html += f"""
        </div>
        
        <div class='section'>
            <div class='section-title'>🎯 综合评分</div>
            <div style='text-align: center; margin-top: 10px;'>
                <span style='font-size: 32px; color: #4CAF50; font-weight: bold;'>{score}</span>
                <span style='color: #888; font-size: 14px;'> / 100</span>
            </div>
        </div>
        
        <div style='color: #666; font-size: 10px; text-align: center; margin-top: 15px;'>
            数据更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        """
        
        return html
    
    def _format_ai_analysis_html(self, stock_code: str, sentiment: Dict, advice: Dict) -> str:
        """格式化AI分析HTML"""
        # 使用真实的AI分析数据
        
        # 情绪相关
        score = sentiment.get('score', 0.0)
        sentiment_text = sentiment.get('sentiment', 'neutral')
        confidence = sentiment.get('confidence', 0.5)
        summary = sentiment.get('summary', '暂无分析')
        keywords = sentiment.get('keywords', [])
        
        # 建议相关
        action = advice.get('action', 'HOLD')
        action_confidence = advice.get('confidence', 0.5)
        reasoning = advice.get('reasoning', '暂无建议')
        support = advice.get('support', 0)
        resistance = advice.get('resistance', 0)
        
        # 情绪颜色
        if sentiment_text == 'positive':
            sentiment_color = '#4CAF50'
            sentiment_cn = '偏正面'
        elif sentiment_text == 'negative':
            sentiment_color = '#ff5555'
            sentiment_cn = '偏负面'
        else:
            sentiment_color = '#FFA500'
            sentiment_cn = '中性'
        
        # 操作建议颜色
        if action == 'BUY':
            action_color = '#4CAF50'
            action_cn = '建议买入'
        elif action == 'SELL':
            action_color = '#ff5555'
            action_cn = '建议卖出'
        else:
            action_color = '#FFA500'
            action_cn = '建议持有'
        
        html = f"""
        <style>
            .ai-section {{
                background-color: #3d3d3d;
                padding: 12px;
                margin-bottom: 10px;
                border-radius: 4px;
                border-left: 3px solid #2196F3;
            }}
            .ai-title {{
                color: #2196F3;
                font-weight: bold;
                font-size: 13px;
                margin-bottom: 8px;
            }}
            .ai-content {{
                color: #cccccc;
                font-size: 12px;
                line-height: 1.6;
            }}
        </style>
        
        <div class='ai-section'>
            <div class='ai-title'>🤖 AI情绪分析</div>
            <div class='ai-content'>
                市场情绪<span style='color: {sentiment_color}; font-weight: bold;'>{sentiment_cn}</span>，
                情绪评分：<span style='color: {sentiment_color}; font-weight: bold;'>{score:.2f}</span><br>
                置信度：{confidence*100:.1f}%<br>
                分析：{summary}
            </div>
        </div>
        """
        
        if keywords:
            keywords_str = "、".join(keywords[:5])
            html += f"""
        <div class='ai-section'>
            <div class='ai-title'>🔑 关键词</div>
            <div class='ai-content'>
                {keywords_str}
            </div>
        </div>
        """
        
        if support > 0 and resistance > 0:
            html += f"""
        <div class='ai-section'>
            <div class='ai-title'>📊 技术面分析</div>
            <div class='ai-content'>
                • 支撑位: <span style='color: #4CAF50;'>${support:.2f}</span><br>
                • 阻力位: <span style='color: #ff5555;'>${resistance:.2f}</span>
            </div>
        </div>
        """
        
        html += f"""
        <div class='ai-section'>
            <div class='ai-title'>💡 AI建议</div>
            <div class='ai-content'>
                操作：<span style='color: {action_color}; font-weight: bold;'>{action_cn}</span><br>
                置信度：{action_confidence*100:.1f}%<br>
                理由：{reasoning}
            </div>
        </div>
        
        <div style='background-color: #3d3d3d; padding: 10px; border-radius: 4px; text-align: center; margin-top: 10px;'>
            <span style='color: #2196F3; font-size: 11px;'>
                ⚠️ AI分析仅供参考，不构成投资建议
            </span>
        </div>
        
        <div style='color: #666; font-size: 10px; text-align: center; margin-top: 10px;'>
            AI分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        """
        
        return html
    
    def _get_loading_html(self) -> str:
        """获取加载中HTML"""
        return """
        <div style='text-align: center; padding: 40px; color: #888;'>
            <div style='font-size: 32px; margin-bottom: 10px;'>⏳</div>
            <div style='font-size: 14px;'>正在加载数据...</div>
        </div>
        """
    
    def _get_default_news(self) -> str:
        """获取默认新闻HTML"""
        return """
        <div style='text-align: center; padding: 40px; color: #888;'>
            <div style='font-size: 32px; margin-bottom: 10px;'>📰</div>
            <div style='font-size: 14px;'>请从左侧自选股列表选择股票</div>
            <div style='font-size: 12px; margin-top: 10px; color: #666;'>
                点击股票后将自动加载相关新闻
            </div>
        </div>
        """
    
    def _get_default_analysis(self) -> str:
        """获取默认基本面HTML"""
        return """
        <div style='text-align: center; padding: 40px; color: #888;'>
            <div style='font-size: 32px; margin-bottom: 10px;'>📊</div>
            <div style='font-size: 14px;'>请选择股票查看基本面分析</div>
        </div>
        """
    
    def _get_default_ai_analysis(self) -> str:
        """获取默认AI分析HTML"""
        return """
        <div style='text-align: center; padding: 40px; color: #888;'>
            <div style='font-size: 32px; margin-bottom: 10px;'>🤖</div>
            <div style='font-size: 14px;'>请选择股票查看AI分析</div>
        </div>
        """
