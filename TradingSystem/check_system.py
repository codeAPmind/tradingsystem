"""
系统配置检查工具
检查环境配置、依赖安装、API连接等
"""
import sys
import os
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'futu_backtest_trader'))

def check_python_version():
    """检查Python版本"""
    print("\n" + "="*70)
    print("检查1: Python版本")
    print("="*70)
    
    version = sys.version_info
    print(f"当前版本: Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python版本符合要求（需要3.8+）")
        return True
    else:
        print("❌ Python版本过低，需要3.8或更高版本")
        return False


def check_dependencies():
    """检查依赖安装"""
    print("\n" + "="*70)
    print("检查2: 依赖包")
    print("="*70)
    
    required = {
        'pandas': '数据处理',
        'numpy': '数值计算',
        'requests': 'HTTP请求',
        'dotenv': '环境变量',
        'schedule': '任务调度'
    }
    
    optional = {
        'tushare': 'A股数据',
        'openai': 'AI分析（DeepSeek/ChatGPT）',
        'anthropic': 'AI分析（Claude）',
        'dashscope': 'AI分析（通义千问）',
        'futu': '港股数据'
    }
    
    all_ok = True
    
    # 检查必需依赖
    print("\n必需依赖:")
    for pkg, desc in required.items():
        try:
            __import__(pkg)
            print(f"  ✅ {pkg:15s} - {desc}")
        except ImportError:
            print(f"  ❌ {pkg:15s} - {desc} （未安装）")
            all_ok = False
    
    # 检查可选依赖
    print("\n可选依赖:")
    for pkg, desc in optional.items():
        try:
            __import__(pkg)
            print(f"  ✅ {pkg:15s} - {desc}")
        except ImportError:
            print(f"  ⚪ {pkg:15s} - {desc} （未安装）")
    
    return all_ok


def check_env_config():
    """检查环境配置"""
    print("\n" + "="*70)
    print("检查3: 环境变量配置")
    print("="*70)
    
    # 加载环境变量
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / 'futu_backtest_trader' / '.env'
    
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ 找到.env文件: {env_path}")
    else:
        print(f"⚠️  未找到.env文件: {env_path}")
        print("   请创建.env文件并配置API密钥")
    
    # 检查配置项
    configs = {
        '美股API': 'FINANCIAL_DATASETS_API_KEY',
        'A股API': 'TUSHARE_TOKEN',
        'DeepSeek': 'DEEPSEEK_API_KEY',
        'ChatGPT': 'OPENAI_API_KEY',
        'Claude': 'CLAUDE_API_KEY',
        '通义千问': 'QWEN_API_KEY',
        'Futu Host': 'FUTU_HOST',
        'Futu Port': 'FUTU_PORT'
    }
    
    print("\n配置项:")
    for name, key in configs.items():
        value = os.environ.get(key)
        if value:
            # 隐藏API密钥
            if 'KEY' in key or 'TOKEN' in key:
                masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
                print(f"  ✅ {name:12s}: {masked}")
            else:
                print(f"  ✅ {name:12s}: {value}")
        else:
            print(f"  ⚪ {name:12s}: 未配置")
    
    # 检查是否至少有一个数据源
    has_data_source = (
        os.environ.get('FINANCIAL_DATASETS_API_KEY') or
        os.environ.get('TUSHARE_TOKEN')
    )
    
    if not has_data_source:
        print("\n⚠️  警告: 未配置任何数据源API")
        print("   建议至少配置 FINANCIAL_DATASETS_API_KEY 或 TUSHARE_TOKEN")
    
    return True


