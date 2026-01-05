"""
消息列表组件 - 滚动对话区 + 内联输入 + Glitch 动画
"""
from textual.widgets import Static, Label, TextArea
from textual.containers import ScrollableContainer, Vertical
from textual.message import Message

from .glitch_label import GlitchAIBubble


class MessageBubble(Vertical):
    """消息气泡基类 (容器)"""
    
    def __init__(self, content: str = "", role: str = "user"):
        super().__init__()
        self.role = role
        self._content = content
        self.add_class(f"{role}-bubble-container")
    
    def compose(self):
        if self.role == "user":
            # 使用可靠的 Unicode Emoji
            yield Label("👤 OPERATOR │ ⌨️ CMD", classes="bubble-header user-header")
            # 用户消息通常是纯文本，但也开启 markup 以防万一 (虽然我们主要依赖 Markdown)
            # 注意：用户输入如果包含 [ ] 可能会被误解析，所以这里最好还是默认 safe
            # 但为了统一，我们对 Static 开启 markup=True，并在传入前对用户输入做转义是最佳实践
            # 这里简单起见，仅对系统消息开启 markup 支持比较安全
            yield Static(self._content, classes="bubble-content", id="user-content")
        else:
            # 系统消息 (支持 Rich Markup)
            yield Label("🖥️ SYSTEM │ ℹ️ INFO", classes="bubble-header system-header")
            yield Static(self._content, classes="bubble-content", markup=True)


class UserBubble(MessageBubble):
    """用户消息气泡"""
    def __init__(self, content: str):
        super().__init__(content, role="user")


class SystemBubble(MessageBubble):
    """系统消息气泡"""
    def __init__(self, content: str):
        super().__init__(content, role="system")


# AIBubble 现在使用 GlitchAIBubble (已在 glitch_label.py 中重构为容器)
AIBubble = GlitchAIBubble


class InlineInputContainer(Vertical):
    """内联输入框容器 - 带标题和边框"""
    
    def __init__(self, input_widget: "InlineInput"):
        super().__init__()
        self.input_widget = input_widget
        self.add_class("input-container")
        
    def compose(self):
        # 输入框标题
        yield Label("💬 CONSOLE │ ✏️ INPUT", classes="bubble-header input-header")
        yield self.input_widget


class ShortcutTriggered(Message):
    """快捷键触发事件 - 转发到 App 层处理"""
    def __init__(self, action: str):
        self.action = action
        super().__init__()


