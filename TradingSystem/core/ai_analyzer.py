"""
AI分析引擎
支持多个AI模型，自动选择和降级
"""
import os
from typing import Optional, Dict, List
import json


class AIAnalyzer:
    """AI分析管理器"""
    
    # 支持的AI模型
    SUPPORTED_MODELS = {
        'deepseek': {
            'name': 'DeepSeek',
            'api_key_env': 'DEEPSEEK_API_KEY',
            'base_url': 'https://api.deepseek.com/v1',
            'model': 'deepseek-chat',
            'cost_per_1k': 0.001,  # CNY
            'suitable_for': ['technical', 'signal_confirm']
        },
        'chatgpt': {
            'name': 'ChatGPT',
            'api_key_env': 'OPENAI_API_KEY',
            'base_url': 'https://api.openai.com/v1',
            'model': 'gpt-4-turbo-preview',
            'cost_per_1k': 0.01,  # USD
            'suitable_for': ['fundamental', 'news']
        },
        'claude': {
            'name': 'Claude',
            'api_key_env': 'CLAUDE_API_KEY',
            'base_url': 'https://api.anthropic.com/v1',
            'model': 'claude-3-sonnet-20240229',
            'cost_per_1k': 0.003,  # USD
            'suitable_for': ['fundamental', 'research']
        },
        'qwen': {
            'name': '通义千问',
            'api_key_env': 'QWEN_API_KEY',
            'base_url': 'https://dashscope.aliyuncs.com/api/v1',
            'model': 'qwen-turbo',
            'cost_per_1k': 0.002,  # CNY
            'suitable_for': ['a_stock', 'chinese']
        },
        'ernie': {
            'name': '文心一言',
            'api_key_env': 'ERNIE_API_KEY',
            'base_url': 'https://aip.baidubce.com/rpc/2.0',
            'model': 'ernie-bot-turbo',
            'cost_per_1k': 0.002,  # CNY
            'suitable_for': ['a_stock', 'financial']
        }
    }
    
    def __init__(self, primary_model='deepseek', fallback_models=None):
        """
        初始化AI分析器
        
        Parameters:
        -----------
        primary_model : str
            主要使用的模型
        fallback_models : list
            降级模型列表
        """
        self.primary_model = primary_model
        self.fallback_models = fallback_models or ['chatgpt', 'deepseek']
        
        # 检查可用的模型
        self.available_models = self._check_available_models()
        
        if not self.available_models:
            print("⚠️  警告: 没有可用的AI模型，AI分析功能将不可用")
            print("   请在.env文件中配置至少一个AI API密钥")
        else:
            print(f"✅ AI分析器已初始化")
            print(f"   主模型: {self.primary_model}")
            print(f"   可用模型: {', '.join(self.available_models)}")
    
    def _check_available_models(self) -> List[str]:
        """检查哪些模型可用（有API key）"""
        available = []
        
        for model_id, config in self.SUPPORTED_MODELS.items():
            api_key = os.environ.get(config['api_key_env'])
            if api_key:
                available.append(model_id)
        
        return available
    
    def is_available(self) -> bool:
        """检查AI功能是否可用"""
        return len(self.available_models) > 0
    
    def _call_api(self, model_id: str, messages: List[Dict], 
                  temperature: float = 0.7) -> Optional[str]:
        """
        调用AI API
        
        Parameters:
        -----------
        model_id : str
            模型ID
        messages : list
            消息列表
        temperature : float
            温度参数
        
        Returns:
        --------
        str : AI响应
        """
        if model_id not in self.available_models:
            return None
        
        config = self.SUPPORTED_MODELS[model_id]
        api_key = os.environ.get(config['api_key_env'])
        
        try:
            if model_id in ['deepseek', 'chatgpt']:
                # OpenAI兼容接口
                try:
                    import openai
                except ImportError:
                    print(f"❌ openai包未安装，请运行: pip install openai")
                    return None
                
                client = openai.OpenAI(
                    api_key=api_key,
                    base_url=config['base_url']
                )
                
                response = client.chat.completions.create(
                    model=config['model'],
                    messages=messages,
                    temperature=temperature
                )
                
                return response.choices[0].message.content
            
            elif model_id == 'claude':
                # Anthropic API
                try:
                    import anthropic
                except ImportError:
                    print(f"❌ anthropic包未安装，请运行: pip install anthropic")
                    return None
                
                client = anthropic.Anthropic(api_key=api_key)
                
                # 转换消息格式
                system_msg = next((m['content'] for m in messages if m['role'] == 'system'), None)
                user_messages = [m for m in messages if m['role'] != 'system']
                
                response = client.messages.create(
                    model=config['model'],
                    max_tokens=4096,
                    system=system_msg,
                    messages=user_messages,
                    temperature=temperature
                )
                
                return response.content[0].text
            
            elif model_id == 'qwen':
                # 通义千问API
                try:
                    import dashscope
                    from dashscope import Generation
                except ImportError:
                    print(f"❌ dashscope包未安装，请运行: pip install dashscope")
                    return None
                
                dashscope.api_key = api_key
                
                # 转换消息格式
                response = Generation.call(
                    model=config['model'],
                    messages=messages,
                    temperature=temperature,
                    result_format='message'
                )
                
                if response.status_code == 200:
                    return response.output.choices[0].message.content
                return None
            
            elif model_id == 'ernie':
                # 文心一言API
                try:
                    import requests
                except ImportError:
                    print(f"❌ requests包未安装")
                    return None
                
                # 获取access token
                token_url = f"{config['base_url']}/oauth/2.0/token"
                token_params = {
                    'grant_type': 'client_credentials',
                    'client_id': api_key,
                    'client_secret': os.environ.get('ERNIE_SECRET_KEY')
                }
                token_response = requests.get(token_url, params=token_params)
                access_token = token_response.json()['access_token']
                
                # 调用API
                chat_url = f"{config['base_url']}/chat/{config['model']}"
                chat_params = {'access_token': access_token}
                chat_data = {
                    'messages': messages,
                    'temperature': temperature
                }
                
                response = requests.post(chat_url, params=chat_params, json=chat_data)
                result = response.json()
                
                if 'result' in result:
                    return result['result']
                return None
        
        except Exception as e:
            print(f"❌ {config['name']} API调用失败: {e}")
            return None
    
    def analyze(self, task_type: str, content: str, 
                context: Optional[Dict] = None) -> Optional[str]:
        """
        执行AI分析（自动选择最合适的模型）
        
        Parameters:
        -----------
        task_type : str
            任务类型:
            - 'technical': 技术分析
            - 'fundamental': 基本面分析
            - 'news': 新闻情感分析
            - 'signal_confirm': 信号确认
            - 'a_stock': A股专项分析
        content : str
            分析内容
        context : dict
            额外上下文
        
        Returns:
        --------
        str : AI分析结果
        """
        if not self.is_available():
            print("❌ AI功能不可用")
            return None
        
        # 根据任务类型选择最合适的模型
        best_model = self._select_best_model(task_type)
        
        if not best_model:
            print("❌ 没有合适的AI模型")
            return None
        
        # 构建消息
        messages = self._build_messages(task_type, content, context)
        
        # 尝试主模型
        result = self._call_api(best_model, messages)
        
        if result:
            return result
        
        # 降级到备用模型
        for fallback in self.fallback_models:
            if fallback in self.available_models and fallback != best_model:
                print(f"⚠️  尝试降级到 {fallback}")
                result = self._call_api(fallback, messages)
                if result:
                    return result
        
        print(f"❌ 所有AI模型调用失败")
        return None
    
    def _select_best_model(self, task_type: str) -> Optional[str]:
        """根据任务类型选择最佳模型"""
        # 优先使用适合该任务的模型
        for model_id in self.available_models:
            config = self.SUPPORTED_MODELS[model_id]
            if task_type in config['suitable_for']:
                return model_id
        
        # 否则使用主模型
        if self.primary_model in self.available_models:
            return self.primary_model
        
        # 最后使用任何可用模型
        return self.available_models[0] if self.available_models else None
    
    def _build_messages(self, task_type: str, content: str,
                       context: Optional[Dict] = None) -> List[Dict]:
        """构建消息"""
        messages = []
        
        # 系统提示
        if task_type == 'technical':
            system_prompt = """你是一位专业的量化交易分析师。
请分析提供的技术指标数据，给出买卖建议。
要求：
1. 分析技术形态
2. 判断趋势方向
3. 给出操作建议
4. 评估风险等级
输出格式为JSON，包含：analysis（分析）、suggestion（建议）、risk（风险等级1-5）"""
        
        elif task_type == 'fundamental':
            system_prompt = """你是一位专业的基本面分析师。
请分析提供的公司财务数据和行业信息，给出投资建议。
要求：
1. 分析财务健康度
2. 评估估值水平
3. 对比行业地位
4. 列出正面因素（至少3条）
5. 列出负面因素（至少3条）
6. 给出综合评分（0-100）
输出格式为JSON"""
        
        elif task_type == 'news':
            system_prompt = """你是一位金融新闻分析师。
请分析提供的新闻内容，评估对股价的影响。
要求：
1. 情感分析（正面/中性/负面）
2. 影响程度（1-5）
3. 关键事件提取
4. 投资建议
输出格式为JSON"""
        
        elif task_type == 'signal_confirm':
            system_prompt = """你是一位交易信号验证专家。
请验证提供的交易信号是否合理。
要求：
1. 分析信号合理性
2. 结合基本面判断
3. 评估成功概率
4. 给出仓位建议
5. 建议止损位
输出格式为JSON"""
        
        elif task_type == 'a_stock':
            system_prompt = """你是一位A股市场专家。
请分析提供的A股数据，考虑中国市场特点。
要求：
1. 分析资金流向
2. 政策影响评估
3. 市场情绪判断
4. 操作建议
输出格式为JSON"""
        
        else:
            system_prompt = "你是一位专业的金融分析师。"
        
        messages.append({
            'role': 'system',
            'content': system_prompt
        })
        
        # 用户消息
        user_message = content
        
        # 添加上下文
        if context:
            user_message += f"\n\n上下文信息:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        return messages


# 使用示例
if __name__ == '__main__':
    # 初始化
    analyzer = AIAnalyzer(primary_model='deepseek')
    
    if analyzer.is_available():
        # 技术分析
        tech_data = """
股票: TSLA
当前价: $420.0
TSF(9): $425.0
LSMA(20): $415.0
差值: +$10.0
趋势: 上涨
"""
        
        print("\n=== 技术分析 ===")
        result = analyzer.analyze('technical', tech_data)
        if result:
            print(result)
    else:
        print("\n请配置至少一个AI API密钥以使用AI分析功能")
        print("支持的API:")
        for model_id, config in AIAnalyzer.SUPPORTED_MODELS.items():
            print(f"  - {config['name']}: 设置环境变量 {config['api_key_env']}")
