"""
AI情绪分析工具
使用Claude API分析股票新闻/社交媒体情绪
"""
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class SentimentAnalyzer:
    """
    AI驱动的情绪分析器
    支持新闻、推特等文本分析
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化情绪分析器
        
        Parameters:
        -----------
        api_key : str, optional
            Anthropic API密钥，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            print("⚠️  未设置ANTHROPIC_API_KEY，情绪分析功能将被禁用")
            self.enabled = False
        else:
            print("✅ 情绪分析器已初始化")
            self.enabled = True
        
        # API配置
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-sonnet-4-20250514"
        
        # 缓存（避免重复分析）
        self.cache = {}
    
    def analyze_text(self, text: str, context: str = "") -> Dict:
        """
        分析文本情绪
        
        Parameters:
        -----------
        text : str
            要分析的文本（新闻标题、推文等）
        context : str
            上下文信息（如股票代码、日期）
        
        Returns:
        --------
        dict : {
            'sentiment_score': float (-1.0 ~ 1.0),
            'confidence': float (0.0 ~ 1.0),
            'reasoning': str,
            'keywords': list
        }
        """
        if not self.enabled:
            return self._neutral_result("情绪分析未启用")
        
        # 检查缓存
        cache_key = f"{text[:50]}_{context}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            result = self._call_claude_api(text, context)
            self.cache[cache_key] = result
            return result
        
        except Exception as e:
            print(f"❌ 情绪分析失败: {e}")
            return self._neutral_result(f"分析失败: {e}")
    
    def analyze_news_batch(self, news_list: List[str], stock_code: str) -> Dict:
        """
        批量分析新闻列表
        
        Parameters:
        -----------
        news_list : list
            新闻标题列表
        stock_code : str
            股票代码
        
        Returns:
        --------
        dict : 综合情绪分析结果
        """
        if not self.enabled or not news_list:
            return self._neutral_result("无新闻或分析未启用")
        
        # 合并新闻文本
        combined_text = "\n".join([f"• {news}" for news in news_list[:10]])  # 最多10条
        
        # 分析
        return self.analyze_text(combined_text, f"股票: {stock_code}")
    
    def _call_claude_api(self, text: str, context: str) -> Dict:
        """调用Claude API进行分析"""
        
        # 构建提示词
        prompt = self._build_prompt(text, context)
        
        # API请求
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": self.model,
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code} - {response.text}")
        
        # 解析响应
        response_json = response.json()
        result_text = response_json['content'][0]['text']
        
        # 提取JSON结果
        result = self._parse_response(result_text)
        
        return result
    
    def _build_prompt(self, text: str, context: str) -> str:
        """构建Claude分析提示词"""
        
        prompt = f"""你是一位专业的金融市场情绪分析师，擅长从新闻和社交媒体中判断市场情绪。

{f'背景信息: {context}' if context else ''}

请分析以下内容的市场情绪：

{text}

请从以下维度进行分析：
1. **整体情绪倾向**: 这些信息对股价是正面、负面还是中性？
2. **影响程度**: 这些信息对股价的潜在影响有多大？
3. **可信度**: 信息来源是否可靠？
4. **关键词**: 提取最重要的关键词（3-5个）

请以JSON格式输出结果：
```json
{{
  "sentiment_score": <-1.0到1.0之间的浮点数，-1表示极度负面，0表示中性，1表示极度正面>,
  "confidence": <0.0到1.0之间的浮点数，表示分析的置信度>,
  "reasoning": "<100字以内的简要分析>",
  "keywords": ["关键词1", "关键词2", "关键词3"]
}}
```

评分标准：
- **sentiment_score**:
  * -1.0 ~ -0.7: 极度负面（如破产、重大丑闻）
  * -0.7 ~ -0.3: 负面（如业绩下滑、负面新闻）
  * -0.3 ~ 0.3: 中性（如常规公告、市场噪音）
  * 0.3 ~ 0.7: 正面（如业绩增长、产品发布）
  * 0.7 ~ 1.0: 极度正面（如重大突破、超预期业绩）

- **confidence**:
  * 0.0 ~ 0.3: 低置信度（信息模糊或相互矛盾）
  * 0.3 ~ 0.7: 中等置信度（信息较明确但可能有争议）
  * 0.7 ~ 1.0: 高置信度（信息明确且来源可靠）

