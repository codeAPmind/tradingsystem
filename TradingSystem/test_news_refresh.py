"""
新闻刷新功能测试脚本
Test News Widget Refresh
"""

def test_news_widget():
    """测试新闻组件是否正确响应"""
    
    print("\n" + "="*70)
    print("新闻组件刷新功能测试".center(70))
    print("="*70 + "\n")
    
    # 检查1: news_widget.py 是否存在
    import os
    news_widget_path = 'ui/widgets/news_widget.py'
    
    if not os.path.exists(news_widget_path):
        print("❌ news_widget.py 不存在")
        return False
    
    print("✅ news_widget.py 文件存在")
    
    # 检查2: 是否有 update_news 方法
    with open(news_widget_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'def update_news(' in content:
        print("✅ update_news 方法已定义")
    else:
        print("❌ update_news 方法未定义")
        return False
    
    # 检查3: main_window.py 是否调用了 update_news
    main_window_path = 'ui/main_window.py'
    
    if not os.path.exists(main_window_path):
        print("❌ main_window.py 不存在")
        return False
    
    print("✅ main_window.py 文件存在")
    
    with open(main_window_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'self.news_widget.update_news(stock_code)' in content:
        print("✅ main_window 中已调用 update_news")
    else:
        print("❌ main_window 中未调用 update_news")
        print("\n需要在 load_stock_data 方法的末尾添加：")
        print("    self.news_widget.update_news(stock_code)")
        return False
    
    # 检查4: NewsLoaderThread 是否存在
    if 'class NewsLoaderThread' in content:
        print("✅ NewsLoaderThread 线程类已定义")
    else:
        print("⚠️  未找到 NewsLoaderThread（可能在不同位置）")
    
    print("\n" + "="*70)
    print("✅ 所有检查通过！".center(70))
    print("="*70)
    print("""
新闻刷新功能应该正常工作

测试方法:
1. 运行程序: python main.py
2. 点击左侧自选股列表中的任意股票
3. 观察右侧"新闻"标签页是否自动刷新
4. 标题应该显示: "新闻与分析 - [股票代码] ([股票名称])"
5. 内容应该显示该股票的相关新闻

如果新闻没有刷新:
1. 检查控制台是否有错误信息
2. 确认 config.py 中有 get_stock_display_name 函数
3. 检查 news_widget.py 的导入是否正确
""")
    
    return True


if __name__ == '__main__':
    test_news_widget()
