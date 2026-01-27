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
            包含: date(字符串), open, high, low, close, volume
        """
        print(f"📊 [FinancialDatasets] 获取 {ticker} 从 {start_date} 到 {end_date}...")
        
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
                
                # 数据清洗和标准化
                # 1. 重命名列（time → date）
                if 'time' in df.columns:
                    df = df.rename(columns={'time': 'date'})
                
                # 2. 确保有所需的列
                required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    print(f"❌ 缺少必需列: {missing_cols}")
                    return None
                
                # 3. 转换date为datetime然后转为字符串（保持与futu_data.py一致）
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                
                # 4. 按日期排序
                df = df.sort_values('date')
                
                # 5. 转换为数值类型
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # 6. 删除NaN行
                df = df.dropna()
                
                # 7. 重置索引
                df = df.reset_index(drop=True)
                
                # 8. 只返回需要的列
                result = df[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
                
                print(f"✅ 成功获取 {len(result)} 条数据")
                print(f"   列: {list(result.columns)}")
                print(f"   日期范围: {result['date'].iloc[0]} ~ {result['date'].iloc[-1]}")
                print(f"   数据类型: date={result['date'].dtype}")
                
                return result
            
            elif response.status_code == 401:
                print(f"❌ API认证失败: 请检查API密钥")
                print(f"   当前密钥: {self.api_key[:10]}... (已部分隐藏)")
                return None
            
            elif response.status_code == 404:
                print(f"❌ 未找到股票数据: {ticker}")
                return None
            
            else:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"   响应: {response.text[:200]}")
                return None
        
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时: 网络连接可能有问题")
            return None
        
        except requests.exceptions.ConnectionError:
            print(f"❌ 连接失败: 无法连接到API服务器")
            return None
        
        except Exception as e:
            print(f"❌ 获取数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*70)
    print("Financial Datasets API 测试")
    print("="*70 + "\n")
    
    api = FinancialDatasetsAPI()
    
    if not api.api_key:
        print("❌ 未设置API密钥")
        print("   请设置环境变量: FINANCIAL_DATASETS_API_KEY")
    else:
        print(f"✅ API密钥: {api.api_key[:10]}... (已部分隐藏)")
        
        # 测试获取Tesla数据
        print("\n【测试1】获取 Tesla (TSLA) 数据")
        print("-"*70)
        df = api.get_stock_prices('TSLA', '2025-01-01', '2025-01-27')
        
        if df is not None:
            print(f"\n✅ 数据获取成功!")
            print(f"   形状: {df.shape}")
            print(f"   列: {list(df.columns)}")
            print(f"   数据类型:")
            for col, dtype in df.dtypes.items():
                print(f"      {col}: {dtype}")
            
            print(f"\n前3行:")
            print(df.head(3).to_string())
            
            print(f"\n后3行:")
            print(df.tail(3).to_string())
        
        # 测试获取Apple数据
        print("\n\n【测试2】获取 Apple (AAPL) 数据")
        print("-"*70)
        df2 = api.get_stock_prices('AAPL', '2025-01-20', '2025-01-27')
        
        if df2 is not None:
            print(f"\n✅ 数据获取成功! ({len(df2)}行)")
    
    print("\n" + "="*70)
    print("测试完成")
    print("="*70 + "\n")
