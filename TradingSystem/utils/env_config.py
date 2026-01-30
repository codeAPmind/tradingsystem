"""
环境变量配置加载器
Environment Configuration Loader
"""
import os
from pathlib import Path
from typing import Optional


class EnvConfig:
    """环境变量配置类"""
    
    _instance = None
    _loaded = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置"""
        if not self._loaded:
            self.load_env()
            self._loaded = True
    
    def load_env(self):
        """加载环境变量"""
        # 查找.env文件
        env_file = Path('.env')
        
        if env_file.exists():
            self._load_env_file(env_file)
            print("✅ 环境变量已从 .env 文件加载")
        else:
            print("⚠️  未找到 .env 文件，使用系统环境变量")
            print("   提示: 复制 .env.example 为 .env 并配置API密钥")
    
    def _load_env_file(self, env_file: Path):
        """从文件加载环境变量"""
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                # 解析键值对
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 设置环境变量（如果尚未设置）
                    if key and value and not os.environ.get(key):
                        os.environ[key] = value
    
    # ==========================================
    # API Keys
    # ==========================================
    
    @property
    def financial_datasets_api_key(self) -> Optional[str]:
        """Financial Datasets API密钥"""
        return self._get_env('FINANCIAL_DATASETS_API_KEY')
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """OpenAI API密钥"""
        return self._get_env('OPENAI_API_KEY')
    
    @property
    def anthropic_api_key(self) -> Optional[str]:
        """Anthropic API密钥"""
        return self._get_env('ANTHROPIC_API_KEY')
    
    @property
    def alpha_vantage_api_key(self) -> Optional[str]:
        """Alpha Vantage API密钥"""
        return self._get_env('ALPHA_VANTAGE_API_KEY')
    
    @property
    def news_api_key(self) -> Optional[str]:
        """News API密钥"""
        return self._get_env('NEWS_API_KEY')
    
    # ==========================================
    # Futu配置
    # ==========================================
    
    @property
    def futu_host(self) -> str:
        """Futu OpenD主机"""
        return self._get_env('FUTU_HOST', '127.0.0.1')
    
    @property
    def futu_port(self) -> int:
        """Futu OpenD端口"""
        return int(self._get_env('FUTU_PORT', '11111'))
    
    # ==========================================
    # 其他配置
    # ==========================================
    
    @property
    def log_level(self) -> str:
        """日志级别"""
        return self._get_env('LOG_LEVEL', 'INFO')
    
    @property
    def news_cache_duration(self) -> int:
        """新闻缓存时间（分钟）"""
        return int(self._get_env('NEWS_CACHE_DURATION', '5'))
    
    @property
    def ai_provider(self) -> str:
        """AI分析提供商"""
        return self._get_env('AI_PROVIDER', 'claude').lower()
    
    # ==========================================
    # 辅助方法
    # ==========================================
    
    def _get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取环境变量
        
        Parameters:
        -----------
        key : str
            环境变量名
        default : str, optional
            默认值
        
        Returns:
        --------
        str or None
            环境变量值
        """
        value = os.environ.get(key, default)
        
        # 检查是否为占位符
        if value and 'your_' in value and '_here' in value:
            return None
        
        return value
    
    def has_financial_datasets_api(self) -> bool:
        """是否配置了Financial Datasets API"""
        return self.financial_datasets_api_key is not None
    
    def has_openai_api(self) -> bool:
        """是否配置了OpenAI API"""
        return self.openai_api_key is not None
    
    def has_anthropic_api(self) -> bool:
        """是否配置了Anthropic API"""
        return self.anthropic_api_key is not None
    
    def has_any_news_api(self) -> bool:
        """是否配置了任意新闻API"""
        return (self.has_financial_datasets_api() or 
                self.alpha_vantage_api_key is not None or
                self.news_api_key is not None)
    
    def has_any_ai_api(self) -> bool:
        """是否配置了任意AI API"""
        return self.has_anthropic_api() or self.has_openai_api()
    
    def print_status(self):
        """打印配置状态"""
        print("\n" + "="*60)
        print("API配置状态".center(60))
        print("="*60)
        
        print(f"\n📊 新闻API:")
        print(f"  Financial Datasets: {'✅' if self.has_financial_datasets_api() else '❌'}")
        print(f"  Alpha Vantage: {'✅' if self.alpha_vantage_api_key else '❌'}")
        print(f"  News API: {'✅' if self.news_api_key else '❌'}")
        
        print(f"\n🤖 AI API:")
        print(f"  Anthropic (Claude): {'✅' if self.has_anthropic_api() else '❌'}")
        print(f"  OpenAI (ChatGPT): {'✅' if self.has_openai_api() else '❌'}")
        
        print(f"\n⚙️  其他配置:")
        print(f"  AI提供商: {self.ai_provider}")
        print(f"  新闻缓存: {self.news_cache_duration}分钟")
        print(f"  日志级别: {self.log_level}")
        
        print("\n" + "="*60 + "\n")


# 全局配置实例
config = EnvConfig()


# 使用示例
if __name__ == '__main__':
    config.print_status()
