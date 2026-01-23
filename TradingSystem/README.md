# TradingSystem - 量化交易系统

基于VNPY设计理念的现代化量化交易系统，支持美股、港股、A股三大市场。

## ✨ 核心功能

### 🌍 三市场全支持
- **美股**: FinancialDatasets API
- **港股**: Futu OpenAPI
- **A股**: Tushare + 东方财富

### 🤖 AI分析引擎
支持5个AI模型：
- DeepSeek（推荐，便宜）
- ChatGPT（质量高）
- Claude（长文本）
- 通义千问（A股专家）
- 文心一言（金融专业）

### 📊 策略系统
- TSF-LSMA策略（已实现）
- MACD策略（待实现）
- RSI策略（待实现）
- 支持自定义策略

### ⏰ 自动化任务
- 每日信号生成
- 自动交易执行
- 定时任务调度

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入目录
cd F:\PyProjects\futu_backtest_trader\TradingSystem

# 安装基础依赖
pip install pandas numpy requests python-dotenv schedule

# 安装A股数据（可选）
pip install tushare

# 安装AI支持（可选）
pip install openai anthropic dashscope

# 安装港股支持（可选）
pip install futu-api
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env`，然后配置：

```bash
# ==================== 美股API ====================
FINANCIAL_DATASETS_API_KEY=your_key_here

# ==================== 港股API ====================
FUTU_HOST=127.0.0.1
FUTU_PORT=11111

# ==================== A股API ====================
# Tushare Token（推荐）
TUSHARE_TOKEN=your_tushare_token

# ==================== AI模型（可选）====================
# DeepSeek（推荐，便宜）
DEEPSEEK_API_KEY=sk-xxx

# ChatGPT
OPENAI_API_KEY=sk-xxx

# 通义千问（推荐用于A股）
QWEN_API_KEY=sk-xxx
```

### 3. 运行测试

```bash
# 测试核心功能
python test_core.py
```

### 4. 使用示例

#### 数据获取

```python
from core.data_manager import DataManager

manager = DataManager()

# 美股
df = manager.get_kline_data('TSLA', '2025-01-01', '2025-01-22')

# 港股
df = manager.get_kline_data('HK.01797', '2025-01-01', '2025-01-22')

# A股
df = manager.get_kline_data('600519', '2025-01-01', '2025-01-22')
```

#### 策略分析

```python
from core.strategy_engine import StrategyEngine

engine = StrategyEngine()

# 激活策略
engine.activate_strategy('TSLA', 'TSF-LSMA', {
    'tsf_period': 9,
    'lsma_period': 20,
    'buy_threshold_pct': 0.5,
    'sell_threshold_pct': 0.5
})

# 生成信号
signals = engine.generate_signal('TSLA', df)
```

#### AI分析

```python
from core.ai_analyzer import AIAnalyzer

analyzer = AIAnalyzer(primary_model='deepseek')

# 技术分析
result = analyzer.analyze('technical', """
股票: TSLA
TSF: $425.0
LSMA: $415.0
趋势: 上涨
""")
```

#### 定时任务

```python
from core.scheduler import TaskScheduler

scheduler = TaskScheduler(data_manager, strategy_engine)

# 添加每日信号任务
scheduler.add_daily_signal_task(
    stock_code='TSLA',
    time_str='04:10',  # 美股收盘后
    strategy_name='TSF-LSMA',
    params={'buy_threshold_pct': 0.5}
)

# 启动调度器
scheduler.start()
```

## 📁 项目结构

```
TradingSystem/
├── core/                      # 核心引擎
│   ├── data_manager.py       # 统一数据管理
│   ├── strategy_engine.py    # 策略引擎
│   ├── scheduler.py          # 任务调度
│   └── ai_analyzer.py        # AI分析
│
├── data/                      # 数据源
│   ├── tushare_data.py       # A股数据
│   ├── eastmoney_data.py     # 东方财富
│   └── financial_data.py     # 美股数据（参考futu_backtest_trader）
│
├── ui/                        # UI界面（待实现）
│
├── test_core.py              # 核心功能测试
├── main.py                   # 主程序
└── README.md                 # 本文件
```

## 🔧 配置说明

### 美股API（必需）
- 注册：https://financialdatasets.ai
- 获取API Key
- 配置：`FINANCIAL_DATASETS_API_KEY`

### 港股API（可选）
- 下载Futu OpenD：https://www.futunn.com
- 启动OpenD
- 配置：`FUTU_HOST`和`FUTU_PORT`

### A股API（可选）
- 注册Tushare：https://tushare.pro/register
- 获取Token
- 配置：`TUSHARE_TOKEN`

### AI模型（可选）
根据需要配置一个或多个：

1. **DeepSeek**（推荐）
   - 注册：https://platform.deepseek.com
   - 成本：¥0.001/千tokens
   - 适用：技术分析、信号确认

2. **ChatGPT**
   - 注册：https://platform.openai.com
   - 成本：$0.01/千tokens
   - 适用：基本面分析、新闻解读

3. **通义千问**（推荐用于A股）
   - 注册：https://dashscope.aliyun.com
   - 成本：¥0.002/千tokens
   - 适用：A股分析、政策解读

## ⚠️ 注意事项

### 数据源依赖
- **美股**：需要FinancialDatasets API（免费额度有限）
- **港股**：需要Futu OpenD运行
- **A股**：需要Tushare Token

### AI功能
- AI分析是可选功能
- 未配置API时，系统仍可正常使用
- 建议至少配置一个便宜的模型（如DeepSeek）

### 实盘交易
- 当前版本仅支持信号生成
- 实盘交易功能待实现
- 建议先在模拟盘测试

## 📊 测试结果

运行 `python test_core.py` 后，你应该看到：

```
✅ 数据管理器测试完成
✅ 策略引擎测试完成
✅ 任务调度器测试完成
✅ AI分析器测试完成
✅ Tushare测试完成
✅ 东方财富测试完成

🎉 所有测试通过！系统核心功能正常。
```

## 🎯 下一步

1. ✅ 核心功能已实现
2. 🚧 UI界面开发中
3. 📝 实盘交易待实现
4. 📈 更多策略待添加

## 💡 使用技巧

### 1. 数据缓存
系统自动缓存获取的数据，避免重复API调用：
```python
# 使用缓存（默认）
df = manager.get_kline_data('TSLA', start, end, use_cache=True)

# 强制更新
df = manager.get_kline_data('TSLA', start, end, force_update=True)
```

### 2. 策略参数
根据不同股票调整参数：
```python
# 美股（波动大）
params = {'buy_threshold_pct': 0.5, 'sell_threshold_pct': 0.5}

# A股（波动中等）
params = {'buy_threshold_pct': 0.9, 'sell_threshold_pct': 4.0}
```

### 3. AI成本控制
- 技术分析：使用DeepSeek（便宜）
- 基本面分析：使用ChatGPT/Claude（质量高）
- A股分析：使用通义千问（中文好）

## 📞 获取帮助

如有问题，请检查：
1. 环境变量是否正确配置
2. 依赖是否完整安装
3. API密钥是否有效
4. Futu OpenD是否运行（港股）

## 📄 许可证

MIT License

---

**Happy Trading! 📈💰**
