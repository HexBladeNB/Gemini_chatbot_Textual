"""
智谱 AI 客户端初始化 - 单 Key 版本（智谱 API 稳定，不需要轮换）
"""
from pathlib import Path
from rich.console import Console
import os

console = Console(stderr=True)

# 显式加载 .env（确保在任何导入之前）
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    loaded = load_dotenv(env_path, override=True)
    if loaded:
        key_preview = os.getenv("ZHIPU_API_KEY", "")[:10] + "..."
        console.print(f"[dim]📁 已加载 .env: {key_preview}[/]")
except ImportError:
    console.print("[yellow]⚠️ 未安装 python-dotenv，使用系统环境变量[/]")


class ZhipuClient:
    """智谱客户端 - 单 Key 版本"""

    # 智谱模型列表（根据用户实际配额）
    MODELS = {
        # 赠送额度（优先使用）
        "glm-4.6v": {"name": "GLM-4.6V", "desc": "赠送 600万", "type": "free", "tokens": 6000000},
        "glm-4.6": {"name": "GLM-4.6", "desc": "赠送 700万", "type": "free", "tokens": 7000000},
        "glm-4.5-air": {"name": "GLM-4.5 Air", "desc": "赠送 962万", "type": "free", "tokens": 9621586},
        # 付费额度
        "glm-4.7": {"name": "GLM-4.7", "desc": "付费 977万", "type": "paid", "tokens": 9770866},
    }

    def __init__(self):
        self._client = None
        self._has_key = False
        self._init_error = None

        # 直接读取环境变量（避免循环导入）
        api_key = os.getenv("ZHIPU_API_KEY", "")

        if not api_key:
            console.print("[yellow]⚠️ 未配置 ZHIPU_API_KEY 环境变量[/]")
            self._init_error = "未配置 ZHIPU_API_KEY"
            return

        self._has_key = True
        self.api_key = api_key

        # 掩码显示
        masked = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***"
        console.print(f"[cyan]🔑 智谱 API Key:[/] [dim]{masked}[/]")

        # 初始化客户端
        try:
            import zhipuai
            self._client = zhipuai.ZhipuAI(api_key=self.api_key)
            console.print("[green]✅ 智谱 GLM 客户端初始化成功[/]")
        except Exception as e:
            self._init_error = str(e)
            self._has_key = False
            console.print(f"[red]❌ 智谱客户端初始化失败:[/] {e}")

    @property
    def is_available(self) -> bool:
        """检查是否可用"""
        return self._has_key and self._client is not None

    @property
    def chat(self):
        """代理访问 client.chat"""
        if self._client is None:
            raise RuntimeError("智谱客户端未初始化")
        return self._client.chat

    def __getattr__(self, name):
        """代理其他属性到底层 client"""
        if self._client is None:
            raise RuntimeError(f"智谱客户端未初始化: {self._init_error or '未知错误'}")
        return getattr(self._client, name)


# 全局单例
_zhipu_client = None


def get_zhipu_client():
    """获取智谱客户端单例"""
    global _zhipu_client
    if _zhipu_client is None:
        _zhipu_client = ZhipuClient()
    return _zhipu_client
