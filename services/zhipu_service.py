"""
智谱 API 服务层
支持联网搜索，优先使用赠送额度
"""
from core.zhipu_client import get_zhipu_client
from config.settings import SYSTEM_INSTRUCTION
from utils.logger import get_logger

logger = get_logger("zhipu_service")


class ZhipuService:
    """智谱 API 服务 - 联网搜索 + 赠送额度优先"""

    def __init__(self, enable_web_search: bool = True):
        self._client = None
        self._history = []
        self._enable_web_search = enable_web_search
        # 默认使用赠送额度最多的模型
        self._model = "glm-4.6v"  # 赠送 600万 tokens

    @property
    def client(self):
        """懒加载客户端"""
        if self._client is None:
            self._client = get_zhipu_client()
        return self._client

    @property
    def is_available(self) -> bool:
        """检查服务是否可用"""
        try:
            return self.client.is_available if hasattr(self.client, "is_available") else True
        except Exception:
            return False

    def set_model(self, model: str):
        """切换模型"""
        if hasattr(self.client, "MODELS") and model in self.client.MODELS:
            self._model = model
            model_info = self.client.MODELS[model]
            logger.info(f"智谱模型: {model_info['name']} ({model_info['desc']})")
            return True
        return False

    def get_history(self):
        """获取当前历史"""
        return [(msg["role"], msg["content"]) for msg in self._history]

    def _build_tools(self):
        """构建工具列表（联网搜索）"""
        if not self._enable_web_search:
            return None

        return [{
            "type": "web_search",
            "web_search": {
                "enable": True,
                "search_result": True
            }
        }]

    def _convert_history_to_messages(self, user_message: str):
        """转换历史消息为智谱 API 格式"""
        messages = []
        
        # 0. 注入系统提示词 (强制人格)
        if SYSTEM_INSTRUCTION:
            messages.append({
                "role": "system",
                "content": SYSTEM_INSTRUCTION
            })
            
        for msg in self._history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        messages.append({"role": "user", "content": user_message})
        return messages

    def stream_chat_sync(self, message: str, model_name: str = None):
        """同步流式聊天"""
        if not self.is_available:
            error_detail = ""
            try:
                # 尝试获取更详细的错误信息
                if hasattr(self.client, '_init_error'):
                    error_detail = f" ({self.client._init_error})"
            except:
                pass
            raise RuntimeError(f"智谱 API 不可用{error_detail}，请检查 ZHIPU_API_KEY 配置")

        model = model_name or self._model
        logger.info(f"智谱请求: model={model}, len={len(message)}, web_search={self._enable_web_search}")

        messages = self._convert_history_to_messages(message)
        tools = self._build_tools()

        full_response = ""

        try:
            # 智谱流式调用
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                stream=True,
                temperature=0.7,
            )

            for chunk in response:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content_text = delta.content
                        full_response += content_text
                        yield content_text

        except Exception as e:
            logger.error(f"智谱 API 失败: {str(e)}")
            raise RuntimeError(f"智谱 API 调用失败: {str(e)}")

        # 更新历史
        self._history.append({"role": "user", "content": message})
        self._history.append({"role": "assistant", "content": full_response})

        # 限制历史长度 (保留最近 20 轮)
        if len(self._history) > 40:
            self._history = self._history[-40:]

        # Token 估算（0.7 token/char）
        prompt_tokens = max(1, int(len(message) * 0.7))
        output_tokens = max(1, int(len(full_response) * 0.7))
        turn_tokens = prompt_tokens + output_tokens

        logger.info(f"智谱响应: in={prompt_tokens}, out={output_tokens}")
        yield f"__TOKEN_STATS__:{turn_tokens}"

    def clear_history(self):
        """清空对话历史"""
        logger.info("清空智谱对话历史")
        self._history = []

    def undo_last_turn(self) -> bool:
        """撤销上一轮对话"""
        if len(self._history) >= 2:
            self._history.pop()
            self._history.pop()
            return True
        return False