def check_api_connectivity():
    """检查API连接"""
    print("\n" + "="*70)
    print("检查4: API连接测试")
    print("="*70)
    
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / 'futu_backtest_trader' / '.env')
    
    # 测试美股API
    print("\n--- 测试美股API ---")
    if os.environ.get('FINANCIAL_DATASETS_API_KEY'):
        try:
            from data.financial_data import FinancialDatasetsAPI
            api = FinancialDatasetsAPI()
            df = api.get_stock_prices('AAPL', '2025-01-20', '2025-01-22')
            if df is not None and len(df) > 0:
                print(f"✅ 美股API连接正常（获取到{len(df)}条数据）")
            else:
                print("⚠️  美股API返回空数据")
        except Exception as e:
            print(f"❌ 美股API测试失败: {e}")
    else:
        print("⚪ 未配置美股API")
    
    # 测试A股API
    print("\n--- 测试A股API（Tushare）---")
    if os.environ.get('TUSHARE_TOKEN'):
        try:
            from data.tushare_data import TushareDataFetcher
            fetcher = TushareDataFetcher()
            df = fetcher.get_history_kline('600519', '2025-01-20', '2025-01-22')
            if df is not None and len(df) > 0:
                print(f"✅ Tushare API连接正常（获取到{len(df)}条数据）")
            else:
                print("⚠️  Tushare API返回空数据")
        except Exception as e:
            print(f"❌ Tushare测试失败: {e}")
    else:
        print("⚪ 未配置Tushare")
    
    # 测试AI API
    print("\n--- 测试AI API ---")
    if any([os.environ.get(k) for k in ['DEEPSEEK_API_KEY', 'OPENAI_API_KEY', 
                                         'CLAUDE_API_KEY', 'QWEN_API_KEY']]):
        try:
            from core.ai_analyzer import AIAnalyzer
            analyzer = AIAnalyzer()
            if analyzer.is_available():
                print(f"✅ AI功能可用")
                print(f"   可用模型: {', '.join(analyzer.available_models)}")
            else:
                print("⚠️  AI功能不可用")
        except Exception as e:
            print(f"❌ AI测试失败: {e}")
    else:
        print("⚪ 未配置AI API")
    
    return True


def check_core_modules():
    """检查核心模块"""
    print("\n" + "="*70)
    print("检查5: 核心模块")
    print("="*70)
    
    modules = [
        ('core.data_manager', 'DataManager', '数据管理器'),
        ('core.strategy_engine', 'StrategyEngine', '策略引擎'),
        ('core.scheduler', 'TaskScheduler', '任务调度器'),
        ('core.ai_analyzer', 'AIAnalyzer', 'AI分析器'),
    ]
    
    all_ok = True
    
    for module_name, class_name, desc in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"  ✅ {desc:15s} - {module_name}")
        except Exception as e:
            print(f"  ❌ {desc:15s} - 导入失败: {e}")
            all_ok = False
    
    return all_ok


def generate_report():
    """生成检查报告"""
    print("\n" + "="*70)
    print("系统配置检查报告")
    print("="*70)
    
    results = []
    
    # 运行所有检查
    results.append(("Python版本", check_python_version()))
    results.append(("依赖包", check_dependencies()))
    results.append(("环境配置", check_env_config()))
    results.append(("API连接", check_api_connectivity()))
    results.append(("核心模块", check_core_modules()))
    
    # 汇总
    print("\n" + "="*70)
    print("检查汇总")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:12s}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*70)
    print(f"总计: {len(results)} 项检查")
    print(f"通过: {passed} 项")
    print(f"失败: {failed} 项")
    print("="*70)
    
    if failed == 0:
        print("\n🎉 系统配置正常！可以开始使用。")
        print("\n下一步:")
        print("  1. 运行测试: python test_core.py")
        print("  2. 运行演示: python main.py")
    else:
        print(f"\n⚠️  有 {failed} 项检查失败。")
        print("\n建议:")
        print("  1. 检查Python版本（需要3.8+）")
        print("  2. 安装缺失的依赖: pip install -r requirements.txt")
        print("  3. 配置.env文件（参考QUICKSTART.md）")
        print("  4. 检查API密钥是否有效")
    
    return failed == 0


if __name__ == '__main__':
    try:
        success = generate_report()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 检查过程出错: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
