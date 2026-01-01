"""
异步挂件系统 - 支持后台刷新的 Widget 管理器
"""
import threading
from typing import Dict, Any, Callable, Optional
from rich.panel import Panel
from rich.text import Text

# 全局挂件管理器实例
_widget_manager = None


class Widget:
    """挂件基类"""
    
    def __init__(self, name: str, title: str = ""):
        self.name = name
        self.title = title or name
        self.data: Any = None
        self.is_loading = False
    
    def render(self) -> Panel:
        """渲染挂件内容"""
        if self.is_loading:
            content = Text("加载中...", style="dim italic")
        elif self.data is None:
            content = Text("暂无数据", style="dim")
        elif isinstance(self.data, str):
            content = Text(self.data)
        else:
            content = Text(str(self.data))
        
        return Panel(
            content,
            title=f"[bold]{self.title}[/]",
            border_style="dim",
            height=5,
            padding=(0, 1)
        )


class WidgetManager:
    """挂件管理器 - 管理三个独立挂件区域"""
    
    def __init__(self):
        self.widgets: Dict[str, Widget] = {
            "slot1": Widget("slot1", "📍 插槽1"),
            "slot2": Widget("slot2", "📍 插槽2"),
            "slot3": Widget("slot3", "📍 插槽3"),
        }
        self._lock = threading.Lock()
        self._async_tasks: Dict[str, threading.Thread] = {}
    
    def update(self, name: str, data: Any, title: Optional[str] = None):
        """
        同步更新挂件数据
        
        Args:
            name: 挂件名称 (slot1/slot2/slot3)
            data: 显示的数据
            title: 可选的新标题
        """
        with self._lock:
            if name in self.widgets:
                self.widgets[name].data = data
                self.widgets[name].is_loading = False
                if title:
                    self.widgets[name].title = title
    
    def update_async(self, name: str, fetch_func: Callable[[], Any], title: Optional[str] = None):
        """
        异步更新挂件 - 后台线程获取数据，不阻塞主循环
        
        Args:
            name: 挂件名称
            fetch_func: 获取数据的函数 (可能耗时，如爬虫/API调用)
            title: 可选的新标题
        """
        if name not in self.widgets:
            return
        
        # 设置加载状态
        with self._lock:
            self.widgets[name].is_loading = True
            if title:
                self.widgets[name].title = title
        
        def _fetch_task():
            try:
                result = fetch_func()
                self.update(name, result)
            except Exception as e:
                self.update(name, f"错误: {e}")
        
        # 取消已有任务
        if name in self._async_tasks and self._async_tasks[name].is_alive():
            pass  # 让旧任务自然结束
        
        # 启动新线程
        thread = threading.Thread(target=_fetch_task, daemon=True)
        self._async_tasks[name] = thread
        thread.start()
    
    def get_widget(self, name: str) -> Optional[Widget]:
        """获取挂件实例"""
        return self.widgets.get(name)
    
    def render_all(self) -> Dict[str, Panel]:
        """渲染所有挂件"""
        with self._lock:
            return {name: widget.render() for name, widget in self.widgets.items()}


def get_widget_manager() -> WidgetManager:
    """获取全局挂件管理器"""
    global _widget_manager
    if _widget_manager is None:
        _widget_manager = WidgetManager()
    return _widget_manager


def update_widget(name: str, data: Any, title: Optional[str] = None):
    """
    便捷接口 - 更新指定挂件
    
    用法示例:
        update_widget("slot1", {"temp": "25°C"}, title="🌤️ 天气")
        update_widget("slot2", "最新新闻标题...", title="📰 新闻")
    """
    get_widget_manager().update(name, data, title)


def update_widget_async(name: str, fetch_func: Callable[[], Any], title: Optional[str] = None):
    """
    便捷接口 - 异步更新挂件 (不阻塞聊天)
    
    用法示例:
        update_widget_async("slot1", lambda: requests.get(...).json(), title="🌤️ 天气")
    """
    get_widget_manager().update_async(name, fetch_func, title)
