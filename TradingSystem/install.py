"""
TradingSystem 依赖安装脚本
自动安装所需的Python包
"""
import subprocess
import sys

def run_pip(packages):
    """运行pip安装"""
    cmd = [sys.executable, '-m', 'pip', 'install'] + packages
    print(f"执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0

def main():
    print("="*70)
    print("TradingSystem 依赖安装程序")
    print("="*70)
    print()
    
    # 升级pip
    print("[1/4] 升级pip...")
    run_pip(['--upgrade', 'pip'])
    print()
    
    # 核心依赖
    print("[2/4] 安装核心依赖（必需）...")
    core_packages = [
        'pandas>=2.0.0',
        'numpy>=1.24.0',
        'requests>=2.31.0',
        'python-dotenv>=1.0.0',
        'schedule>=1.2.0'
    ]
    
    success = run_pip(core_packages)
    if not success:
        print("❌ 核心依赖安装失败")
        return 1
    print("✅ 核心依赖安装完成")
    print()
    
    # A股支持
    print("[3/4] 安装A股数据支持（推荐）...")
    response = input("是否安装Tushare？(Y/n): ").strip().lower()
    if response != 'n':
        success = run_pip(['tushare>=1.4.0'])
        if success:
            print("✅ Tushare安装完成")
        else:
            print("⚠️  Tushare安装失败（可跳过）")
    else:
        print("⚪ 跳过Tushare安装")
    print()
    
    # AI支持
    print("[4/4] 安装AI分析支持（推荐）...")
    print("推荐安装OpenAI SDK（支持DeepSeek和ChatGPT）")
    response = input("是否安装？(Y/n): ").strip().lower()
    if response != 'n':
        success = run_pip(['openai>=1.12.0'])
        if success:
            print("✅ OpenAI SDK安装完成")
        else:
            print("⚠️  OpenAI SDK安装失败（可跳过）")
    else:
        print("⚪ 跳过AI支持安装")
    print()
    
    # 可选：工具库
    print("安装可选工具库（loguru, orjson）...")
    response = input("是否安装？(y/N): ").strip().lower()
    if response == 'y':
        run_pip(['loguru>=0.7.0', 'orjson>=3.9.0'])
    print()
    
    # 完成
    print("="*70)
    print("安装完成！")
    print("="*70)
    print()
    print("下一步:")
    print("  1. 配置 .env 文件")
    print("  2. 运行检查: python check_system.py")
    print("  3. 运行测试: python test_core.py")
    print("  4. 运行演示: python main.py")
    print()
    print("详细说明请查看 QUICKSTART.md")
    
    return 0

if __name__ == '__main__':
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n用户取消安装")
        exit(1)
    except Exception as e:
        print(f"\n❌ 安装过程出错: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
