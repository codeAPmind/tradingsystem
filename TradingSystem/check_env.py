"""
检查环境变量配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件
env_path = Path(__file__).parent / '.env'
if not env_path.exists():
    env_path = Path(__file__).parent.parent / 'futu_backtest_trader' / '.env'

print(f"检查.env文件: {env_path}")
print(f"文件存在: {env_path.exists()}")

if env_path.exists():
    load_dotenv(env_path)
    print(f"\n已加载.env文件: {env_path}")
else:
    load_dotenv()
    print("\n尝试从默认位置加载.env")

# 检查环境变量
print("\n环境变量检查:")
print(f"FINANCIAL_DATASETS_API_KEY: {'已设置' if os.getenv('FINANCIAL_DATASETS_API_KEY') else '未设置'}")
if os.getenv('FINANCIAL_DATASETS_API_KEY'):
    key = os.getenv('FINANCIAL_DATASETS_API_KEY')
    print(f"  值: {key[:10]}...{key[-5:] if len(key) > 15 else ''}")

print(f"TUSHARE_TOKEN: {'已设置' if os.getenv('TUSHARE_TOKEN') else '未设置'}")
print(f"DEEPSEEK_API_KEY: {'已设置' if os.getenv('DEEPSEEK_API_KEY') else '未设置'}")