只输出JSON，不要有其他内容。"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        """解析Claude的响应"""
        
        try:
            # 查找JSON部分
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("响应中未找到JSON")
            
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            # 验证和标准化
            result.setdefault('sentiment_score', 0.0)
            result.setdefault('confidence', 0.5)
            result.setdefault('reasoning', '无分析')
            result.setdefault('keywords', [])
            
            # 限制范围
            result['sentiment_score'] = max(-1.0, min(1.0, result['sentiment_score']))
            result['confidence'] = max(0.0, min(1.0, result['confidence']))
            
            return result
        
        except Exception as e:
            print(f"⚠️  响应解析失败: {e}")
            print(f"原始响应: {response_text}")
            return self._neutral_result(f"解析失败: {e}")
    
    def _neutral_result(self, reason: str = "") -> Dict:
        """返回中性结果"""
        return {
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'reasoning': reason or '无法分析',
            'keywords': []
        }
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
        print("✅ 情绪分析缓存已清除")


class MockSentimentAnalyzer(SentimentAnalyzer):
    """
    模拟情绪分析器（用于测试，无需API密钥）
    根据关键词返回模拟情绪分数
    """
    
    def __init__(self):
        super().__init__(api_key="mock")
        self.enabled = True
        print("✅ 使用模拟情绪分析器（测试模式）")
    
    def analyze_text(self, text: str, context: str = "") -> Dict:
        """基于关键词的简单情绪分析"""
        
        text_lower = text.lower()
        
        # 正面关键词
        positive_keywords = [
            'breakthrough', '突破', 'record', '创纪录', 'surge', '飙升',
            'profit', '盈利', 'beat', '超预期', 'upgrade', '升级',
            'partnership', '合作', 'expansion', '扩张', 'innovation', '创新',
            'growth', '增长', 'success', '成功', 'strong', '强劲'
        ]
        
        # 负面关键词
        negative_keywords = [
            'crash', '暴跌', 'loss', '亏损', 'recall', '召回',
            'scandal', '丑闻', 'lawsuit', '诉讼', 'decline', '下滑',
            'warning', '警告', 'cut', '削减', 'miss', '不及预期',
            'bankruptcy', '破产', 'investigation', '调查', 'fraud', '欺诈'
        ]
        
        # 统计关键词出现次数
        positive_count = sum(1 for kw in positive_keywords if kw in text_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in text_lower)
        
        # 计算情绪分数
        if positive_count + negative_count == 0:
            sentiment_score = 0.0
            confidence = 0.3
        else:
            sentiment_score = (positive_count - negative_count) / (positive_count + negative_count)
            confidence = min(0.7, (positive_count + negative_count) * 0.2)
        
        # 找到匹配的关键词
        found_keywords = []
        for kw in positive_keywords + negative_keywords:
            if kw in text_lower:
                found_keywords.append(kw)
        
        return {
            'sentiment_score': sentiment_score,
            'confidence': confidence,
            'reasoning': f'检测到 {positive_count} 个正面词, {negative_count} 个负面词',
            'keywords': found_keywords[:5]
        }


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*70)
    print("情绪分析工具测试")
    print("="*70 + "\n")
    
    # 测试1: 使用模拟分析器
    print("【测试1】模拟情绪分析器")
    print("-"*70)
    
    mock_analyzer = MockSentimentAnalyzer()
    
    test_texts = [
        "Tesla reports record profits, beats earnings expectations",
        "Tesla recalls 2 million vehicles due to safety concerns",
        "Elon Musk announces major FSD breakthrough",
        "Tesla stock neutral, trading sideways"
    ]
    
    for text in test_texts:
        result = mock_analyzer.analyze_text(text, "TSLA")
        print(f"\n文本: {text}")
        print(f"情绪分数: {result['sentiment_score']:+.2f}")
        print(f"置信度: {result['confidence']:.2f}")
        print(f"原因: {result['reasoning']}")
        print(f"关键词: {result['keywords']}")
    
    # 测试2: 真实API（如果配置了密钥）
    print("\n\n【测试2】真实API分析器")
    print("-"*70)
    
    analyzer = SentimentAnalyzer()
    
    if analyzer.enabled:
        result = analyzer.analyze_text(
            "Tesla announces breakthrough in autonomous driving technology, "
            "stock surges 15% on strong earnings beat",
            "TSLA"
        )
        print(f"\n情绪分数: {result['sentiment_score']:+.2f}")
        print(f"置信度: {result['confidence']:.2f}")
        print(f"分析: {result['reasoning']}")
        print(f"关键词: {result['keywords']}")
    else:
        print("⚠️  真实API未启用（未设置ANTHROPIC_API_KEY）")
    
    print("\n" + "="*70)
    print("测试完成")
    print("="*70 + "\n")
