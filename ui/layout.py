"""
终端 UI 布局管理器 - 主区域 + 挂件侧栏
"""
from typing import List, Dict, Any
from collections import deque
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich import box

from .widgets import get_widget_manager, update_widget

# 控制台实例
console = Console()


class ConversationBuffer:
    """对话缓冲区 - 管理可见对话历史"""
    
    def __init__(self, max_visible: int = 3):
        """
        Args:
            max_visible: 保留可见的最近对话轮数
        """
        self.max_visible = max_visible
        self._buffer: deque = deque(maxlen=max_visible * 2)  # user + model 成对
    
    def add_user(self, content: str):
        """添加用户消息"""
        self._buffer.append(("user", content))
    
    def add_model(self, content: str):
        """添加模型响应"""
        self._buffer.append(("model", content))
    
    def get_visible(self) -> List[tuple]:
        """获取当前可见的对话"""
        return list(self._buffer)
    
    def clear(self):
        """清空缓冲区"""
        self._buffer.clear()


class TerminalLayout:
    """
    终端布局管理器
    
    布局结构:
    ┌─────────────────────────────────────┐
    │              Header                 │
    ├────────────────────────┬────────────┤
    │                        │  Widget 1  │
    │       Main Area        ├────────────┤
    │   (对话视窗)            │  Widget 2  │
    │                        ├────────────┤
    │                        │  Widget 3  │
    └────────────────────────┴────────────┘
    """
    
    def __init__(self, show_header: bool = True, sidebar_width: int = 25):
        self.show_header = show_header
        self.sidebar_width = sidebar_width
        self.conversation = ConversationBuffer()
        self.widget_manager = get_widget_manager()
        self.current_input = ""
        self.current_response = ""
        self.status_text = "就绪"
        
    def _build_layout(self) -> Layout:
        """构建布局结构"""
        root = Layout()
        
        # 核心修改：将界面分为"应用区"和"底部输入区"
        # 底部留白(size=3) 留出足够空间给 Prompt，并用 Panel 包裹
        root.split_column(
            Layout(name="app_layer"),
            Layout(name="input_area", size=3) 
        )
        
        layout = root["app_layer"]
        # 初始化底部输入区样式
        root["input_area"].update(Panel(Text(">>> 在此输入...", style="dim"), title="[bold]⌨️ 输入[/]", border_style="cyan"))
        
        if self.show_header:
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="body")
            )
            body = layout["body"]
        else:
            body = layout
        
        body.split_row(
            Layout(name="main", ratio=3),
            Layout(name="sidebar", size=self.sidebar_width)
        )
        
        # 侧边栏分割为三个挂件区
        body["sidebar"].split_column(
            Layout(name="widget1"),
            Layout(name="widget2"),
            Layout(name="widget3")
        )
        
        return root
    
    def _render_header(self) -> Panel:
        """渲染顶栏"""
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M:%S")
        header_text = Text()
        header_text.append("🚀 老司机终端 ", style="bold")
        header_text.append(f"│ {self.status_text} ", style="dim")
        header_text.append(f"│ {time_str}", style="dim italic")
        return Panel(header_text, box=box.SIMPLE, padding=0)
    
    def _render_main(self) -> Panel:
        """渲染主对话区"""
        parts = []
        
        # 显示历史对话 (上卷区域)
        visible = self.conversation.get_visible()
        if visible:
            for role, content in visible:
                if role == "user":
                    parts.append(Text(f">>> 你: ", style="bold magenta") + Text(content[:100] + "..." if len(content) > 100 else content, style="dim"))
                else:
                    parts.append(Text(f"<<< AI: ", style="bold green") + Text(content[:150] + "..." if len(content) > 150 else content, style="dim"))
            parts.append(Text("─" * 40, style="dim"))
        
        # 当前输入
        if self.current_input:
            parts.append(Text(f"\n>>> 你: ", style="bold magenta") + Text(self.current_input))
        
        # 当前响应 (流式)
        if self.current_response:
            parts.append(Text(f"\n<<< AI: ", style="bold green") + Text(self.current_response))
        
        if not parts:
            parts.append(Text("输入消息开始对话...", style="dim italic"))
        
        return Panel(
            Group(*parts) if parts else Text(""),
            title="[bold]💬 对话[/]",
            border_style="bright_blue",
            padding=(1, 2)
        )
    
    def render(self) -> Layout:
        """渲染完整布局"""
        layout = self._build_layout()
        
        # 填充内容
        if self.show_header:
            layout["header"].update(self._render_header())
        
        layout["main"].update(self._render_main())
        
        # 渲染挂件
        widgets = self.widget_manager.render_all()
        layout["widget1"].update(widgets.get("slot1", Panel("", title="slot1")))
        layout["widget2"].update(widgets.get("slot2", Panel("", title="slot2")))
        layout["widget3"].update(widgets.get("slot3", Panel("", title="slot3")))
        
        return layout
    
    def update_main(self, user_input: str = None, response: str = None, append_response: bool = False):
        """
        更新主区域内容
        
        Args:
            user_input: 用户输入
            response: AI响应
            append_response: 是否追加响应 (用于流式输出)
        """
        if user_input is not None:
            self.current_input = user_input
        
        if response is not None:
            if append_response:
                self.current_response += response
            else:
                self.current_response = response
    
    def commit_turn(self):
        """提交当前对话轮次到历史"""
        if self.current_input:
            self.conversation.add_user(self.current_input)
        if self.current_response:
            self.conversation.add_model(self.current_response)
        self.current_input = ""
        self.current_response = ""
    
    def set_status(self, text: str):
        """设置状态栏文本"""
        self.status_text = text
    
    def clear(self):
        """清空对话"""
        self.conversation.clear()
        self.current_input = ""
        self.current_response = ""


# 便捷的全局实例
_layout_instance = None


def get_layout() -> TerminalLayout:
    """获取全局布局实例"""
    global _layout_instance
    if _layout_instance is None:
        _layout_instance = TerminalLayout()
    return _layout_instance
