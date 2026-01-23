# TradingSystem 快速开始指南

## 🎯 5分钟快速上手

### Step 1: 检查环境

```bash
# 确认Python版本（需要3.8+）
python --version

# 进入项目目录
cd F:\PyProjects\futu_backtest_trader\TradingSystem
```

### Step 2: 安装基础依赖

```bash
# 必需依赖
pip install pandas numpy requests python-dotenv schedule

# 可选：A股支持
pip install tushare

# 可选：AI支持（至少装一个）
pip install openai        # DeepSeek/ChatGPT
pip install anthropic     # Claude
pip install dashscope     # 通义千问
```

### Step 3: 配置API密钥

创建 `.env` 文件（参考父目录的 `.env`）：

```bash
# 美股API（必需）
FINANCIAL_DATASETS_API_KEY=your_key_here

# A股API（可选）
TUSHARE_TOKEN=your_token_here

# AI API（可选，推荐DeepSeek）
DEEPSEEK_API_KEY=sk-your-key
```

获取API密钥：
- **美股API**: https://financialdatasets.ai （注册免费）
- **Tushare**: https://tushare.pro/register （注册免费）
- **DeepSeek**: https://platform.deepseek.com （注册免费，便宜）

### Step 4: 运行测试

```bash
# 测试所有核心功能
python test_core.py
```

期望输出：
```
✅ 数据管理器测试完成
✅ 策略引擎测试完成
✅ 任务调度器测试完成
✅ AI分析器测试完成
✅ Tushare测试完成
✅ 东方财富测试完成

🎉 所有测试通过！系统核心功能正常。
```

### Step 5: 运行演示

```bash
# 运行完整演示
python main.py

# 或交互模式
python main.py --interactive
```

## 📚 基础使用示例

### 示例1: 获取股票数据

```python
from core.data_manager import DataManager

manager = DataManager()

# 美股
df = manager.get_kline_data('TSLA', '2025-01-01', '2025-01-22')
print(df.tail())

# A股（需要Tushare）
df = manager.get_kline_data('600519', '2025-01-01', '2025-01-22')
print(df.tail())
```

### 示例2: 生成交易信号

```python
from core.data_manager import DataManager
from core.strategy_engine import StrategyEngine

manager = DataManager()
engine = StrategyEngine()

# 激活策略
engine.activate_strategy('TSLA', 'TSF-LSMA', {
    'tsf_period': 9,
    'lsma_period': 20,
    'buy_threshold_pct': 0.5,
    'sell_threshold_pct': 0.5
})

# 获取数据并生成信号
df = manager.get_kline_data('TSLA', '2024-12-01', '2025-01-22')
signals = engine.generate_signal('TSLA', df)

for signal in signals:
    print(f"信号: {signal['type']}")
    print(f"原因: {signal['reason']}")
    print(f"当前价: ${signal['current_price']:.2f}")
```

### 示例3: 添加定时任务

```python
from core.scheduler import TaskScheduler

scheduler = TaskScheduler(data_manager, strategy_engine)

# 添加每日信号任务（美股收盘后04:10）
scheduler.add_daily_signal_task(
    stock_code='TSLA',
    time_str='04:10',
    strategy_name='TSF-LSMA',
    params={'buy_threshold_pct': 0.5}
)

# 手动测试任务
scheduler.run_task_now('signal_TSLA_0410')

# 启动后台调度（可选）
# scheduler.start()
```

### 示例4: AI分析

```python
from core.ai_analyzer import AIAnalyzer

analyzer = AIAnalyzer(primary_model='deepseek')

if analyzer.is_available():
    # 技术分析
    result = analyzer.analyze('technical', """
    股票: TSLA
    当前价: $420.0
    TSF: $425.0
    LSMA: $415.0
    趋势: 上涨
    """)
    
    print(result)
else:
    print("请配置AI API密钥")
```

## 🔧 常见问题

### Q1: 测试失败怎么办？

**A**: 检查以下几点：
1. Python版本是否3.8+
2. 依赖是否完整安装
3. `.env`文件是否正确配置
4. API密钥是否有效

### Q2: A股数据获取失败？

**A**: 
1. 确认已安装tushare: `pip install tushare`
2. 确认已配置`TUSHARE_TOKEN`
3. Token获取：https://tushare.pro/register

### Q3: 港股数据获取失败？

**A**:
1. 确认Futu OpenD已启动
2. 确认OpenD配置正确（默认127.0.0.1:11111）
3. 检查OpenD日志

### Q4: AI功能不可用？

**A**:
1. AI功能是可选的，不影响核心功能
2. 至少配置一个AI API密钥
3. 推荐使用DeepSeek（便宜且好用）

### Q5: 如何修改策略参数？

**A**:
```python
# 修改买卖阈值
params = {
    'tsf_period': 9,
    'lsma_period': 20,
    'buy_threshold_pct': 0.5,   # 买入阈值
    'sell_threshold_pct': 0.5,  # 卖出阈值
    'use_percent': True          # 使用百分比
}

engine.activate_strategy('TSLA', 'TSF-LSMA', params)
```

## 📊 数据源说明

### 美股
- **数据源**: FinancialDatasets API
- **优势**: 数据准确、免费额度
- **限制**: 有请求限制
- **缓存**: 自动缓存，减少API调用

### 港股
- **数据源**: Futu OpenAPI
- **优势**: 实时数据、稳定
- **要求**: 需要Futu OpenD运行
- **费用**: 免费

### A股
- **数据源**: Tushare（历史）+ 东方财富（实时）
- **优势**: 数据全面、免费
- **要求**: 需要注册Token
- **特色**: 支持资金流向

## 🤖 AI模型选择

### DeepSeek（推荐）
- ✅ 便宜：¥0.001/千tokens
- ✅ 速度快
- ✅ 适合技术分析
- 注册：https://platform.deepseek.com

### ChatGPT
- ✅ 质量高
- ✅ 理解力强
- ⚠️ 稍贵：$0.01/千tokens
- 注册：https://platform.openai.com

### 通义千问（A股推荐）
- ✅ 中文理解好
- ✅ A股专业
- ✅ 便宜：¥0.002/千tokens
- 注册：https://dashscope.aliyun.com

## 📈 策略参数调优

### 美股（波动大）
```python
params = {
    'buy_threshold_pct': 0.5,   # 较小阈值
    'sell_threshold_pct': 0.5
}
```

### A股（波动中等）
```python
params = {
    'buy_threshold_pct': 0.9,   # 较大阈值
    'sell_threshold_pct': 4.0
}
```

### 港股（参考美股）
```python
params = {
    'buy_threshold_pct': 0.5,
    'sell_threshold_pct': 0.5
}
```

## 🎯 下一步

1. ✅ 完成基础配置和测试
2. 📊 添加更多策略
3. 🤖 配置AI分析
4. ⏰ 设置定时任务
5. 🖥️ 等待UI界面

## 💡 提示

### 性能优化
- 使用缓存减少API调用
- 批量处理多只股票
- 定时任务在后台运行

### 成本控制
- 优先使用缓存数据
- AI分析使用DeepSeek
- 避免频繁API调用

### 安全建议
- 不要分享API密钥
- 定期更换密钥
- 先在模拟盘测试

## 📞 需要帮助？

1. 查看 `README.md` 详细文档
2. 运行 `python test_core.py` 诊断问题
3. 检查日志输出

---

**祝交易顺利！** 📈💰
