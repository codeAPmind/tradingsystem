# TradingSystem 项目文件索引

## 📁 完整文件列表  test

```
TradingSystem/
│
├── 📄 核心程序
│   ├── main.py                    主程序入口（命令行界面）
│   ├── test_system.py             系统测试脚本
│   └── check_system.py            系统状态检查
│
├── 📄 配置和文档
│   ├── .env.example               环境变量示例
│   ├── requirements.txt           依赖列表
│   ├── README.md                  项目说明
│   ├── QUICKSTART.md              快速开始指南
│   ├── PROJECT_SUMMARY.md         项目总结
│   └── FILE_INDEX.md              本文件
│
├── 📄 批处理脚本
│   ├── install.bat                快速安装脚本
│   └── test.bat                   快速测试脚本
│
├── 📦 config/ - 配置模块
│   ├── __init__.py
│   └── settings.py                系统配置（读取.env）
│
├── 📦 core/ - 核心引擎
│   ├── __init__.py
│   └── data_manager.py            数据管理器★
│       ├─ 自动识别三市场
│       ├─ 统一数据接口
│       ├─ 智能缓存
│       └─ 实时价格
│
├── 📦 data/ - 数据获取
│   ├── __init__.py
│   ├── futu_data.py               港股数据（Futu API）
│   ├── financial_data.py          美股数据（Financial Datasets）
│   └── tushare_data.py            A股数据（Tushare）
│
├── 📦 utils/ - 工具函数
│   ├── __init__.py
│   └── cache.py                   数据缓存系统
│
├── 📁 strategies/ - 策略模块（待开发）
├── 📁 ui/ - UI界面（待开发）
│   └── widgets/ - UI组件
│
├── 📁 data_cache/ - 缓存目录（自动创建）
└── 📁 logs/ - 日志目录（自动创建）
```

---

## 🎯 关键文件说明

### 必读文件 📖

1. **README.md** - 项目概览
   - 功能特性
   - 项目结构
   - 快速开始
   - 使用示例

2. **QUICKSTART.md** - 快速开始
   - 5分钟快速开始
   - API密钥获取
   - 配置指南
   - 常见问题

3. **PROJECT_SUMMARY.md** - 项目总结
   - 已完成功能
   - 待开发功能
   - 使用指南
   - 测试状态

### 配置文件 ⚙️

1. **.env.example** - 环境变量示例
   - 复制为 .env
   - 填入API密钥
   - 包含详细注释

2. **requirements.txt** - Python依赖
   - 运行 `pip install -r requirements.txt`
   - 包含所有必需和可选依赖

### 核心模块 💻

1. **core/data_manager.py** ⭐ 最重要
   - 统一数据管理器
   - 自动识别市场
   - 智能API调用
   - 缓存管理

2. **data/*.py** - 数据源
   - futu_data.py: 港股
   - financial_data.py: 美股
   - tushare_data.py: A股

3. **utils/cache.py** - 缓存系统
   - 本地CSV存储
   - 自动合并数据
   - 元数据管理

### 测试脚本 🧪

1. **check_system.py** - 状态检查
   - 环境检查
   - 配置检查
   - 模块检查
   - 最先运行

2. **test_system.py** - 功能测试
   - 市场识别测试
   - 数据获取测试
   - 缓存系统测试

3. **main.py** - 交互界面
   - 命令行菜单
   - 功能选择
   - 环境检查

---

## 🚀 使用流程

### 首次使用

```bash
# 1. 安装（Windows）
install.bat

# 或手动安装
pip install -r requirements.txt
copy .env.example .env
# 编辑.env文件

# 2. 检查环境
python check_system.py

# 3. 测试功能
python test_system.py

# 4. 使用程序
python main.py
```

### 日常使用

```bash
# 快速测试
test.bat

# 或使用主程序
python main.py
```

---

## 📝 配置优先级

### 最小配置（仅美股）
```
.env:
FINANCIAL_DATASETS_API_KEY=xxx
```

### 推荐配置（美股+港股）
```
.env:
FINANCIAL_DATASETS_API_KEY=xxx
FUTU_HOST=127.0.0.1
FUTU_PORT=11111
```

### 完整配置（三市场）
```
.env:
FINANCIAL_DATASETS_API_KEY=xxx
FUTU_HOST=127.0.0.1
FUTU_PORT=11111
TUSHARE_TOKEN=xxx
```

### 高级配置（+AI）
```
.env:
# ... 上面的配置 ...
DEEPSEEK_API_KEY=xxx
# 或其他AI模型
```

---

## 🔍 文件查找指南

### 想要... → 查看...

| 需求 | 文件 |
|------|------|
| 了解项目 | README.md |
| 快速开始 | QUICKSTART.md |
| 检查状态 | check_system.py |
| 测试功能 | test_system.py |
| 使用程序 | main.py |
| 查看总结 | PROJECT_SUMMARY.md |
| 配置API | .env.example |
| 安装依赖 | requirements.txt |
| 数据管理 | core/data_manager.py |
| 美股数据 | data/financial_data.py |
| 港股数据 | data/futu_data.py |
| A股数据 | data/tushare_data.py |
| 缓存系统 | utils/cache.py |
| 系统配置 | config/settings.py |

---

## ⚡ 快捷命令

```bash
# 检查系统
python check_system.py

# 测试功能
python test_system.py

# 主程序
python main.py

# 查看缓存
python -c "from utils.cache import DataCache; import json; print(json.dumps(DataCache().get_cache_info(), indent=2))"

# 测试单个市场
python -c "from core.data_manager import DataManager; m=DataManager(); print(m.get_kline_data('TSLA','2025-01-20','2025-01-22'))"
```

---

## 📞 获取帮助

1. 查看文档
   - README.md - 项目概览
   - QUICKSTART.md - 快速开始
   - PROJECT_SUMMARY.md - 详细总结

2. 运行检查
   - `python check_system.py` - 诊断问题

3. 查看示例
   - 每个.py文件的`if __name__ == '__main__'`部分

4. 参考现有代码
   - `F:\PyProjects\futu_backtest_trader\futu_backtest_trader\`

---

**最后更新**: 2025-01-22
**项目状态**: v0.1.0 (Alpha) - 核心功能可用
