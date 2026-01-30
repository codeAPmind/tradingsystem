"""
AI分析服务
AI Analysis Service - Claude & ChatGPT
"""
from typing import Dict, List, Optional
from utils.env_config import config


class AIAnalyzer:
    """AI分析服务"""
    
    def __init__(self):
        """初始化AI分析器"""
        self.provider = config.ai_provider
        
        # 初始化客户端
        if self.provider == 'claude' and config.has_anthropic_api():
            self._init_claude()
        elif self.provider == 'openai' and config.has_openai_api():
            self._init_openai()
        else:
            print("⚠️  未配置AI API，AI分析功能将禁用")
            self.client = None
    
    def _init_claude(self):
        """初始化Claude客户端"""
        try:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=config.anthropic_api_key
            )
            print("✅ Claude AI已初始化")
        except ImportError:
            print("❌ anthropic库未安装: pip install anthropic")
            self.client = None
        except Exception as e:
            print(f"❌ Claude初始化失败: {e}")
            self.client = None
    
    def _init_openai(self):
        """初始化OpenAI客户端"""
        try:
            import openai
            openai.api_key = config.openai_api_key
            self.client = openai
            print("✅ OpenAI已初始化")
        except ImportError:
            print("❌ openai库未安装: pip install openai")
            self.client = None
        except Exception as e:
            print(f"❌ OpenAI初始化失败: {e}")
            self.client = None
    
    def analyze_sentiment(self, stock_code: str, news_list: List[Dict]) -> Dict:
        """
        分析新闻情绪
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        news_list : list
            新闻列表
        
        Returns:
        --------
        dict : {
            'score': float,         # -1.0 to 1.0
            'sentiment': str,       # 'positive'/'neutral'/'negative'
            'confidence': float,    # 0.0 to 1.0
            'summary': str,         # 分析摘要
            'keywords': list        # 关键词
        }
        """
        if not self.client or not news_list:
            return self._get_neutral_sentiment()
        
        try:
            # 构建提示词
            news_text = self._format_news_for_analysis(news_list)
            
            if self.provider == 'claude':
                return self._analyze_with_claude(stock_code, news_text)
            elif self.provider == 'openai':
                return self._analyze_with_openai(stock_code, news_text)
            else:
                return self._get_neutral_sentiment()
        
        except Exception as e:
            print(f"❌ AI情绪分析失败: {e}")
            return self._get_neutral_sentiment()
    
    def analyze_fundamental(self, stock_code: str) -> Dict:
        """
        基本面分析
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        
        Returns:
        --------
        dict : {
            'metrics': dict,        # 财务指标
            'valuation': dict,      # 估值分析
            'strengths': list,      # 优势
            'risks': list,          # 风险
            'score': int            # 综合评分 0-100
        }
        """
        if not self.client:
            return self._get_default_fundamental()
        
        try:
            if self.provider == 'claude':
                return self._fundamental_with_claude(stock_code)
            elif self.provider == 'openai':
                return self._fundamental_with_openai(stock_code)
            else:
                return self._get_default_fundamental()
        
        except Exception as e:
            print(f"❌ 基本面分析失败: {e}")
            return self._get_default_fundamental()
    
    def generate_trading_advice(self, stock_code: str, sentiment: Dict, fundamental: Dict) -> Dict:
        """
        生成交易建议
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        sentiment : dict
            情绪分析结果
        fundamental : dict
            基本面分析结果
        
        Returns:
        --------
        dict : {
            'action': str,          # 'BUY'/'HOLD'/'SELL'
            'confidence': float,    # 0.0 to 1.0
            'reasoning': str,       # 理由
            'target_price': float,  # 目标价
            'stop_loss': float      # 止损价
        }
        """
        if not self.client:
            return self._get_default_advice()
        
        try:
            if self.provider == 'claude':
                return self._advice_with_claude(stock_code, sentiment, fundamental)
            elif self.provider == 'openai':
                return self._advice_with_openai(stock_code, sentiment, fundamental)
            else:
                return self._get_default_advice()
        
        except Exception as e:
            print(f"❌ 交易建议生成失败: {e}")
            return self._get_default_advice()
    
    # ==========================================
    # Claude实现
    # ==========================================
    
    def _analyze_with_claude(self, stock_code: str, news_text: str) -> Dict:
        """使用Claude分析情绪"""
        prompt = f"""请分析以下关于 {stock_code} 的新闻，给出情绪评分和分析：

新闻内容：
{news_text}

请以JSON格式返回分析结果，包含：
1. score: 情绪评分（-1.0到1.0，负数表示看空，正数表示看多）
2. sentiment: 情绪类别（positive/neutral/negative）
3. confidence: 置信度（0.0到1.0）
4. summary: 分析摘要（50字以内）
5. keywords: 关键词列表（最多5个）

仅返回JSON，不要其他文字。"""
        
        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # 解析响应
        content = message.content[0].text
        import json
        result = json.loads(content)
        
        return result
    
    def _fundamental_with_claude(self, stock_code: str) -> Dict:
        """使用Claude进行基本面分析"""
        prompt = f"""请对 {stock_code} 进行基本面分析：

请以JSON格式返回分析结果，包含：
1. metrics: 财务指标（营收增长率、净利润增长率、毛利率、ROE）
2. valuation: 估值指标（PE、PB、PS、PEG）
3. strengths: 优势列表（最多4项）
4. risks: 风险列表（最多4项）
5. score: 综合评分（0-100）

仅返回JSON，不要其他文字。"""
        
        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = message.content[0].text
        import json
        result = json.loads(content)
        
        return result
    
    def _advice_with_claude(self, stock_code: str, sentiment: Dict, fundamental: Dict) -> Dict:
        """使用Claude生成交易建议"""
        prompt = f"""基于以下信息，给出 {stock_code} 的交易建议：

情绪分析：
{sentiment}

基本面分析：
{fundamental}

请以JSON格式返回建议，包含：
1. action: 操作建议（BUY/HOLD/SELL）
2. confidence: 置信度（0.0-1.0）
3. reasoning: 理由（100字以内）
4. support: 支撑位
5. resistance: 阻力位

仅返回JSON，不要其他文字。"""
        
        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = message.content[0].text
        import json
        result = json.loads(content)
        
        return result
    
    # ==========================================
    # OpenAI实现
    # ==========================================
    
    def _analyze_with_openai(self, stock_code: str, news_text: str) -> Dict:
        """使用OpenAI分析情绪"""
        prompt = f"""请分析以下关于 {stock_code} 的新闻，给出情绪评分和分析：

新闻内容：
{news_text}

请以JSON格式返回分析结果，包含：
1. score: 情绪评分（-1.0到1.0）
2. sentiment: 情绪类别（positive/neutral/negative）
3. confidence: 置信度（0.0到1.0）
4. summary: 分析摘要（50字以内）
5. keywords: 关键词列表（最多5个）

仅返回JSON。"""
        
        response = self.client.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个专业的股票分析师。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        content = response.choices[0].message['content']
        import json
        result = json.loads(content)
        
        return result
    
    def _fundamental_with_openai(self, stock_code: str) -> Dict:
        """使用OpenAI进行基本面分析"""
        prompt = f"""请对 {stock_code} 进行基本面分析，以JSON格式返回。"""
        
        response = self.client.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个专业的基本面分析师。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        content = response.choices[0].message['content']
        import json
        result = json.loads(content)
        
        return result
    
    def _advice_with_openai(self, stock_code: str, sentiment: Dict, fundamental: Dict) -> Dict:
        """使用OpenAI生成交易建议"""
        prompt = f"""基于情绪和基本面分析，给出 {stock_code} 的交易建议（JSON格式）。

情绪: {sentiment}
基本面: {fundamental}"""
        
        response = self.client.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个专业的交易顾问。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        content = response.choices[0].message['content']
        import json
        result = json.loads(content)
        
        return result
    
    # ==========================================
    # 辅助方法
    # ==========================================
    
    def _format_news_for_analysis(self, news_list: List[Dict]) -> str:
        """格式化新闻用于分析"""
        formatted = []
        for i, news in enumerate(news_list, 1):
            formatted.append(
                f"{i}. {news['title']}\n"
                f"   {news['summary']}\n"
            )
        return "\n".join(formatted)
    
    def _get_neutral_sentiment(self) -> Dict:
        """获取中性情绪"""
        return {
            'score': 0.0,
            'sentiment': 'neutral',
            'confidence': 0.5,
            'summary': '未进行AI分析（未配置API）',
            'keywords': []
        }
    
    def _get_default_fundamental(self) -> Dict:
        """获取默认基本面"""
        return {
            'metrics': {
                'revenue_growth': 0.15,
                'profit_growth': 0.18,
                'gross_margin': 0.42,
                'roe': 0.18
            },
            'valuation': {
                'pe': 28.5,
                'pb': 5.2,
                'ps': 3.8,
                'peg': 1.5
            },
            'strengths': ['数据不可用'],
            'risks': ['数据不可用'],
            'score': 50
        }
    
    def _get_default_advice(self) -> Dict:
        """获取默认建议"""
        return {
            'action': 'HOLD',
            'confidence': 0.5,
            'reasoning': '未进行AI分析（未配置API）',
            'support': 0,
            'resistance': 0
        }


# 全局分析器实例
ai_analyzer = AIAnalyzer()


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*60)
    print("AI分析服务测试".center(60))
    print("="*60 + "\n")
    
    # 测试新闻列表
    test_news = [
        {
            'title': 'Tesla Q4 Earnings Beat Expectations',
            'summary': 'Tesla reported strong Q4 earnings with revenue growth of 25%...'
        },
        {
            'title': 'Elon Musk Announces New Gigafactory',
            'summary': 'Tesla CEO revealed plans for a new factory in Southeast Asia...'
        }
    ]
    
    print("📊 测试情绪分析:")
    sentiment = ai_analyzer.analyze_sentiment('TSLA', test_news)
    print(f"  情绪评分: {sentiment['score']}")
    print(f"  情绪类别: {sentiment['sentiment']}")
    print(f"  置信度: {sentiment['confidence']}")
    print(f"  摘要: {sentiment['summary']}")
    
    print("\n" + "="*60 + "\n")
