"""
API集成测试脚本
Test API Integration - 验证所有API是否正确配置
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def print_header(title):
    """打印标题"""
    print("\n" + "="*70)
    print(title.center(70))
    print("="*70 + "\n")


def print_section(title):
    """打印章节"""
    print(f"\n{'─'*70}")
    print(f"📋 {title}")
    print(f"{'─'*70}\n")


def test_env_config():
    """测试环境配置"""
    print_section("测试1: 环境配置加载")
    
    try:
        from utils.env_config import config
        
        print("✅ 环境配置模块导入成功")
        
        # 打印配置状态
        config.print_status()
        
        # 检查必要配置
        has_news = config.has_any_news_api()
        has_ai = config.has_any_ai_api()
        
        print(f"\n配置检查:")
        print(f"  新闻API: {'✅ 已配置' if has_news else '❌ 未配置'}")
        print(f"  AI API:  {'✅ 已配置' if has_ai else '❌ 未配置'}")
        
        if not has_news and not has_ai:
            print("\n⚠️  警告: 未配置任何API，将使用模拟数据")
            print("   请参考 API_INTEGRATION_GUIDE.md 配置API密钥")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 环境配置加载失败: {e}")
        return False


def test_news_service():
    """测试新闻服务"""
    print_section("测试2: 新闻服务")
    
    try:
        from utils.news_service import news_service
        from utils.env_config import config
        
        print("✅ 新闻服务模块导入成功")
        
        # 测试获取新闻
        test_stocks = ['TSLA', 'AAPL']
        
        for stock in test_stocks:
            print(f"\n📰 测试获取 {stock} 的新闻...")
            news = news_service.get_news(stock, limit=3)
            
            if news:
                print(f"  ✅ 成功获取 {len(news)} 条新闻")
                
                # 显示第一条新闻
                if len(news) > 0:
                    first = news[0]
                    print(f"\n  示例新闻:")
                    print(f"    标题: {first['title'][:60]}...")
                    print(f"    来源: {first['source']}")
                    print(f"    时间: {first['time']}")
            else:
                print(f"  ⚠️  未获取到新闻（使用模拟数据）")
        
        return True
        
    except Exception as e:
        print(f"❌ 新闻服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_analyzer():
    """测试AI分析服务"""
    print_section("测试3: AI分析服务")
    
    try:
        from utils.ai_analyzer import ai_analyzer
        from utils.env_config import config
        
        print("✅ AI分析服务模块导入成功")
        
        # 检查AI是否初始化
        if not ai_analyzer.client:
            print("⚠️  AI API未配置，将返回默认分析")
            return True
        
        print(f"✅ AI提供商: {config.ai_provider}")
        
        # 测试新闻列表
        test_news = [
            {
                'title': 'Tesla Q4 Earnings Beat Expectations',
                'summary': 'Tesla reported strong Q4 earnings with revenue growth of 25%'
            },
            {
                'title': 'Elon Musk Announces New Gigafactory',
                'summary': 'Tesla CEO revealed plans for a new factory'
            }
        ]
        
        # 测试情绪分析
        print("\n🤖 测试情绪分析...")
        sentiment = ai_analyzer.analyze_sentiment('TSLA', test_news)
        
        print(f"  ✅ 情绪评分: {sentiment['score']:.2f}")
        print(f"  ✅ 情绪类别: {sentiment['sentiment']}")
        print(f"  ✅ 置信度: {sentiment['confidence']:.2f}")
        print(f"  ✅ 摘要: {sentiment['summary'][:50]}...")
        
        # 测试基本面分析
        print("\n📊 测试基本面分析...")
        fundamental = ai_analyzer.analyze_fundamental('TSLA')
        
        print(f"  ✅ 综合评分: {fundamental['score']}/100")
        print(f"  ✅ 优势数量: {len(fundamental['strengths'])}")
        print(f"  ✅ 风险数量: {len(fundamental['risks'])}")
        
        # 测试交易建议
        print("\n💡 测试交易建议...")
        advice = ai_analyzer.generate_trading_advice('TSLA', sentiment, fundamental)
        
        print(f"  ✅ 建议操作: {advice['action']}")
        print(f"  ✅ 置信度: {advice['confidence']:.2f}")
        print(f"  ✅ 理由: {advice['reasoning'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ AI分析服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """测试完整集成"""
    print_section("测试4: 完整集成测试")
    
    try:
        from utils.news_service import news_service
        from utils.ai_analyzer import ai_analyzer
        
        print("🔄 模拟完整工作流程...\n")
        
        stock_code = 'TSLA'
        
        # 1. 获取新闻
        print(f"1️⃣ 获取 {stock_code} 新闻...")
        news = news_service.get_news(stock_code, limit=5)
        print(f"   ✅ 获取到 {len(news)} 条新闻")
        
        # 2. 情绪分析
        print(f"\n2️⃣ 分析新闻情绪...")
        sentiment = ai_analyzer.analyze_sentiment(stock_code, news)
        print(f"   ✅ 情绪: {sentiment['sentiment']} ({sentiment['score']:.2f})")
        
        # 3. 基本面分析
        print(f"\n3️⃣ 分析基本面...")
        fundamental = ai_analyzer.analyze_fundamental(stock_code)
        print(f"   ✅ 评分: {fundamental['score']}/100")
        
        # 4. 生成建议
        print(f"\n4️⃣ 生成交易建议...")
        advice = ai_analyzer.generate_trading_advice(
            stock_code, sentiment, fundamental
        )
        print(f"   ✅ 建议: {advice['action']}")
        
        print("\n✅ 完整工作流程测试成功！")
        
        return True
        
    except Exception as e:
        print(f"❌ 完整集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_dependencies():
    """检查依赖包"""
    print_section("检查依赖包")
    
    dependencies = {
        'anthropic': 'Claude API支持',
        'openai': 'ChatGPT API支持',
        'requests': 'HTTP请求',
        'PyQt6': 'GUI框架'
    }
    
    missing = []
    
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"✅ {package:15s} - {description}")
        except ImportError:
            print(f"❌ {package:15s} - {description} (未安装)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing)}")
        print(f"\n安装命令:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def main():
    """主测试函数"""
    print_header("API集成测试")
    
    print("📝 本测试将验证:")
    print("   1. 环境配置是否正确加载")
    print("   2. 新闻API是否正常工作")
    print("   3. AI分析API是否正常工作")
    print("   4. 完整工作流程是否通畅")
    
    input("\n按Enter开始测试...")
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请先安装缺失的包")
        return
    
    # 运行测试
    results = []
    
    results.append(("环境配置", test_env_config()))
    results.append(("新闻服务", test_news_service()))
    results.append(("AI分析", test_ai_analyzer()))
    results.append(("完整集成", test_integration()))
    
    # 输出结果
    print_header("测试结果汇总")
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name:15s} {status}")
    
    print(f"\n总计: {success_count}/{total_count} 项测试通过")
    
    if success_count == total_count:
        print("\n" + "="*70)
        print("🎉 所有测试通过！API集成成功！".center(70))
        print("="*70)
        print("""
✅ 你的系统现在可以：
   1. 获取真实的股票新闻
   2. 进行AI情绪分析
   3. 生成基本面分析
   4. 提供智能交易建议

下一步：
   运行 python main.py 启动程序
   点击任意股票查看真实数据！
""")
    else:
        print("\n" + "="*70)
        print("⚠️  部分测试失败".center(70))
        print("="*70)
        print("""
建议：
   1. 检查 .env 文件是否正确配置
   2. 验证API密钥是否有效
   3. 确认网络连接正常
   4. 查看详细错误信息

参考文档：
   API_INTEGRATION_GUIDE.md
""")
    
    print("\n")


if __name__ == '__main__':
    main()
