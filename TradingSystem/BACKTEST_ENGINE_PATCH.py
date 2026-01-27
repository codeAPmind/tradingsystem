# backtest_engine.py 修复补丁
# 修复 add_data_from_dataframe 方法中的 date 处理

"""
在第94行左右，替换此部分:

# === 原代码（有问题）===
df_bt = df.copy()
if not isinstance(df_bt.index, pd.DatetimeIndex):
    df_bt = df_bt.set_index('date')

# === 新代码（修复后）===
df_bt = df.copy()

# 关键修复：先将date列转换为datetime类型
if 'date' in df_bt.columns:
    df_bt['date'] = pd.to_datetime(df_bt['date'])
    print(f"   ✅ Date列已转换为datetime类型")

# 然后设置为索引
if not isinstance(df_bt.index, pd.DatetimeIndex):
    df_bt = df_bt.set_index('date')

# 验证DatetimeIndex
if not isinstance(df_bt.index, pd.DatetimeIndex):
    raise ValueError("无法将date转换为DatetimeIndex")

print(f"   数据行数: {len(df_bt)}")
print(f"   日期范围: {df_bt.index[0].date()} ~ {df_bt.index[-1].date()}")

"""

# === 使用说明 ===
# 1. 打开 F:\PyProjects\新建文件夹\tradingsystem\TradingSystem\core\backtest_engine.py
# 2. 找到 add_data_from_dataframe 方法（约第68行）
# 3. 找到 df_bt = df.copy() 这一行（约第94行）
# 4. 用上面的"新代码"替换"原代码"部分
# 5. 保存文件

# === 完整的 add_data_from_dataframe 方法（修复后）===

def add_data_from_dataframe(self, df: pd.DataFrame, stock_code: str = ""):
    """
    从DataFrame添加数据
    
    Parameters:
    -----------
    df : DataFrame
        K线数据，必须包含: date, open, high, low, close, volume
    stock_code : str
        股票代码（用于标识）
    """
    if df is None or len(df) == 0:
        raise ValueError("数据为空")
    
    # 确保有date列
    if 'date' not in df.columns:
        raise ValueError("数据必须包含'date'列")
    
    # 准备数据
    df_bt = df.copy()
    
    # === 关键修复：将date列转换为datetime类型 ===
    if 'date' in df_bt.columns:
        df_bt['date'] = pd.to_datetime(df_bt['date'])
        print(f"   ✅ Date列已转换为datetime类型")
    
    # 设置日期为索引
    if not isinstance(df_bt.index, pd.DatetimeIndex):
        df_bt = df_bt.set_index('date')
    
    # 验证DatetimeIndex
    if not isinstance(df_bt.index, pd.DatetimeIndex):
        raise ValueError("无法将date转换为DatetimeIndex")
    
    # 确保列名正确
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df_bt.columns:
            raise ValueError(f"数据必须包含'{col}'列")
    
    # 转换为数值类型
    for col in required_cols:
        df_bt[col] = pd.to_numeric(df_bt[col], errors='coerce')
    
    # 删除NaN行
    df_bt = df_bt.dropna()
    
    if len(df_bt) == 0:
        raise ValueError("数据清洗后为空")
    
    print(f"   数据行数: {len(df_bt)}")
    print(f"   日期范围: {df_bt.index[0].date()} ~ {df_bt.index[-1].date()}")
    
    # 创建backtrader数据源
    data_feed = bt.feeds.PandasData(
        dataname=df_bt,
        datetime=None,  # 使用索引作为日期
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest=-1
    )
    
    self.cerebro.adddata(data_feed, name=stock_code)
    print(f"✅ 已添加数据: {stock_code} ({len(df_bt)}条)")
