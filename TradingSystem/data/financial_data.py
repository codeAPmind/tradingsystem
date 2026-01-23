"""
Financial Datasets API客户端
支持美股数据获取
"""
import os
import requests
import pandas as pd
from typing import Optional
from datetime import datetime


class FinancialDatasetsAPI:
    """Financial Datasets API 客户端"""
    
    BASE_URL = "https://api.financialdatasets.ai"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化API客户端
        
        Parameters:
        -----------
        api_key : str, optional
            API密钥，如果不提供则从环境变量读取
        """
        self.session = requests.Session()
        
        self.api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
        
        if self.api_key:
            self.session.headers.update({"X-API-KEY": self.api_key})
            print("✅ Financial Datasets API已初始化")
        else:
            print("⚠️  未设置FINANCIAL_DATASETS_API_KEY")
    
    def get_stock_prices(
        self, 
        ticker: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        获取股票价格数据
        
        Parameters:
        -----------
        ticker : str
            股票代码，如 'TSLA', 'AAPL'
        start_date : str, optional
            开始日期 'YYYY-MM-DD'
        end_date : str, optional
            结束日期 'YYYY-MM-DD'
        
        Returns:
        --------
        DataFrame : 价格数据
            包含: date, open, high, low, close, volume
        """
        url = f"{self.BASE_URL}/prices/"
        
        params = {
            'ticker': ticker,
            'interval': 'day',
            'interval_multiplier': 1,
        }
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # 解析数据
                if 'prices' in data:
                    prices_list = data['prices']
                    df = pd.DataFrame(prices_list)
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    print(f"❌ 无法解析数据格式")
                    return None
                
                if len(df) == 0:
                    print(f"⚠️  未获取到数据")
                    return None
                
                # 数据清洗
                df = df.rename(columns={
                    'time': 'date',
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume'
                })
                
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                # 转换为数值类型
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                print(f"✅ 成功获取 {len(df)} 条数据")
                return df[['date', 'open', 'high', 'low', 'close', 'volume']]
            
            else:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return None
        
        except Exception as e:
            print(f"❌ 获取数据失败: {e}")
            return None


# 使用示例
if __name__ == '__main__':
    api = FinancialDatasetsAPI()
    
    # 获取Tesla数据
    df = api.get_stock_prices('TSLA', '2025-01-01', '2025-01-22')
    if df is not None:
        print("\n数据前5行:")
        print(df.head())
        print("\n数据后5行:")
        print(df.tail())
