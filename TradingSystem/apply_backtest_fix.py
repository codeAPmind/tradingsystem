#!/usr/bin/env python3
"""
自动修复 backtest_engine.py 中的 date 处理问题
Auto-fix date handling in backtest_engine.py
"""
import os
import sys

def apply_patch():
    """应用修复补丁"""
    
    file_path = 'core/backtest_engine.py'
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    print("📝 读取原文件...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经修复过
    if "pd.to_datetime(df_bt['date'])" in content:
        print("✅ 文件已经修复过了，无需重复修复")
        return True
    
    # 定义需要替换的代码
    old_code = """        # 设置日期为索引
        df_bt = df.copy()
        if not isinstance(df_bt.index, pd.DatetimeIndex):
            df_bt = df_bt.set_index('date')"""
    
    new_code = """        # 准备数据
        df_bt = df.copy()
        
        # 关键修复：将date列转换为datetime类型
        if 'date' in df_bt.columns:
            df_bt['date'] = pd.to_datetime(df_bt['date'])
            print(f"   ✅ Date列已转换为datetime类型")
        
        # 设置日期为索引
        if not isinstance(df_bt.index, pd.DatetimeIndex):
            df_bt = df_bt.set_index('date')
        
        # 验证DatetimeIndex
        if not isinstance(df_bt.index, pd.DatetimeIndex):
            raise ValueError("无法将date转换为DatetimeIndex")
        
        print(f"   数据行数: {len(df_bt)}")
        print(f"   日期范围: {df_bt.index[0].date()} ~ {df_bt.index[-1].date()}")"""
    
    # 检查旧代码是否存在
    if old_code not in content:
        print("⚠️  未找到需要替换的代码片段")
        print("   可能文件已被修改，请手动检查")
        return False
    
    # 应用补丁
    print("🔧 应用修复补丁...")
    content = content.replace(old_code, new_code)
    
    # 备份原文件
    backup_path = file_path + '.backup'
    print(f"💾 备份原文件到: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(open(file_path, 'r', encoding='utf-8').read())
    
    # 写入修复后的文件
    print("✍️  写入修复后的文件...")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 修复完成！")
    print(f"   原文件已备份到: {backup_path}")
    print(f"   如有问题，可以用备份文件恢复")
    
    return True


def show_help():
    """显示帮助信息"""
    print("""
回测引擎修复工具
================

功能:
  自动修复 backtest_engine.py 中的 date 处理问题
  
问题:
  backtrader需要DatetimeIndex，但数据中的date是字符串
  错误: 'str' object has no attribute 'to_pydatetime'
  
修复:
  在设置索引前，先将date列转换为datetime类型
  
使用方法:
  python apply_backtest_fix.py
  
注意:
  - 会自动备份原文件
  - 如果已经修复过，会跳过
  - 可以用备份文件恢复
    """)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("回测引擎 Date处理 修复工具".center(70))
    print("="*70 + "\n")
    
    if '--help' in sys.argv or '-h' in sys.argv:
        show_help()
        sys.exit(0)
    
    success = apply_patch()
    
    if success:
        print("\n" + "="*70)
        print("修复成功！".center(70))
        print("="*70)
        print("""
✅ backtest_engine.py 已修复

现在可以:
1. 运行回测: python main.py
2. 测试修复: python test_backtest_complete.py

修复内容:
- date列会自动转换为datetime类型
- 转换后设置为DatetimeIndex
- 增加了验证和日志输出
""")
    else:
        print("\n" + "="*70)
        print("修复失败".center(70))
        print("="*70)
        print("""
❌ 修复未成功应用

可能原因:
1. 文件不存在
2. 文件已被修改
3. 代码结构不匹配

建议:
1. 检查文件路径
2. 查看 BACKTEST_ENGINE_PATCH.py 手动修复
3. 或使用备份文件恢复
""")
    
    print("\n")
