"""
策略配置加载器
Strategy Configuration Loader

从JSON文件加载策略配置并计算交易信号
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd


class StrategyConfig:
    """策略配置类"""
    
    def __init__(self, config_file: str):
        """
        初始化策略配置
        
        Parameters:
        -----------
        config_file : str
            配置文件路径
        """
        self.config_file = config_file
        self.config = self._load_config()
        self._validate()
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {self.config_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件JSON格式错误: {e}")
    
    def _validate(self):
        """验证配置完整性"""
        required_fields = ['stock_code', 'strategy', 'parameters']
        
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"配置缺少必需字段: {field}")
        
        if not self.config['stock_code']:
            raise ValueError("stock_code不能为空")
        
        if not self.config['strategy']:
            raise ValueError("strategy不能为空")
        
        if not isinstance(self.config['parameters'], dict):
            raise ValueError("parameters必须是字典类型")
    
    @property
    def name(self) -> str:
        """配置名称"""
        return self.config.get('name', f"{self.stock_code}-{self.strategy}")
    
    @property
    def description(self) -> str:
        """配置描述"""
        return self.config.get('description', '')
    
    @property
    def enabled(self) -> bool:
        """是否启用"""
        return self.config.get('enabled', True)
    
    @property
    def stock_code(self) -> str:
        """股票代码"""
        return self.config['stock_code']
    
    @property
    def strategy(self) -> str:
        """策略名称"""
        return self.config['strategy']
    
    @property
    def parameters(self) -> Dict:
        """策略参数"""
        # 过滤掉注释字段
        return {
            k: v for k, v in self.config['parameters'].items()
            if not k.startswith('_comment')
        }
    
    def __repr__(self):
        return f"StrategyConfig(name={self.name}, stock={self.stock_code}, strategy={self.strategy})"


class StrategyConfigLoader:
    """策略配置加载器"""
    
    def __init__(self, config_dir: str = 'settings'):
        """
        初始化配置加载器
        
        Parameters:
        -----------
        config_dir : str
            配置文件目录
        """
        self.config_dir = Path(config_dir)
        
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ 创建配置目录: {self.config_dir}")
        
        self.configs: Dict[str, StrategyConfig] = {}
        self.load_all()
    
    def load_all(self):
        """加载所有配置文件"""
        print(f"\n📂 加载策略配置...")
        print(f"   目录: {self.config_dir.absolute()}")
        
        # 查找所有.json文件
        config_files = list(self.config_dir.glob('*.json'))
        
        if not config_files:
            print(f"   ⚠️  未找到配置文件")
            return
        
        loaded = 0
        enabled = 0
        
        for config_file in config_files:
            try:
                # 跳过模板文件
                if 'template' in config_file.name.lower():
                    continue
                
                config = StrategyConfig(str(config_file))
                config_id = config_file.stem  # 文件名（不含扩展名）
                
                self.configs[config_id] = config
                loaded += 1
                
                if config.enabled:
                    enabled += 1
                    status = "✅"
                else:
                    status = "⚪"
                
                print(f"   {status} {config.name}")
                print(f"      文件: {config_file.name}")
                print(f"      股票: {config.stock_code} | 策略: {config.strategy}")
                
            except Exception as e:
                print(f"   ❌ 加载失败: {config_file.name}")
                print(f"      错误: {e}")
        
        print(f"\n   总计: {loaded} 个配置 ({enabled} 个已启用)\n")
    
    def get(self, config_id: str) -> Optional[StrategyConfig]:
        """
        获取指定配置
        
        Parameters:
        -----------
        config_id : str
            配置ID（文件名不含扩展名）
        
        Returns:
        --------
        StrategyConfig or None
        """
        return self.configs.get(config_id)
    
    def get_by_stock(self, stock_code: str) -> List[StrategyConfig]:
        """
        获取指定股票的所有配置
        
        Parameters:
        -----------
        stock_code : str
            股票代码
        
        Returns:
        --------
        list : 配置列表
        """
        return [
            config for config in self.configs.values()
            if config.stock_code == stock_code
        ]
    
    def get_enabled(self) -> List[StrategyConfig]:
        """获取所有启用的配置"""
        return [
            config for config in self.configs.values()
            if config.enabled
        ]
    
    def list_all(self):
        """列出所有配置"""
        print("\n" + "="*70)
        print("策略配置列表".center(70))
        print("="*70 + "\n")
        
        if not self.configs:
            print("  ⚠️  无配置文件\n")
            return
        
        for config_id, config in self.configs.items():
            status = "✅ 已启用" if config.enabled else "⚪ 已禁用"
            print(f"{status} {config.name}")
            print(f"   ID: {config_id}")
            print(f"   股票: {config.stock_code}")
            print(f"   策略: {config.strategy}")
            print(f"   描述: {config.description}")
            print(f"   参数: {len(config.parameters)} 个")
            print()
    
    def reload(self, config_id: str = None):
        """
        重新加载配置
        
        Parameters:
        -----------
        config_id : str, optional
            配置ID，如果为None则重新加载所有
        """
        if config_id is None:
            self.configs.clear()
            self.load_all()
        else:
            config_file = self.config_dir / f"{config_id}.json"
            if config_file.exists():
                config = StrategyConfig(str(config_file))
                self.configs[config_id] = config
                print(f"✅ 重新加载: {config_id}")
            else:
                print(f"❌ 配置文件不存在: {config_id}")


# 全局配置加载器实例
config_loader = StrategyConfigLoader()


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*70)
    print("策略配置加载器测试")
    print("="*70)
    
    # 加载所有配置
    loader = StrategyConfigLoader('settings')
    
    # 列出所有配置
    loader.list_all()
    
    # 获取TSLA配置
    print("\n" + "="*70)
    print("获取TSLA配置")
    print("="*70)
    
    tsla_config = loader.get('TSLA_strategy')
    if tsla_config:
        print(f"\n配置名称: {tsla_config.name}")
        print(f"股票代码: {tsla_config.stock_code}")
        print(f"策略名称: {tsla_config.strategy}")
        print(f"策略参数:")
        for key, value in tsla_config.parameters.items():
            print(f"  {key}: {value}")
    
    # 获取启用的配置
    print("\n" + "="*70)
    print("获取启用的配置")
    print("="*70)
    
    enabled = loader.get_enabled()
    print(f"\n已启用: {len(enabled)} 个配置")
    for config in enabled:
        print(f"  - {config.name} ({config.stock_code})")
    
    print("\n✅ 测试完成\n")
