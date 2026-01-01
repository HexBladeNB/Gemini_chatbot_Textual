"""
对话核心 - 多轮记忆会话管理 (极客版)
极客风动画 + 逐字打印 + Markdown渲染
"""
import sys
import time
import threading
from collections import deque
from google.genai import types
import math
from rich.console import Group
from rich.panel import Panel
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text
from rich import box
from config.settings import SYSTEM_INSTRUCTION, TYPEWRITER_DELAY
from utils.storage import check_token_limit
from core.client import rotate_api_key
# 引入统一 UI
from utils.ui import console, print_error

# 打字延迟 (从配置读取)
CHAR_DELAY = TYPEWRITER_DELAY


class UsageMonitor:
    """
    速率监控器 - 基于滑动窗口的 RPM/TPM 实时追踪
    使用 deque 存储过去 60 秒内的请求记录
    """
    
    # Gemini Free Tier 限制 (参考值)
    RPM_LIMIT = 15       # 每分钟最大请求数
    TPM_LIMIT = 1000000  # 每分钟最大 Token 数
    WINDOW_SECONDS = 60  # 滑动窗口大小 (秒)
    
    def __init__(self):
        # 每条记录: (timestamp, prompt_tokens, output_tokens, total_tokens)
        self._records = deque()
        self._lock = threading.Lock()
    
    def record(self, prompt_tokens: int, output_tokens: int):
        """记录一次请求的 Token 消耗"""
        total = prompt_tokens + output_tokens
        now = time.time()
        
        with self._lock:
            self._records.append((now, prompt_tokens, output_tokens, total))
            self._cleanup(now)
    
    def _cleanup(self, now: float):
        """清理超过 60 秒的旧记录"""
        cutoff = now - self.WINDOW_SECONDS
        while self._records and self._records[0][0] < cutoff:
            self._records.popleft()
    
    def get_stats(self) -> dict:
        """获取当前 60 秒窗口的统计数据"""
        now = time.time()
        
        with self._lock:
            self._cleanup(now)
            
            rpm = len(self._records)
            tpm = sum(r[3] for r in self._records)
            
            return {
                "rpm": rpm,
                "tpm": tpm,
                "rpm_limit": self.RPM_LIMIT,
                "tpm_limit": self.TPM_LIMIT,
                "rpm_ratio": rpm / self.RPM_LIMIT,
                "tpm_ratio": tpm / self.TPM_LIMIT,
            }


# 全局速率监控器单例
usage_monitor = UsageMonitor()

class AudioSpectrum:
    """声波可视化 / 音频频谱分析仪 - 单行极简版"""
    def __init__(self, backend_name="AI"):
        self.backend_name = backend_name
        self.frame = 0
        self.num_bars = 20  # 频段数量
        
        # 每个频段的当前高度 (0-8)
        self.heights = [0] * self.num_bars
        
        # 盲文密度映射 (从低到高, 0-8)
        self.density_chars = [
            "⠀",  # 0 - 空
            "⠁",  # 1
            "⠃",  # 2
            "⠇",  # 3
            "⡇",  # 4
            "⣇",  # 5
            "⣧",  # 6
            "⣷",  # 7
            "⣿",  # 8 - 满
        ]
        
    def _generate_energy(self, bar_idx: int) -> int:
        """模拟频段能量 (基于正弦波叠加 + 随机扰动)"""
        import math
        import random
        
        # 多个正弦波叠加，模拟不同频率的"音频信号"
        t = self.frame * 0.15
        
        # 低频段 (左侧) 波动慢，高频段 (右侧) 波动快
        freq_factor = 0.5 + bar_idx * 0.1
        
        wave1 = math.sin(t * freq_factor)
        wave2 = math.sin(t * freq_factor * 1.7 + bar_idx * 0.3) * 0.5
        wave3 = math.sin(t * 0.3 + bar_idx * 0.5) * 0.3
        
        combined = (wave1 + wave2 + wave3 + 1.8) / 3.6  # 归一化到 0-1
        
        # 加入随机扰动
        combined += random.uniform(-0.15, 0.15)
        combined = max(0, min(1, combined))
        
        return int(combined * 8)
    
    def _update_heights(self):
        """更新各频段高度 (上升快, 下降慢 - 模拟真实均衡器)"""
        for i in range(self.num_bars):
            target = self._generate_energy(i)
            current = self.heights[i]
            
            if target > current:
                # 上升快
                self.heights[i] = min(8, current + 2)
            else:
                # 下降慢 (重力感)
                self.heights[i] = max(0, current - 1)

    def __rich__(self) -> Text:
        self.frame += 1
        self._update_heights()
        
        # 渲染波形
        wave_chars = []
        for h in self.heights:
            char = self.density_chars[h]
            wave_chars.append(char)
        
        wave = "".join(wave_chars)
        
        # 颜色渐变 (根据整体能量)
        avg_energy = sum(self.heights) / len(self.heights)
        if avg_energy > 5:
            color = "bold bright_magenta"
        elif avg_energy > 3:
            color = "cyan"
        else:
            color = "dim cyan"
        
        return Text.assemble(
            ("  🗡️ ", "bold cyan"),
            (Text.from_markup(f"{self.backend_name} ")),
            ("Thinking ", "dim cyan"),
            (wave, color)
        )


