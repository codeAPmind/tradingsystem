"""
东方财富数据获取
支持A股实时行情、资金流向
"""
import requests
import json
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'futu_backtest_trader'))


class EastMoneyDataFetcher:
    """东方财富数据获取器"""
    
    BASE_URL = "http://push2.eastmoney.com"
    QUOTE_URL = "http://qt.gtimg.cn"
    
    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        print("✅ 东方财富数据获取器已初始化")
    
    def get_stock_code_format(self, stock_code):
        """
        转换股票代码格式
        
        Parameters:
        -----------
        stock_code : str
            6位代码，如 '600519'
        
        Returns:
        --------
        tuple : (市场代码, 股票代码)
            - 上海: (1, '600519')
            - 深圳: (0, '000001')
        """
        # 移除可能的.SH或.SZ后缀
        if '.' in stock_code:
            stock_code = stock_code.split('.')[0]
        
        if stock_code.startswith('60') or stock_code.startswith('68'):
            return (1, stock_code)  # 上海
        elif stock_code.startswith('00') or stock_code.startswith('30'):
            return (0, stock_code)  # 深圳
        else:
            raise ValueError(f"无法识别股票代码: {stock_code}")
    
    def get_realtime_price(self, stock_code):
        """
        获取实时价格
        
        Parameters:
        -----------
        stock_code : str
            股票代码，如 '600519' 或 '600519.SH'
        
        Returns:
        --------
        dict : 实时行情数据
        """
        market, code = self.get_stock_code_format(stock_code)
        
        # 腾讯财经API（更稳定）
        market_prefix = 'sh' if market == 1 else 'sz'
        url = f"{self.QUOTE_URL}/q={market_prefix}{code}"
        
        try:
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.text.strip().split('~')
                
                if len(data) >= 50:
                    return {
                        'code': stock_code,
                        'name': data[1],
                        'price': float(data[3]),
                        'change': float(data[31]),
                        'change_pct': float(data[32]),
                        'volume': float(data[6]),
                        'amount': float(data[37]),
                        'open': float(data[5]),
                        'high': float(data[33]),
                        'low': float(data[34]),
                        'pre_close': float(data[4]),
                        'time': data[30]
                    }
            
            print(f"❌ 获取实时数据失败")
            return None
            
        except Exception as e:
            print(f"❌ 获取实时数据失败: {e}")
            return None
    
    def get_money_flow(self, stock_code):
        """
        获取资金流向
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        
        Returns:
        --------
        dict : 资金流向数据
        """
        market, code = self.get_stock_code_format(stock_code)
        
        # 东方财富资金流向API
        url = f"{self.BASE_URL}/api/qt/stock/fflow/kline/get"
        
        params = {
            'fields1': 'f1,f2,f3,f7',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63',
            'klt': '101',  # 日线
            'lmt': 1,      # 最近1天
            'secid': f'{market}.{code}'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and data['data']:
                    klines = data['data'].get('klines', [])
                    if klines:
                        parts = klines[0].split(',')
                        return {
                            'date': parts[0],
                            'main_net_inflow': float(parts[1]),      # 主力净流入
                            'small_net_inflow': float(parts[2]),     # 小单净流入
                            'medium_net_inflow': float(parts[3]),    # 中单净流入
                            'large_net_inflow': float(parts[4]),     # 大单净流入
                            'super_large_net_inflow': float(parts[5]) # 特大单净流入
                        }
            
            print(f"❌ 获取资金流向失败")
            return None
            
        except Exception as e:
            print(f"❌ 获取资金流向失败: {e}")
            return None


# 使用示例
if __name__ == '__main__':
    fetcher = EastMoneyDataFetcher()
    
    # 获取贵州茅台实时行情
    print("\n=== 贵州茅台实时行情 ===")
    quote = fetcher.get_realtime_price('600519')
    if quote:
        print(f"名称: {quote['name']}")
        print(f"价格: ¥{quote['price']:.2f}")
        print(f"涨跌: {quote['change']:+.2f} ({quote['change_pct']:+.2f}%)")
        print(f"开盘: ¥{quote['open']:.2f}")
        print(f"最高: ¥{quote['high']:.2f}")
        print(f"最低: ¥{quote['low']:.2f}")
        print(f"成交量: {quote['volume']:.0f}手")
        print(f"成交额: ¥{quote['amount']/100000000:.2f}亿")
    
    # 获取资金流向
    print("\n=== 资金流向 ===")
    flow = fetcher.get_money_flow('600519')
    if flow:
        print(f"日期: {flow['date']}")
        print(f"主力净流入: ¥{flow['main_net_inflow']/10000:.2f}万")
        print(f"大单净流入: ¥{flow['large_net_inflow']/10000:.2f}万")
        print(f"中单净流入: ¥{flow['medium_net_inflow']/10000:.2f}万")
        print(f"小单净流入: ¥{flow['small_net_inflow']/10000:.2f}万")
