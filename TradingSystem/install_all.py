"""
一键安装所有推荐依赖
适合快速开始使用
"""
import subprocess
import sys

def install_packages():
    """安装所有推荐的包"""
    
    # 要安装的包（核心+A股+AI）
    packages = [
        'pandas>=2.0.0',
        'numpy>=1.24.0', 
        'requests>=2.31.0',
        'python-dotenv>=1.0.0',
        'schedule>=1.2.0',
        'tushare>=1.4.0',
        'openai>=1.12.0',
        'loguru>=0.7.0'
    ]
    
    print("="*70)
    print("TradingSystem - 一键安装所有推荐依赖")
    print("="*70)
    print()
    print("将要安装以下包:")
    for pkg in packages:
        print(f"  - {pkg}")
    print()
    
    # 升级pip
    print("正在升级pip...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
    print()
    
    # 安装所有包
    print("正在安装依赖包...")
    cmd = [sys.executable, '-m', 'pip', 'install'] + packages
    result = subprocess.run(cmd)
    
    print()
    print("="*70)
    
    if result.returncode == 0:
        print("✅ 安装成功！")
        print()
        print("已安装:")
        print("  ✅ 核心依赖（pandas, numpy, requests, python-dotenv, schedule）")
        print("  ✅ A股数据支持（tushare）")
        print("  ✅ AI分析支持（openai - 支持DeepSeek/ChatGPT）")
        print("  ✅ 工具库（loguru）")
        print()
        print("下一步:")
        print("  1. 配置 .env 文件（参考父目录的.env）")
        print("  2. 运行检查: python check_system.py")
        print("  3. 运行测试: python test_core.py")
        return 0
    else:
        print("❌ 安装失败")
        print()
        print("请尝试手动安装:")
        print("  pip install " + " ".join(packages))
        return 1

if __name__ == '__main__':
    try:
        exit(install_packages())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户取消安装")
        exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
