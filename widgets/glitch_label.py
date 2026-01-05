"""
GlitchLabel 组件 - 简化版：纯 Markdown 输出
- 直接显示全部内容
- 支持 Rich Markdown 渲染
"""
import random
from textual.widgets import Static
from textual.timer import Timer
from rich.text import Text


# ============== 配置参数 ==============
# 速度档位 (保留，用于未来扩展)
SPEED_LEVELS = {
    "slow": {"delay": 1.0},
    "normal": {"delay": 0.3},
    "fast": {"delay": 0.1},
}
CURRENT_SPEED = "normal"


def get_speed_config():
    """获取当前速度配置"""
    return SPEED_LEVELS.get(CURRENT_SPEED, SPEED_LEVELS["normal"])


def set_speed(level: str):
    """设置速度档位"""
    global CURRENT_SPEED
    if level in SPEED_LEVELS:
        CURRENT_SPEED = level
        return True
    return False


def cycle_speed() -> str:
    """循环切换速度档位，返回新档位名"""
    global CURRENT_SPEED
    levels = list(SPEED_LEVELS.keys())
    idx = levels.index(CURRENT_SPEED) if CURRENT_SPEED in levels else 0
    CURRENT_SPEED = levels[(idx + 1) % len(levels)]
    return CURRENT_SPEED


# ============== 乱码字符集 (保留，用于思考动画) ==============
GLITCH_CHARS = "█▓▒░▖▗▘▙▚▛▜▝▞▟■□▪▫"


