# 环境设置完成 ✅

## 已完成的工作

### 1. Conda环境创建 ✅
- 环境名称: `trading_system`
- Python版本: 3.10
- 位置: `C:\Users\xiwen\AppData\Local\anaconda3\envs\trading_system`

### 2. 依赖安装 ✅
已成功安装所有依赖包：
- ✅ pandas, numpy, requests
- ✅ python-dotenv, schedule
- ✅ tushare (A股数据)
- ✅ openai (AI支持)
- ✅ PyQt6 (UI界面)
- ✅ loguru, orjson

### 3. 系统测试 ✅
系统核心功能已正常运行：
- ✅ 数据管理器初始化
- ✅ 策略引擎初始化（TSF-LSMA, MACD, RSI）
- ✅ 任务调度器初始化
- ✅ AI分析器初始化

## 🚀 使用方法

### 方式1: 使用批处理文件（推荐）

```bash
# 启动UI界面
start_ui.bat

# 运行演示
start_demo.bat
```

### 方式2: 手动启动

```bash
# 激活环境
conda activate trading_system

# 启动UI
python main.py --ui

# 或运行演示
python main.py --demo
```

## ⚙️ 配置说明

### 当前状态
- ⚠️ Futu未安装（港股数据不可用，可选）
- ⚠️ FinancialDatasets未配置（美股数据需要API密钥）
- ⚠️ Tushare未配置（A股数据需要token）

### 配置API密钥

在项目根目录创建`.env`文件：

```bash
# 美股数据（FinancialDatasets）
FINANCIAL_DATASETS_API_KEY=your_api_key_here

# A股数据（Tushare）
# 获取地址: https://tushare.pro/register
TUSHARE_TOKEN=your_token_here

# AI分析（可选，至少配置一个）
DEEPSEEK_API_KEY=sk-your-key
OPENAI_API_KEY=sk-your-key
CLAUDE_API_KEY=sk-ant-your-key
QWEN_API_KEY=sk-your-key
ERNIE_API_KEY=your-key
ERNIE_SECRET_KEY=your-secret
```

### 安装可选依赖

```bash
# 港股支持（需要Futu OpenD）
conda activate trading_system
pip install futu-api

# 其他AI支持
pip install anthropic    # Claude
pip install dashscope    # 通义千问
```

## 📊 功能状态

| 功能模块 | 状态 | 说明 |
|---------|------|------|
| 数据管理 | ✅ | 核心架构完成 |
| 策略引擎 | ✅ | TSF-LSMA, MACD, RSI已实现 |
| 任务调度 | ✅ | 定时任务框架完成 |
| AI分析 | ✅ | 5个模型支持 |
| UI界面 | ✅ | PyQt6界面完成 |
| 美股数据 | ⚠️ | 需要API密钥 |
| 港股数据 | ⚠️ | 需要安装futu-api |
| A股数据 | ⚠️ | 需要Tushare token |

## 🎯 下一步

1. **配置API密钥**：在`.env`文件中添加数据源API密钥
2. **测试数据获取**：运行`python main.py --demo`测试数据获取
3. **启动UI界面**：运行`python main.py --ui`查看图形界面
4. **配置策略**：在UI中配置交易策略参数

## 📝 注意事项

1. **编码问题**：Windows控制台已配置UTF-8编码支持
2. **路径问题**：已修复导入路径，确保使用当前项目的模块
3. **可选依赖**：Futu、Tushare等是可选的，不影响核心功能

## 🆘 故障排除

### 如果遇到导入错误
```bash
# 确保在正确的目录
cd F:\PyProjects\futu_backtest_trader\TradingSystem

# 确保环境已激活
conda activate trading_system
```

### 如果UI无法启动
```bash
# 检查PyQt6是否安装
pip show PyQt6

# 重新安装
pip install PyQt6
```

### 如果数据获取失败
- 检查`.env`文件中的API密钥是否正确
- 检查网络连接
- 查看控制台错误信息

---

**环境设置完成！可以开始使用系统了！** 🎉