class InlineInput(TextArea):
    """内联输入框 - 多行支持 + 历史记录"""

    # 全局输入历史 (所有输入框共享)
    HISTORY: list[str] = []

    class Submitted(Message):
        """输入提交事件"""
        def __init__(self, value: str, input: "InlineInput"):
            self.value = value
            self.input = input
            super().__init__()

    def __init__(self):
        super().__init__(text="", language=None, theme="css")
        self.show_line_numbers = False
        self.add_class("inline-input")
        # 历史记录指针 (None 表示在最新空白处)
        self._history_index: int | None = None
        # 暂存当前正在输入的内容 (以便从历史切回来时不丢失)
        self._temp_input: str = ""

    def _emit_shortcut(self, action: str) -> None:
        """发送快捷键事件到 App 层"""
        self.post_message(ShortcutTriggered(action))
    
    @property
    def value(self) -> str:
        return self.text

    def _on_key(self, event) -> None:
        """拦截按键事件 - 处理快捷键、Enter、上、下键"""
        key = event.key if hasattr(event, 'key') else ''
        key_lower = key.lower()

        # 功能键快捷键
        if key_lower in ["f2", "f5", "f12"]:
            event.prevent_default()
            event.stop()
            if key_lower == "f2":
                self._emit_shortcut("clear_log")
            elif key_lower == "f5":
                self._emit_shortcut("reset_session")
            elif key_lower == "f12":
                self._emit_shortcut("switch_flavor")
            return

        # 检测 Ctrl+ 字母组合
        # 支持两种格式：直接 "ctrl+s" 等或单独的字符 + ctrl 属性
        is_ctrl = False
        if hasattr(event, "ctrl"):
            is_ctrl = event.ctrl
        elif hasattr(event, "modifiers"):
            # 检查 modifiers 中是否有 ctrl
            mods = event.modifiers if event.modifiers else set()
            is_ctrl = "ctrl" in {str(m).lower() for m in mods}

        # 处理 Ctrl+字母
        if is_ctrl and len(key_lower) == 1 and key_lower.isalpha():
            event.prevent_default()
            event.stop()
            if key_lower == "s":
                self._emit_shortcut("switch_speed")
            elif key_lower == "d":
                self._emit_shortcut("switch_service")
            elif key_lower == "q":
                self._emit_shortcut("quit")
            return

        # 处理 "ctrl+x" 格式的按键 (某些 Textual 版本)
        if "+" in key_lower:
            parts = key_lower.split("+")
            if len(parts) == 2 and parts[0] == "ctrl":
                letter = parts[1]
                if len(letter) == 1 and letter.isalpha():
                    event.prevent_default()
                    event.stop()
                    if letter == "s":
                        self._emit_shortcut("switch_speed")
                    elif letter == "d":
                        self._emit_shortcut("switch_service")
                    elif letter == "q":
                        self._emit_shortcut("quit")
                    return

        # Enter 键发送消息
        if key_lower == "enter":
            event.prevent_default()
            event.stop()
            self._do_submit()
            return

        # 上键：回溯历史（仅在第一行时）
        if key_lower == "up" and self.cursor_location[0] == 0:
            self._navigate_history(-1)
            event.prevent_default()
            event.stop()
            return

        # 下键：前进历史（仅在最后一行时）
        if key_lower == "down":
            last_line_idx = self.document.line_count - 1
            if self.cursor_location[0] == last_line_idx:
                self._navigate_history(1)
                event.prevent_default()
                event.stop()
                return

        # 其他按键交给父类处理
        super()._on_key(event)

    def _navigate_history(self, direction: int) -> None:
        """导航历史记录 (-1: 上一条, 1: 下一条)"""
        if not self.HISTORY:
            return

        # 如果当前在“最新”位置，先暂存当前输入
        if self._history_index is None:
            self._temp_input = self.text

        # 计算新索引
        new_index = -1
        if self._history_index is None:
            # 从最新处开始按上键 -> 列表最后一个
            if direction == -1:
                new_index = len(self.HISTORY) - 1
            else:
                return # 在最新处按下键无效
        else:
            new_index = self._history_index + direction
        
        # 边界检查
        if new_index < 0:
            new_index = 0 # 到底了
        elif new_index >= len(self.HISTORY):
            # 超过最旧的一条，回到“最新”空白/暂存状态
            self._history_index = None
            self.text = self._temp_input
            self.cursor_location = (len(self.text.splitlines()) - 1, len(self.text)) # 光标移到最后
            return

        # 应用历史记录
        self._history_index = new_index
        history_text = self.HISTORY[new_index]
        self.text = history_text
        
        # 光标移到末尾
        lines = history_text.splitlines() or [""]
        self.cursor_location = (len(lines) - 1, len(lines[-1]))

    def _do_submit(self) -> None:
        """执行提交"""
        val = self.text.strip()
        if val:
            # 记录到历史 (避免连续重复)
            if not self.HISTORY or self.HISTORY[-1] != val:
                self.HISTORY.append(val)
            
            self.post_message(self.Submitted(val, self))
            self.text = ""
            self._history_index = None # 重置指针



class MessageLog(ScrollableContainer):
    """消息列表容器 - 包含内联输入"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_input: InlineInput | None = None
    
    def add_user_message(self, content: str) -> UserBubble:
        """添加用户消息"""
        bubble = UserBubble(content)
        self.mount(bubble)
        self.scroll_end(animate=False)
        return bubble
    
    def add_ai_message_streaming(self, model_name: str = "AI") -> GlitchAIBubble:
        """创建流式 AI 消息气泡 (带 Glitch 动画)"""
        bubble = GlitchAIBubble(model_name=model_name)
        self.mount(bubble)
        self.scroll_end(animate=False)
        return bubble
    
    def add_system_message(self, content: str) -> SystemBubble:
        """添加系统消息"""
        bubble = SystemBubble(content)
        self.mount(bubble)
        self.scroll_end(animate=False)
        return bubble
    
    def create_inline_input(self) -> InlineInput:
        """创建内联输入框 (带容器)"""
        # 清除旧的输入框容器 (如果存在)
        self.query(InlineInputContainer).remove()
        
        input_widget = InlineInput()
        container = InlineInputContainer(input_widget)
        self.mount(container)
        self.scroll_end(animate=False)
        input_widget.focus()
        self._current_input = input_widget
        return input_widget
    
    def clear_messages(self) -> None:
        """清空所有消息"""
        for child in list(self.children):
            child.remove()
        self._current_input = None