class GlitchLabel(Static):
    """矩阵式文字解码动画组件（通用版）"""
    
    def __init__(self, text: str = "", style: str = ""):
        super().__init__()
        self._target_text = text
        self._decoded_count = 0
        self._frame = 0
        self._timer: Timer | None = None
        self._custom_style = style
    
    def on_mount(self) -> None:
        if self._target_text:
            self._start_decode()
    
    def set_text_with_glitch(self, text: str) -> None:
        """设置文本并触发解码动画"""
        self._target_text = text
        self._decoded_count = 0
        self._frame = 0
        self._start_decode()
    
    def _start_decode(self) -> None:
        """启动解码动画"""
        if self._timer is not None:
            self._timer.stop()
        
        fps = 10
        total_frames = 10
        self._chars_per_frame = max(1, len(self._target_text) / total_frames)
        
        self._timer = self.set_interval(1 / fps, self._animate_frame, name="glitch")
    
    def _animate_frame(self) -> None:
        """每帧：已解码部分 + 乱码尾部"""
        text = self._target_text
        text_len = len(text)
        
        if self._decoded_count >= text_len:
            self._finalize()
            return
        
        decoded = text[:self._decoded_count]
        remaining = text_len - self._decoded_count
        glitch_len = min(remaining, 15)
        glitch = "".join(random.choice(GLITCH_CHARS) for _ in range(glitch_len))
        
        styled = Text()
        styled.append(decoded, style=self._custom_style)
        styled.append(glitch, style="dim " + self._custom_style)
        self.update(styled)
        
        self._frame += 1
        self._decoded_count = min(int(self._frame * self._chars_per_frame), text_len)
    
    def _finalize(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self.update(Text(self._target_text, style=self._custom_style))


from textual.containers import Vertical
from textual.widgets import Label


class GlitchAIBubble(Vertical):
    """
    AI 消息气泡容器 - 简化版：纯 Markdown 输出
    
    流程：
    1. API 流式返回 -> 后台积累（显示"思考中"动画）
    2. 完成后 -> 直接显示 Markdown 渲染结果
    """
    
    def __init__(self, model_name: str = "AI"):
        super().__init__()
        self._raw_content = ""
        self._is_streaming = True
        self._timer: Timer | None = None
        self._thinking_frame = 0
        self._model_name = model_name
        
        self.add_class("ai-bubble-container")

    def compose(self):
        header_text = f"🤖 {self._model_name.upper()} │ 💬 RESPONSE"
        yield Label(header_text, classes="bubble-header ai-header")
        yield Static("", id="ai-content", classes="bubble-content")
    
    def on_mount(self) -> None:
        """启动思考动画"""
        self._start_thinking_animation()
    
    @property
    def display_widget(self) -> Static:
        return self.query_one("#ai-content", Static)

    # ============== 阶段1: 流式接收 + 思考动画 ==============
    
    def _start_thinking_animation(self) -> None:
        """显示"思考中"动画"""
        self._timer = self.set_interval(0.15, self._thinking_tick, name="thinking")
    
    def _thinking_tick(self) -> None:
        """思考动画 tick"""
        if not self._is_streaming:
            return
        
        spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        waves = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂"]
        
        frame = self._thinking_frame
        spinner = spinners[frame % len(spinners)]
        
        wave_str = ""
        for i in range(5):
            wave_str += waves[(frame + i * 2) % len(waves)]
        
        char_count = len(self._raw_content)
        est_tokens = max(1, int(char_count * 0.7)) if char_count > 0 else 0
        
        styled = Text()
        styled.append(f" {spinner} ", style="bold cyan")
        styled.append("AI 思考中", style="cyan")
        styled.append(f" {wave_str} ", style="dim cyan")
        
        if char_count > 0:
            styled.append(f"\n    📝 ", style="dim")
            styled.append(f"{char_count}", style="bold yellow")
            styled.append(" 字符", style="dim")
            styled.append(" │ ", style="dim")
            styled.append(f"≈{est_tokens}", style="bold magenta")
            styled.append(" tokens", style="dim")
        
        self.display_widget.update(styled)
        self._thinking_frame += 1
    
    def append_text(self, chunk: str) -> None:
        """接收 API 流式返回的文本块 (只积累，不显示)"""
        self._raw_content += chunk

    # ============== 阶段2: 直接显示 Markdown ==============

    def finalize_with_glitch(self) -> None:
        """API 完成，直接显示 Markdown 渲染结果"""
        self._is_streaming = False
        self._stop_timer()
        
        # 渲染并显示
        self._render_and_display()
    
    def _render_and_display(self) -> None:
        """渲染 Markdown 并直接显示"""
        try:
            from rich.markdown import Markdown
            from rich.console import Console
            from rich.text import Text as RichText
            
            # 使用合适的宽度
            console = Console(force_terminal=True, width=100, no_color=False)
            md = Markdown(self._raw_content, justify="left", code_theme="monokai")
            
            # 渲染为 Text
            rendered = RichText()
            for segment in console.render(md):
                if segment.text:
                    rendered.append(segment.text, style=segment.style)
            
            # 创建带统计头的最终文本
            char_count = len(self._raw_content)
            est_tokens = max(1, int(char_count * 0.7))
            
            final_text = Text()
            final_text.append("📊 ", style="dim")
            final_text.append(f"{char_count}", style="bold yellow")
            final_text.append(" 字符", style="dim")
            final_text.append(" │ ", style="dim")
            final_text.append(f"≈{est_tokens}", style="bold magenta")
            final_text.append(" tokens", style="dim")
            final_text.append("\n\n", style="dim")
            
            # 添加渲染后的内容
            final_text.append_text(rendered)
            
            self.display_widget.update(final_text)
            
        except Exception as e:
            # 降级：纯文本
            self.display_widget.update(Text(self._raw_content, style="cyan"))

    # ============== 辅助方法 ==============
    
    def set_reconnecting(self, attempt: int = 1, max_attempts: int = 5) -> None:
        styled = Text()
        styled.append("⚠️ API 连接中断 (CONNECTION_LOST)\n", style="bold red")
        styled.append(f"⟳ 正在尝试切换线路并重连... ({attempt}/{max_attempts})", style="yellow blink")
        self.display_widget.update(styled)
        self.add_class("reconnecting")
    
    def set_error(self, error: str) -> None:
        self._stop_timer()
        self._raw_content = f"⚠️ 错误: {error}"
        self._is_streaming = False
        self.display_widget.update(Text(self._raw_content, style="red"))
        self.add_class("error-bubble")
        self.remove_class("reconnecting")
    
    def _stop_timer(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
