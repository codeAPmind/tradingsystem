"""
新闻获取服务
News Fetcher Service - 集成多个API源
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from utils.env_config import config


class NewsService:
    """新闻获取服务"""
    
    def __init__(self):
        """初始化服务"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TradingSystem/1.0'
        })
    
    def get_news(self, stock_code: str, limit: int = 5) -> List[Dict]:
        """
        获取股票新闻
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        limit : int
            新闻数量
        
        Returns:
        --------
        list
            新闻列表
        """
        # 判断市场
        market = self._detect_market(stock_code)
        
        # 美股：优先使用Financial Datasets
        if market == 'US' and config.has_financial_datasets_api():
            try:
                return self._fetch_financial_datasets(stock_code, limit)
            except Exception as e:
                print(f"⚠️  Financial Datasets API失败: {e}")
        
        # 备用：Alpha Vantage
        if config.alpha_vantage_api_key:
            try:
                return self._fetch_alpha_vantage(stock_code, limit)
            except Exception as e:
                print(f"⚠️  Alpha Vantage API失败: {e}")
        
        # 备用：News API
        if config.news_api_key:
            try:
                return self._fetch_news_api(stock_code, limit)
            except Exception as e:
                print(f"⚠️  News API失败: {e}")
        
        # 所有API都失败，返回空列表
        print(f"⚠️  无法获取 {stock_code} 的新闻（未配置API或全部失败）")
        return []
    
    def _detect_market(self, stock_code: str) -> str:
        """
        检测股票市场
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        
        Returns:
        --------
        str
            'US', 'HK', 'CN'
        """
        if stock_code.startswith('HK.'):
            return 'HK'
        elif stock_code.startswith('SH.') or stock_code.startswith('SZ.'):
            return 'CN'
        elif stock_code.isdigit():
            # 纯数字可能是港股或A股
            if len(stock_code) == 5:
                return 'HK'
            elif len(stock_code) == 6:
                return 'CN'
        
        # 默认美股
        return 'US'
    
    def _fetch_financial_datasets(self, stock_code: str, limit: int) -> List[Dict]:
        """
        使用Financial Datasets API获取新闻
        
        API文档: https://financialdatasets.ai/docs
        """
        api_key = config.financial_datasets_api_key
        
        # 构建请求
        url = 'https://api.financialdatasets.ai/news/'
        params = {
            'ticker': stock_code,
            'limit': limit,
            'page': 1
        }
        headers = {
            'X-API-KEY': api_key
        }
        
        response = self.session.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 解析新闻
        news_list = []
        for item in data.get('news', [])[:limit]:
            news_list.append({
                'title': item.get('title', ''),
                'source': item.get('source', 'Financial Datasets'),
                'time': self._format_time(item.get('published_at', '')),
                'summary': item.get('text', '')[:200] + '...',  # 限制长度
                'url': item.get('url', '')
            })
        
        return news_list
    
    def _fetch_alpha_vantage(self, stock_code: str, limit: int) -> List[Dict]:
        """
        使用Alpha Vantage API获取新闻
        
        API文档: https://www.alphavantage.co/documentation/#news-sentiment
        """
        api_key = config.alpha_vantage_api_key
        
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': stock_code,
            'apikey': api_key,
            'limit': limit
        }
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 解析新闻
        news_list = []
        for item in data.get('feed', [])[:limit]:
            news_list.append({
                'title': item.get('title', ''),
                'source': item.get('source', 'Alpha Vantage'),
                'time': self._format_time(item.get('time_published', '')),
                'summary': item.get('summary', '')[:200] + '...',
                'url': item.get('url', '')
            })
        
        return news_list
    
    def _fetch_news_api(self, stock_code: str, limit: int) -> List[Dict]:
        """
        使用News API获取新闻
        
        API文档: https://newsapi.org/docs
        """
        api_key = config.news_api_key
        
        # 获取公司名称（可以从config映射）
        company_name = self._get_company_name(stock_code)
        
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': f'{stock_code} OR {company_name}',
            'apiKey': api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': limit,
            'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        }
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 解析新闻
        news_list = []
        for item in data.get('articles', [])[:limit]:
            news_list.append({
                'title': item.get('title', ''),
                'source': item.get('source', {}).get('name', 'News API'),
                'time': self._format_time(item.get('publishedAt', '')),
                'summary': item.get('description', '')[:200] + '...',
                'url': item.get('url', '')
            })
        
        return news_list
    
    def _get_company_name(self, stock_code: str) -> str:
        """获取公司名称"""
        # 简化映射
        mapping = {
            'TSLA': 'Tesla',
            'AAPL': 'Apple',
            'MSFT': 'Microsoft',
            'GOOGL': 'Google',
            'AMZN': 'Amazon',
            'NVDA': 'Nvidia',
            'META': 'Meta',
            'NFLX': 'Netflix',
        }
        return mapping.get(stock_code, stock_code)
    
    def _format_time(self, time_str: str) -> str:
        """
        格式化时间
        
        Parameters:
        -----------
        time_str : str
            时间字符串
        
        Returns:
        --------
        str
            格式化的时间（如：2小时前）
        """
        if not time_str:
            return '未知时间'
        
        try:
            # 尝试解析ISO格式
            if 'T' in time_str:
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(time_str, '%Y%m%dT%H%M%S')
            
            # 计算时间差
            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
            delta = now - dt
            
            if delta.days > 0:
                return f'{delta.days}天前'
            elif delta.seconds >= 3600:
                hours = delta.seconds // 3600
                return f'{hours}小时前'
            elif delta.seconds >= 60:
                minutes = delta.seconds // 60
                return f'{minutes}分钟前'
            else:
                return '刚刚'
        
        except Exception as e:
            # 解析失败，返回原始字符串
            return time_str[:16] if len(time_str) > 16 else time_str


# 全局服务实例
news_service = NewsService()


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*60)
    print("新闻服务测试".center(60))
    print("="*60 + "\n")
    
    # 测试美股
    print("📰 获取TSLA新闻:")
    news = news_service.get_news('TSLA', limit=3)
    
    if news:
        for i, item in enumerate(news, 1):
            print(f"\n{i}. {item['title']}")
            print(f"   来源: {item['source']} | 时间: {item['time']}")
            print(f"   摘要: {item['summary']}")
    else:
        print("  未获取到新闻（请检查API配置）")
    
    print("\n" + "="*60 + "\n")
