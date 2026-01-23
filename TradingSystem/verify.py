"""
快速验证脚本
检查关键依赖和配置
"""
import sys
from pathlib import Path

print("="*70)
print("TradingSystem 快速验证")
print("="*70)

# 检查Python版本
print(f"\n✅ Python {sys.version}")

# 检查依赖
print("\n检查依赖包:")
packages = {
    'pandas': '数据处理',
    'numpy': '数值计算',
    'requests': 'HTTP请求',
    'dotenv': '环境变量',
    'schedule': '任务调度',
    'tushare': 'A股数据',
    'openai': 'AI分析'
}

for pkg, desc in packages.items():
    try:
        if pkg == 'dotenv':
            __import__('dotenv')
        else:
            __import__(pkg)
        print(f"  ✅ {pkg:12s} - {desc}")
    except ImportError:
        print(f"  ❌ {pkg:12s} - {desc} (未安装)")

# 检查环境变量
print("\n检查环境配置:")
import os
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / 'futu_backtest_trader' / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 找到.env文件")
else:
    print(f"⚠️  .env文件不存在")

# 检查关键配置
api_key = os.environ.get('FINANCIAL_DATASETS_API_KEY')
if api_key:
    print(f"  ✅ 美股API: {api_key[:8]}...{api_key[-4:]}")
else:
    print(f"  ⚪ 美股API: 未配置")

tushare_token = os.environ.get('TUSHARE_TOKEN')
if tushare_token:
    print(f"  ✅ Tushare: {tushare_token[:8]}...{tushare_token[-4:]}")
else:
    print(f"  ⚪ Tushare: 未配置")

ai_key = os.environ.get('DEEPSEEK_API_KEY')
if ai_key:
    print(f"  ✅ DeepSeek: {ai_key[:8]}...{ai_key[-4:]}")
else:
    print(f"  ⚪ DeepSeek: 未配置")

print("\n" + "="*70)
print("验证完成！")
print("="*70)
print("\n下一步: python test_core.py")
