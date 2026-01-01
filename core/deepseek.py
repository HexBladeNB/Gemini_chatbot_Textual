"""
DeepSeek 客户端
"""
import os
from openai import OpenAI
from rich.console import Console
from config.settings import SYSTEM_INSTRUCTION

console = Console()


class DeepSeekClient:
    """DeepSeek 客户端"""
    
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY 未配置")
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = "deepseek-chat"
        self.r1_model = "deepseek-reasoner"
    
    def set_model(self, model_key):
        """切换模型 (v3/r1)"""
        if model_key == "r1":
            self.model = self.r1_model
        else:
            self.model = "deepseek-chat"
    
    def chat_stream(self, messages):
        """流式对话"""
        openai_messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
        for msg in messages:
            role = msg.get("role")
            if role == "model":
                role = "assistant"
            content = ""
            for part in msg.get("parts", []):
                content += part.get("text", "")
            openai_messages.append({"role": role, "content": content})
        
        return self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            stream=True
        )
