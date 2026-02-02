"""
系统配置
支持美股、港股、A股三个市场
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# ==================== 项目路径 ====================
BASE_DIR = Path(__file__).parent.parent
DATA_CACHE_DIR = BASE_DIR / 'data_cache'
LOG_DIR = BASE_DIR / 'logs'

# 创建必要的目录
DATA_CACHE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ==================== 数据源配置 ====================

# Futu配置（港股）
FUTU_HOST = os.getenv('FUTU_HOST', '127.0.0.1')
FUTU_PORT = int(os.getenv('FUTU_PORT', 11111))

# Financial Datasets配置（美股）
FINANCIAL_DATASETS_API_KEY = os.getenv('FINANCIAL_DATASETS_API_KEY')

# Tushare配置（A股）
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN')

# ==================== 交易配置 ====================

# Futu交易密码
FUTU_TRADING_PWD = os.getenv('FUTU_TRADING_PWD')

# 默认使用模拟盘
DEFAULT_USE_SIMULATE = True

# 佣金比例
DEFAULT_COMMISSION = 0.001

# ==================== AI配置 ====================

# DeepSeek
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# ChatGPT
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Claude
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')

# 通义千问
QWEN_API_KEY = os.getenv('QWEN_API_KEY')

# 文心一言
ERNIE_API_KEY = os.getenv('ERNIE_API_KEY')
ERNIE_SECRET_KEY = os.getenv('ERNIE_SECRET_KEY')

# 主力AI模型
PRIMARY_AI_MODEL = os.getenv('PRIMARY_AI_MODEL', 'deepseek')

# 备用AI模型
FALLBACK_AI_MODELS = ['chatgpt', 'deepseek']

# ==================== 缓存配置 ====================

CACHE_ENABLED = True

# ==================== 定时任务配置 ====================

SCHEDULER_ENABLED = True

# 任务时间配置
SCHEDULE_HK_SIGNAL = '16:10'    # 港股收盘后
SCHEDULE_A_SIGNAL = '15:05'     # A股收盘后
SCHEDULE_US_SIGNAL = '04:10'    # 美股收盘后
SCHEDULE_HK_TRADE = '09:25'     # 港股开盘前
SCHEDULE_A_TRADE = '09:25'      # A股开盘前
SCHEDULE_US_TRADE = '21:25'     # 美股开盘前

# ==================== 通知配置 ====================

NOTIFICATION_ENABLED = True
EMAIL_ENABLED = False
WECHAT_ENABLED = False

# 邮件配置
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_TO = os.getenv('EMAIL_TO')

# 微信通知（Server酱）
SERVERCHAN_KEY = os.getenv('SERVERCHAN_KEY')

# ==================== UI配置 ====================

THEME = 'dark'  # dark/light
WINDOW_SIZE = (1600, 900)

# ==================== 日志配置 ====================

LOG_LEVEL = 'INFO'
LOG_FILE = LOG_DIR / 'trading_system.log'

# ==================== 市场识别 ====================

def get_market_type(stock_code: str) -> str:
    """
    识别股票所属市场
    
    Parameters:
    -----------
    stock_code : str
        股票代码
    
    Returns:
    --------
    str : 'US', 'HK', 'A'
    """
    # code = stock_code.strip()
    
    # # 显式指定前缀的港股
    # if code.startswith('HK.'):
    #     return 'HK'
    
    # # 纯数字代码
    # if code.isdigit():
    #     # 4~5位数字：优先按港股处理（例如 1797 -> HK.01797）
    #     if 4 <= len(code) <= 5:
    #         return 'HK'
    #     # 6位数字：按A股处理
    #     if len(code) == 6:
    #         return 'A'
    
    # # 其他情况默认按美股处理（英文代码等）
    # return 'US'

    """
    识别股票所属市场
    
    Parameters:
    -----------
    stock_code : str
        股票代码
    
    Returns:
    --------
    str : 'US', 'HK', 'A'
    """
    code = stock_code.strip().upper()
    
    # 🆕 A股：SH. 或 SZ. 前缀
    if code.startswith('SH.') or code.startswith('SZ.'):
        return 'A'
    
    # 港股：HK. 前缀
    if code.startswith('HK.'):
        return 'HK'
    
    # 纯数字代码
    if code.isdigit():
        # 4~5位数字：优先按港股处理
        if 4 <= len(code) <= 5:
            return 'HK'
        # 6位数字：按A股处理
        if len(code) == 6:
            return 'A'
    
    # 其他情况默认按美股处理
    return 'US'


def get_stock_display_name(stock_code: str) -> str:
    """
    获取股票显示名称
    
    Parameters:
    -----------
    stock_code : str
        股票代码
    
    Returns:
    --------
    str : 显示名称
    """
    market = get_market_type(stock_code)
    
    stock_names = {
        # 美股
        'TSLA': 'Tesla特斯拉',
        'NVDA': 'Nvidia英伟达',
        'AAPL': 'Apple苹果',
        'MSFT': 'Microsoft微软',
        'GOOGL': 'Google谷歌',
        'AMZN': 'Amazon亚马逊',
        'META': 'Meta脸书',
        
        # 港股
        'HK.01797': '东方甄选',
        'HK.00700': '腾讯控股',
        'HK.09988': '阿里巴巴',
        'HK.03690': '美团',
        
        # A股
        '600519': '贵州茅台',
        '000001': '平安银行',
        '000002': '万科A',
        '600036': '招商银行',
    }
    
    return stock_names.get(stock_code, stock_code)
