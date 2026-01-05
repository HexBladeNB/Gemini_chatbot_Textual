"""
Gemini 客户端初始化 - 支持多 Key 轮换
"""
from google import genai
from config.settings import load_api_keys, setup_proxy
from rich.console import Console
import random

console = Console(stderr=True)

class ClientPool:
    """Gemini 客户端池 - 支持 429 时自动轮换 Key"""
    
    def __init__(self):
        self.api_keys = load_api_keys()
        self.current_index = 0
        self._client = None
        
        if not self.api_keys:
            console.print("❌ 致命错误: 未找到 API 密钥!")
            console.print("[dim]请在 .env 中设置 GEMINI_API_KEY，多个密钥用逗号分隔[/]")
            exit(1)
        
        # 随机起点，避免所有用户都从第一个 Key 开始
        self.current_index = random.randint(0, len(self.api_keys) - 1)
        self._init_client()
        
        console.print(f"🔑 密钥池已加载: [bold green]{len(self.api_keys)}[/] 个 | 本次挂载: [dim]{self._mask_key()}[/]")
    
    def _mask_key(self):
        """掩码显示当前 Key"""
        key = self.api_keys[self.current_index]
        return f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
    
    def _init_client(self):
        """初始化当前 Key 的客户端"""
        self._client = genai.Client(api_key=self.api_keys[self.current_index])
    
    def rotate_key(self):
        """轮换到下一个 Key (429 时调用)"""
        if len(self.api_keys) <= 1:
            return False  # 只有一个 Key，无法轮换
        
        old_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        self._init_client()
        
        console.print(f"[yellow]🔄 切换 API Key: {old_index + 1} → {self.current_index + 1}[/] [dim]({self._mask_key()})[/]")
        return True
    
    @property
    def models(self):
        """代理访问 client.models"""
        return self._client.models
    
    def __getattr__(self, name):
        """代理其他属性到底层 client"""
        return getattr(self._client, name)


# 全局单例
_pool = None

def get_client():
    """获取客户端池单例"""
    global _pool
    setup_proxy()
    if _pool is None:
        _pool = ClientPool()
    return _pool

def rotate_api_key():
    """外部调用：轮换 API Key"""
    global _pool
    if _pool:
        return _pool.rotate_key()
    return False