def slow_print(text, delay=CHAR_DELAY):
    """逐字打印效果"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        # 标点稍微停顿更久
        if char in '。！？.!?\n':
            time.sleep(delay * 3)
        elif char in '，、；:,;':
            time.sleep(delay * 2)
        else:
            time.sleep(delay)


def typewriter_print(text, delay=CHAR_DELAY):
    """
    打字机效果输出
    先渲染 Rich 标记为 ANSI，再逐字符输出
    """
    if delay <= 0:
        # instant 模式，直接整块输出
        console.print(text, end="", highlight=False)
        return
    
    # 使用 Rich 渲染为带 ANSI 转义的字符串
    from io import StringIO
    from rich.console import Console
    
    # 创建临时 Console 捕获输出
    buffer = StringIO()
    temp_console = Console(file=buffer, force_terminal=True, width=console.width, legacy_windows=False)
    temp_console.print(text, end="", highlight=False)
    rendered = buffer.getvalue()
    
    # 逐字符输出（智能跳过 ANSI 转义序列）
    i = 0
    while i < len(rendered):
        # ANSI 转义序列以 ESC[ 开头
        if rendered[i] == '\x1b' and i + 1 < len(rendered) and rendered[i+1] == '[':
            # 找到序列结尾 (通常是字母)
            j = i + 2
            while j < len(rendered) and not rendered[j].isalpha():
                j += 1
            if j < len(rendered):
                j += 1  # 包含结尾字母
            # 整块输出 ANSI 序列
            sys.stdout.write(rendered[i:j])
            sys.stdout.flush()
            i = j
            continue
        
        # 普通字符
        sys.stdout.write(rendered[i])
        sys.stdout.flush()
        
        # 标点符号额外停顿
        if rendered[i] in '。！？.!?\n':
            time.sleep(delay * 2.5)
        elif rendered[i] in '，、；:,;':
            time.sleep(delay * 1.5)
        else:
            time.sleep(delay)
        
        i += 1


class ChatSession:
    """多轮对话会话类 - 支持Gemini和DeepSeek双后端"""
    
    def __init__(self, client, model_name, backend="gemini"):
        self.client = client
        self.model_name = model_name
        self.history = []
        self.backend = backend
        self.deepseek_client = None
        
        # 打字机速度 (标点延迟, 普通延迟)
        self.speed_config = (0.05, 0.015)  # 默认 normal
    
    def set_speed(self, speed_level):
        """设置打字机流式输出速度"""
        levels = {
            'fast': (0.005, 0.001),   # 极速
            'normal': (0.05, 0.015),  # 默认
            'slow': (0.1, 0.05)       # 慢速
        }
        if speed_level in levels:
            self.speed_config = levels[speed_level]
            return True
        return False
    
    def set_backend(self, backend, deepseek_client=None):
        """切换后端"""
        self.backend = backend
        if deepseek_client:
            self.deepseek_client = deepseek_client

    def bind_deepseek(self, deepseek_client):
        """绑定 DeepSeek 客户端但不立即切换"""
        self.deepseek_client = deepseek_client
    
    def send_message_stream(self, user_input, show_spinner=True):
        """发送消息并配合 EKG 动画流式输出"""
        check_token_limit(self.history)
        self.history.append({"role": "user", "parts": [{"text": user_input}]})
        
        # 定义“六脉神剑”专属配色名 (基于金庸武侠意象)
        styled_name = "[bold yellow]六脉神剑真厉害[/]"
        # 极致简约轮数: · 1
        minimal_turn = f"[dim] · {(len(self.history) + 1) // 2}[/]"
        full_response = ""
        try:
            # 1. 启动动画并等待首个 Token
            first_chunk = None
            response_stream = None
            
            # 显式控制 Live 状态 - 使用声波可视化动画
            live = Live(AudioSpectrum(styled_name), refresh_per_second=15, transient=True, console=console)
            with live:
                if self.backend == "deepseek" and self.deepseek_client:
                    response_stream = self.deepseek_client.chat_stream(self.history)
                else:
                    response_stream = self.client.models.generate_content_stream(
                        model=self.model_name, contents=self.history,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION,
                            tools=[types.Tool(google_search=types.GoogleSearch())],
                            temperature=0.7
                        )
                    )

                # 阻塞直到获取第一个 token
                iterator = iter(response_stream)
                try:
                    first_chunk = next(iterator)
                    # 关键修复: 在离开 context 之前强制停止实时渲染
                    live.stop() 
                except StopIteration:
                    return ""
            
            # --- 此时 Live 已自动退出并清理了动画区域 ---

            # 2. 打印 Header (顶格对齐，移除缩进)
            separator_width = min(60, console.width - 4)
            separator = "─" * separator_width
            # 移除缩进，与 AI 正文（顶格）对齐
            console.print(f"\n[dim cyan]{separator}[/]")
            # 图标后留 1 个空格
            console.print(f"🗡️ {styled_name}{minimal_turn}")
            
            # 设置 AI 输出颜色: Bold(1) + Bright Cyan(96)
            sys.stdout.write("\033[1;96m")
            sys.stdout.flush()

            # 3. 处理首个 chunk - 流式打字机输出
            if self.backend == "deepseek":
                text = first_chunk.choices[0].delta.content or ""
            else:
                text = first_chunk.text or ""
            
            if text:
                full_response += text
                # 逐字符打字机输出
                punct_delay, normal_delay = self.speed_config
                for char in text:
                    sys.stdout.write(char)
                    sys.stdout.flush()
                    if char in '。！？.!?\n':
                        time.sleep(punct_delay)
                    elif char in '，、；:,;':
                        time.sleep(punct_delay * 0.6)
                    else:
                        time.sleep(normal_delay)

            # 4. 后续迭代 - 流式打字机输出
            for chunk in iterator:
                if self.backend == "deepseek":
                    text = chunk.choices[0].delta.content or ""
                else:
                    text = chunk.text or ""
                
                if text:
                    full_response += text
                    for char in text:
                        sys.stdout.write(char)
                        sys.stdout.flush()
                        if char in '。！？.!?\n':
                            time.sleep(punct_delay)
                        elif char in '，、；:,;':
                            time.sleep(punct_delay * 0.6)
                        else:
                            time.sleep(normal_delay)
            
            sys.stdout.write("\033[0m")  # 重置颜色
            print()  # 换行
            
            # === 回复结束装饰 ===
            self._print_response_footer(full_response)
            
        except Exception as e:
            error_str = str(e)
            
            # 优雅处理常见错误
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                # 这是临时限流，先尝试切换 API Key
                console.print()
                console.print("[bold yellow]⏳ 请求被限流[/]")
                
                # 尝试切换到下一个 API Key
                if rotate_api_key():
                    console.print("[dim]  已切换 API Key，立即重试...[/]")
                    wait_time = 1  # 切换 Key 后只等 1 秒
                else:
                    console.print("[dim]  只有一个 Key，等待后重试...[/]")
                    wait_time = 2
                
                # 自动重试 (最多3次，递增等待)
                for retry in range(1, 4):
                    console.print(f"[dim]  等待 {wait_time} 秒后重试 ({retry}/3)...[/]")
                    time.sleep(wait_time)
                    
                    try:
                        # 重新发送请求
                        if self.backend == "deepseek" and self.deepseek_client:
                            response_stream = self.deepseek_client.chat_stream(self.history)
                        else:
                            response_stream = self.client.models.generate_content_stream(
                                model=self.model_name, contents=self.history,
                                config=types.GenerateContentConfig(
                                    system_instruction=SYSTEM_INSTRUCTION,
                                    tools=[types.Tool(google_search=types.GoogleSearch())],
                                    temperature=0.7
                                )
                            )
                        
                        # 成功获取响应，继续处理
                        console.print("[green]✓ 重试成功[/]")
                        console.print(f"\n🗡️  {styled_name}{minimal_turn}")
                        
                        for chunk in response_stream:
                            if self.backend == "deepseek":
                                text = chunk.choices[0].delta.content or ""
                            else:
                                text = chunk.text or ""
                            
                            if text:
                                full_response += text
                                for char in text:
                                    sys.stdout.write(char)
                                    sys.stdout.flush()
                                    if char in '。！？.!?\n':
                                        time.sleep(0.05)
                                    elif char in '，、；:,;':
                                        time.sleep(0.03)
                                    else:
                                        time.sleep(0.015)
                        
                        print()
                        self._print_response_footer(full_response)
                        self.history.append({"role": "model", "parts": [{"text": full_response}]})
                        return full_response
                        
                    except Exception:
                        if retry == 3:
                            console.print("[bold red]❌ 重试失败，请稍后再试或切换模型 (/flash 或 /deepseek)[/]")
                        else:
                            # 重试失败，尝试切换到下一个 Key
                            rotate_api_key()
                            wait_time = min(wait_time + 2, 8)  # 递增等待，最多8秒
                        continue
                
            elif "503" in error_str or "UNAVAILABLE" in error_str:
                console.print()
                console.print("[bold yellow]⚠️ 服务暂时不可用，请稍后重试[/]")
            elif "400" in error_str or "INVALID" in error_str:
                console.print()
                console.print("[bold red]❌ 请求无效，可能是消息格式问题[/]")
            else:
                # 其他错误：只显示简短信息
                console.print()
                console.print(f"[bold red]❌ 出错了: {type(e).__name__}[/]")
                console.print(f"[dim]{error_str[:100]}{'...' if len(error_str) > 100 else ''}[/]")
            
            if self.history and self.history[-1].get("role") == "user":
                self.history.pop()
            return ""
        
        self.history.append({"role": "model", "parts": [{"text": full_response}]})
        return full_response
    
    def _print_response_footer(self, response_text: str, prompt_tokens: int = 0, output_tokens: int = 0):
        """
        回复结束后的三段式统计面板 (HUD)
        - 第一行: 本次消耗
        - 第二行: 速率监控 (60s 滑动窗口)
        - 第三行: 上下文进度
        """
        # === 估算 Token (如果 API 没返回实际值) ===
        if prompt_tokens == 0:
            # 估算 prompt: 用户最后一条消息
            last_user_msg = ""
            for msg in reversed(self.history):
                if msg.get("role") == "user":
                    for part in msg.get("parts", []):
                        last_user_msg = part.get("text", "")
                    break
            prompt_tokens = max(1, len(last_user_msg) // 2)
        
        if output_tokens == 0:
            output_tokens = max(1, len(response_text) // 2)
        
        total_tokens = prompt_tokens + output_tokens
        
        # === 第一行: 本次消耗 + 累计总量 ===
        # 计算累计总token (注意: 此时当前回复尚未加入 history，需额外加上)
        session_total_chars = sum(
            len(part.get("text", "")) 
            for msg in self.history 
            for part in msg.get("parts", [])
        ) + len(response_text)  # 加上当前回复
        session_total_tokens = max(1, session_total_chars // 2)
        
        line1 = Text()
        line1.append("💬 ", style="")  # 移除缩进
        line1.append("本次: ", style="bold white")
        line1.append(f"{total_tokens:,} tokens", style="bold bright_cyan")
        line1.append("  │  ", style="dim")
        line1.append("累计: ", style="bold white")
        line1.append(f"{session_total_tokens:,} tokens", style="bold yellow")
        console.print(line1)
        
        # === 第二行: 上下文进度条 ===
        context_limit = 32000  # 舒适区
        usage_ratio = min(1.0, session_total_tokens / context_limit)
        percent = int(usage_ratio * 100)
        
        # 进度条颜色
        if usage_ratio < 0.5:
            bar_color = "bold green"
        elif usage_ratio < 0.8:
            bar_color = "bold yellow"
        else:
            bar_color = "bold red"
        
        # 构建进度条 (20格)
        bar_width = 20
        filled = int(usage_ratio * bar_width)
        bar = "▰" * filled + "▱" * (bar_width - filled)
        
        line3 = Text()
        line3.append("💾 ", style="")  # 移除缩进
        line3.append("上下文: ", style="bold white")
        line3.append(bar, style=bar_color)
        line3.append(f" {percent}%", style="bold white")
        console.print(line3)
        
        # === 分隔线 ===
        separator_width = min(60, console.width - 4)
        separator = "─" * separator_width
        console.print(f"[dim cyan]{separator}[/]")  # 移除缩进
        console.print()  # 空行
    
    def clear_history(self):
        """清空对话历史"""
        self.history.clear()
    
    def get_turn_count(self):
        """获取当前对话轮数"""
        return len(self.history) // 2
    
    def set_model(self, model_name):
        """切换模型"""
        self.model_name = model_name
    
    def get_history(self):
        """获取对话历史(用于导出)"""
        return self.history
    
    def set_history(self, history):
        """设置对话历史(用于恢复)"""
        self.history = history
