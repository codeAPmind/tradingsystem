"""
策略配置管理器
Strategy Configuration Manager

负责加载、验证和管理策略配置文件
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class StrategyConfig:
    """策略配置类"""
    
    def __init__(self, config_file: str = None, config_dict: Dict = None):
        """
        初始化策略配置
        
        Parameters:
        -----------
        config_file : str, optional
            配置文件路径
        config_dict : dict, optional
            配置字典
        """
        if config_file:
            self.config_file = config_file
            self.config = self._load_from_file(config_file)
        elif config_dict:
            self.config_file = None
            self.config = config_dict
        else:
            raise ValueError("必须提供 config_file 或 config_dict")
        
        # 验证配置
        self._validate()
    
    def _load_from_file(self, file_path: str) -> Dict:
        """从文件加载配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件JSON格式错误: {e}")
    
    def _validate(self):
        """验证配置完整性"""
        required_fields = ['stock_code', 'strategy', 'parameters']
        
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"配置缺少必需字段: {field}")
        
        # 验证股票代码
        if not self.config['stock_code']:
            raise ValueError("股票代码不能为空")
        
        # 验证策略名称
        if not self.config['strategy']:
            raise ValueError("策略名称不能为空")
        
        # 验证参数
        if not isinstance(self.config['parameters'], dict):
            raise ValueError("parameters 必须是字典类型")
    
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
        return self.config['parameters']
    
    @property
    def schedule(self) -> Dict:
        """调度配置"""
        return self.config.get('schedule', {})
    
    @property
    def notification(self) -> Dict:
        """通知配置"""
        return self.config.get('notification', {})
    
    @property
    def risk_control(self) -> Dict:
        """风控配置"""
        return self.config.get('risk_control', {})
    
    @property
    def backtest(self) -> Dict:
        """回测配置"""
        return self.config.get('backtest', {})
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        获取策略参数
        
        Parameters:
        -----------
        key : str
            参数名
        default : Any
            默认值
        
        Returns:
        --------
        Any : 参数值
        """
        return self.parameters.get(key, default)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return self.config.copy()
    
    def __repr__(self):
        return f"StrategyConfig(name={self.name}, stock={self.stock_code}, strategy={self.strategy})"


class StrategyConfigManager:
    """策略配置管理器"""
    
    def __init__(self, config_dir: str = 'settings'):
        """
        初始化配置管理器
        
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
        self.load_all_configs()
    
    def load_all_configs(self):
        """加载所有配置文件"""
        print(f"\n📂 正在加载策略配置...")
        print(f"   配置目录: {self.config_dir.absolute()}")
        
        config_files = list(self.config_dir.glob('strategy_*.json'))
        
        if not config_files:
            print(f"   ⚠️  未找到配置文件")
            return
        
        loaded_count = 0
        enabled_count = 0
        
        for config_file in config_files:
            try:
                # 跳过模板文件
                if 'template' in config_file.name:
                    continue
                
                config = StrategyConfig(str(config_file))
                config_id = config_file.stem  # 文件名（不含扩展名）
                
                self.configs[config_id] = config
                loaded_count += 1
                
                if config.enabled:
                    enabled_count += 1
                    status = "✅ 已启用"
                else:
                    status = "⚪ 已禁用"
                
                print(f"   {status} {config.name}")
                print(f"      股票: {config.stock_code} | 策略: {config.strategy}")
                
            except Exception as e:
                print(f"   ❌ 加载失败: {config_file.name}")
                print(f"      错误: {e}")
        
        print(f"\n   总计: {loaded_count} 个配置 ({enabled_count} 个已启用)")
    
    def get_config(self, config_id: str) -> Optional[StrategyConfig]:
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
    
    def get_configs_by_stock(self, stock_code: str) -> List[StrategyConfig]:
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
    
    def get_enabled_configs(self) -> List[StrategyConfig]:
        """获取所有启用的配置"""
        return [
            config for config in self.configs.values()
            if config.enabled
        ]
    
    def list_all_configs(self):
        """列出所有配置"""
        print("\n" + "="*70)
        print("策略配置列表".center(70))
        print("="*70 + "\n")
        
        if not self.configs:
            print("  ⚠️  无配置文件")
            return
        
        for config_id, config in self.configs.items():
            status = "✅" if config.enabled else "⚪"
            print(f"{status} {config.name}")
            print(f"   ID: {config_id}")
            print(f"   股票: {config.stock_code}")
            print(f"   策略: {config.strategy}")
            print(f"   描述: {config.description}")
            
            if config.schedule.get('enabled'):
                print(f"   调度: {config.schedule.get('time')} ({config.schedule.get('timezone')})")
            
            print()
    
    def create_config(self, config_dict: Dict, config_id: str = None) -> StrategyConfig:
        """
        创建新配置
        
        Parameters:
        -----------
        config_dict : dict
            配置字典
        config_id : str, optional
            配置ID
        
        Returns:
        --------
        StrategyConfig : 配置对象
        """
        # 验证配置
        config = StrategyConfig(config_dict=config_dict)
        
        # 生成配置ID
        if config_id is None:
            config_id = f"strategy_{config.stock_code.replace('.', '_')}"
        
        # 保存到文件
        config_file = self.config_dir / f"{config_id}.json"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        # 添加到管理器
        self.configs[config_id] = config
        
        print(f"✅ 创建配置: {config_id}")
        
        return config
    
    def reload_config(self, config_id: str):
        """重新加载指定配置"""
        config_file = self.config_dir / f"{config_id}.json"
        
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_id}")
        
        config = StrategyConfig(str(config_file))
        self.configs[config_id] = config
        
        print(f"✅ 重新加载配置: {config_id}")
        
        return config
    
    def reload_all_configs(self):
        """重新加载所有配置"""
        self.configs.clear()
        self.load_all_configs()


# 全局配置管理器实例
config_manager = StrategyConfigManager()


# 使用示例
if __name__ == '__main__':
    print("\n" + "="*70)
    print("策略配置管理器测试")
    print("="*70)
    
    # 初始化管理器
    manager = StrategyConfigManager('settings')
    
    # 列出所有配置
    manager.list_all_configs()
    
    # 获取TSLA配置
    print("\n" + "="*70)
    print("测试: 获取TSLA配置")
    print("="*70)
    
    tsla_config = manager.get_config('strategy_TSLA')
    if tsla_config:
        print(f"\n配置名称: {tsla_config.name}")
        print(f"股票代码: {tsla_config.stock_code}")
        print(f"策略名称: {tsla_config.strategy}")
        print(f"策略参数:")
        for key, value in tsla_config.parameters.items():
            print(f"  {key}: {value}")
    
    # 获取启用的配置
    print("\n" + "="*70)
    print("测试: 获取启用的配置")
    print("="*70)
    
    enabled_configs = manager.get_enabled_configs()
    print(f"\n已启用的配置数量: {len(enabled_configs)}")
    for config in enabled_configs:
        print(f"  - {config.name} ({config.stock_code})")
    
    print("\n✅ 测试完成\n")
