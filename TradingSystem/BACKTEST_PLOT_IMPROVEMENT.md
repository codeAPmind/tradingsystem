# 回测绘图功能改进

## ✅ 已完成的改进

### 1. 策略中记录买卖信号 ✅
- 在 `TSFLSMAStrategy` 中添加了 `buy_signals` 和 `sell_signals` 列表
- 在 `next()` 方法中，当触发买卖信号时记录日期和价格

### 2. 改进的 `plot()` 方法 ✅
- 支持自定义买卖信号颜色
- 使用 backtrader 内置绘图功能，自动标注买卖信号
- 参数：
  - `style`: 图表样式（'candlestick', 'line'等）
  - `show_signals`: 是否显示买卖信号标注

### 3. 新增 `plot_with_custom_signals()` 方法 ✅
- 使用 matplotlib 自定义绘制详细的K线图
- 功能：
  - K线图（绿色阳线，红色阴线）
  - TSF和LSMA指标线
  - 买入信号标注（绿色向上箭头 + 文字标注）
  - 卖出信号标注（红色向下箭头 + 文字标注）
  - 成交量柱状图
  - 暗色主题（适合长时间查看）

## 📊 使用方法

### 方法1：使用 backtrader 内置绘图（简单）

```python
from core.backtest_engine import BacktestEngine
from strategies.backtrader_tsf_lsma import TSFLSMAStrategy
from core.data_manager import DataManager

# 初始化
data_manager = DataManager()
engine = BacktestEngine(initial_cash=100000.0)

# 获取数据
df = data_manager.get_kline_data('TSLA', '2024-01-01', '2025-01-22')

# 添加数据和策略
engine.add_data_from_dataframe(df, 'TSLA')
engine.add_strategy(TSFLSMAStrategy, 
                   tsf_period=9, 
                   lsma_period=20,
                   buy_threshold=0.5,
                   sell_threshold=0.5)

# 运行回测
result = engine.run()

# 绘制图表（带买卖信号）
engine.plot(style='candlestick', show_signals=True)
```

### 方法2：使用自定义绘图（详细）

```python
# 运行回测后
result = engine.run()

# 绘制详细图表
engine.plot_with_custom_signals(save_path='backtest_result.png')
```

## 🎨 图表特点

### backtrader 内置绘图
- ✅ 自动标注买卖信号
- ✅ 支持多种样式
- ✅ 快速生成
- ✅ 颜色可自定义

### 自定义绘图
- ✅ 详细的K线图
- ✅ TSF/LSMA指标叠加
- ✅ 清晰的买卖信号标注
- ✅ 成交量显示
- ✅ 暗色主题
- ✅ 可保存为图片

## 📝 买卖信号记录

策略会自动记录：
- **买入信号**: `(date, price)` 元组列表
- **卖出信号**: `(date, price)` 元组列表

这些信号会在回测结果中返回，可用于：
- 绘制图表标注
- 分析交易时机
- 生成交易报告

## 🔧 技术实现

### 策略中记录信号
```python
# 在策略的 next() 方法中
if diff > buy_threshold:
    current_date = self.data.datetime.date(0)
    current_price = self.data.close[0]
    self.buy_signals.append((current_date, current_price))
```

### 回测结果中包含信号
```python
result = {
    'buy_signals': [(date, price), ...],
    'sell_signals': [(date, price), ...],
    ...
}
```

### 绘图时使用信号
```python
# 从策略获取信号
if hasattr(strat, 'buy_signals'):
    buy_signals = strat.buy_signals

# 在图表上标注
ax1.scatter(date, price, color='green', marker='^', s=200)
ax1.annotate('买入', xy=(date, price), ...)
```

## 🎯 后续改进建议

- [ ] 支持更多指标叠加（MACD、RSI等）
- [ ] 支持多策略对比图表
- [ ] 交互式图表（使用plotly）
- [ ] 导出PDF报告
- [ ] 图表模板自定义

---

**绘图功能已改进！现在可以清晰地看到买卖信号标注了！** 🎉
