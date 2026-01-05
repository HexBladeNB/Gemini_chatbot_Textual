"""
Gemini 异步 API 服务层
封装 ClientPool，提供同步/异步流式接口
"""
from core.client import get_client, rotate_api_key
from config.settings import SYSTEM_INSTRUCTION
from utils.logger import get_logger

logger = get_logger("gemini_service")


class GeminiService:
    """Gemini API 服务 - 封装流式调用 + 速率监控"""

    def __init__(self):
        self._client = None
        self._history = []
    
    @property
    def client(self):
        """懒加载客户端"""
        if self._client is None:
            self._client = get_client()
        return self._client

    def get_history(self):
        """获取当前历史"""
        # 转换为 (role, text) 元组列表供 MessageLog 恢复 (如果需要)
        return [(msg["role"], msg["content"]) for msg in self._history]
    
    def stream_chat_sync(self, message: str, model_name: str):
        """
        同步流式聊天 (供 Worker 线程调用)
        """
        from google.genai import types

        logger.info(f"发起请求: model={model_name}, message_len={len(message)}")
        
        # 1. 准备历史消息对象
        contents = []
        for msg in self._history:
            contents.append(types.Content(
                role=msg["role"],
                parts=[types.Part(text=msg["content"])]
            ))
        
        # 2. 添加当前用户消息
        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=message)]
        ))
        
        # 3. 流式生成与重试逻辑
        api_keys = self.client.api_keys if hasattr(self.client, "api_keys") else [1]
        max_retries = len(api_keys) # 确保能遍历完所有 Key
        full_response = ""
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content_stream(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.7,
                    )
                )
                
                full_response = ""
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        yield chunk.text
                
                # Generation Success
                break
                
            except Exception as e:
                error_msg = str(e).upper()
                logger.warning(f"请求失败 (attempt {attempt + 1}/{max_retries}): {error_msg}")
                # 捕获 429 限流、网络超时、连接错误等所有可恢复异常
                is_recoverable = any(x in error_msg for x in [
                    "429", "RESOURCE_EXHAUSTED", "TIMEOUT", "CONNECTION",
                    "NETWORK", "UNAVAILABLE", "503", "REMOTE_HOST"
                ])

                if is_recoverable and attempt < max_retries - 1:
                    if rotate_api_key():
                        logger.info(f"切换 API Key 并重试...")
                        # yield 特殊信号通知 UI 显示重连动画
                        yield f"__RECONNECTING__:{attempt + 1}:{max_retries}"
                        continue  # 切换 Key 并立即重试
                logger.error(f"API 请求最终失败: {error_msg}")
                raise e # 彻底失败或不可恢复错误时抛出
        
        # 4. 更新历史
        self._history.append({"role": "user", "content": message})
        self._history.append({"role": "model", "content": full_response})
        
        # 限制历史长度 (保留最近 20 轮 = 40 条)
        if len(self._history) > 40:
            self._history = self._history[-40:]
        
        # 5. 估算 Token 消耗并通知 UI
        # 简易估算: 中英文混合约 0.7 token/char
        prompt_tokens = max(1, int(len(message) * 0.7))
        output_tokens = max(1, int(len(full_response) * 0.7))
        turn_tokens = prompt_tokens + output_tokens

        logger.info(f"响应完成: input_tokens={prompt_tokens}, output_tokens={output_tokens}")

        # yield Token 统计信号 (UI 会捕获并更新)
        yield f"__TOKEN_STATS__:{turn_tokens}"

    def clear_history(self):
        """清空对话历史"""
        logger.info("清空对话历史")
        self._history = []

    def undo_last_turn(self) -> bool:
        """撤销上一轮对话 (删除最后的一组 User+Model 消息)"""
        if len(self._history) >= 2:
            # 弹出最后两条 (User + Model)
            self._history.pop()
            self._history.pop()
            return True
        return False

