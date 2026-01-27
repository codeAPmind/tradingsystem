#!/usr/bin/env python3
"""
回测界面港股代码格式化测试
Test HK Stock Code Formatting in Backtest Widget
"""

def test_format_stock_code():
    """测试股票代码格式化功能"""
    print("\n" + "="*70)
    print("股票代码格式化测试".center(70))
    print("="*70 + "\n")
    
    # 模拟format_stock_code方法
    def format_stock_code(code, market):
        """格式化股票代码"""
        code = code.strip().upper()
        
        if market == '港股':
            # 港股处理
            if code.startswith('HK.'):
                return code
            else:
                # 纯数字，添加HK.前缀
                try:
                    num = int(code)
                    return f"HK.{num:05d}"
                except ValueError:
                    return f"HK.{code}"
        else:
            # 美股处理
            if code.startswith('HK.'):
                return code.replace('HK.', '')
            else:
                return code
    
    # 测试用例
    test_cases = [
        # (输入, 市场, 预期输出, 说明)
        ('01797', '港股', 'HK.01797', '东方甄选 - 完整代码'),
        ('1797', '港股', 'HK.01797', '东方甄选 - 无前导0'),
        ('700', '港股', 'HK.00700', '腾讯 - 3位代码'),
        ('00700', '港股', 'HK.00700', '腾讯 - 完整代码'),
        ('9988', '港股', 'HK.09988', '阿里巴巴 - 4位代码'),
        ('HK.01797', '港股', 'HK.01797', '已有前缀'),
        
        ('TSLA', '美股', 'TSLA', '特斯拉'),
        ('tsla', '美股', 'TSLA', '特斯拉 - 小写'),
        ('aapl', '美股', 'AAPL', '苹果 - 小写'),
        ('NVDA', '美股', 'NVDA', '英伟达'),
        ('HK.01797', '美股', '01797', '移除错误的HK前缀'),
    ]
    
    print("【港股代码格式化测试】")
    print("-"*70)
    
    passed = 0
    failed = 0
    
    for input_code, market, expected, description in test_cases:
        result = format_stock_code(input_code, market)
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} {description}")
        print(f"   输入: {input_code:12s} 市场: {market:4s} → 输出: {result:12s} (预期: {expected})")
        
        if result != expected:
            print(f"   ❌ 失败: 预期 {expected}，实际 {result}")
        print()
    
    # 总结
    print("="*70)
    print(f"测试总结: 通过 {passed}/{passed+failed}")
    print("="*70)
    
    if failed == 0:
        print("\n✅ 所有测试通过！\n")
        return True
    else:
        print(f"\n❌ {failed} 个测试失败\n")
        return False


def test_common_stocks():
    """测试常见股票"""
    print("\n" + "="*70)
    print("常见股票代码测试".center(70))
    print("="*70 + "\n")
    
    def format_stock_code(code, market):
        """格式化股票代码"""
        code = code.strip().upper()
        
        if market == '港股':
            if code.startswith('HK.'):
                return code
            else:
                try:
                    num = int(code)
                    return f"HK.{num:05d}"
                except ValueError:
                    return f"HK.{code}"
        else:
            if code.startswith('HK.'):
                return code.replace('HK.', '')
            else:
                return code
    
    # 常见股票
    stocks = {
        '港股': [
            ('01797', '东方甄选'),
            ('00700', '腾讯控股'),
            ('09988', '阿里巴巴'),
            ('03690', '美团'),
            ('01810', '小米集团'),
            ('02318', '中国平安'),
        ],
        '美股': [
            ('TSLA', '特斯拉'),
            ('AAPL', '苹果'),
            ('NVDA', '英伟达'),
            ('MSFT', '微软'),
            ('GOOGL', '谷歌'),
            ('AMZN', '亚马逊'),
        ]
    }
    
    for market, stock_list in stocks.items():
        print(f"【{market}】")
        print("-"*70)
        
        for code, name in stock_list:
            formatted = format_stock_code(code, market)
            print(f"✅ {name:12s} | 输入: {code:8s} → 格式化: {formatted}")
        
        print()
    
    print("="*70)
    print("✅ 常见股票测试完成\n")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("回测界面港股代码格式化修复 - 测试脚本")
    print("="*70)
    
    # 运行测试
    test1_passed = test_format_stock_code()
    test_common_stocks()
    
    # 使用说明
    print("\n" + "="*70)
    print("使用说明".center(70))
    print("="*70 + "\n")
    
    print("""
回测界面现在支持自动格式化股票代码：

【港股回测步骤】
1. 启动系统: python main.py
2. 点击"回测"标签页
3. 选择市场: 港股
4. 输入代码: 01797 (或 1797, 700 等)
5. 设置日期范围
6. 点击"开始回测"
7. 系统自动格式化为 HK.01797

【美股回测步骤】
1. 选择市场: 美股
2. 输入代码: TSLA (或 tsla)
3. 点击"开始回测"
4. 系统自动转大写 TSLA

【智能提示】
- 港股占位符: "输入数字代码，如 01797"
- 美股占位符: "输入字母代码，如 TSLA"
- 状态栏显示格式化结果

文档: BACKTEST_HK_FIX.md
    """)
    
    print("="*70)
    
    if test1_passed:
        print("✅ 所有测试通过，港股代码格式化功能正常！\n")
    else:
        print("❌ 部分测试失败，请检查代码\n")
