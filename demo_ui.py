"""
UI 布局管理器演示脚本
运行此脚本查看布局效果和挂件功能
"""
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.live import Live

from ui import TerminalLayout, update_widget
from ui.widgets import update_widget_async

console = Console()


def demo_weather_fetch():
    """模拟天气数据获取 (耗时操作)"""
    time.sleep(1.5)  # 模拟网络延迟
    return "☀️ 25°C 晴天"


def demo_news_fetch():
    """模拟新闻获取"""
    time.sleep(2)
    return "📰 AI突破新进展..."


def main():
    console.clear()
    console.print("[bold green]🚀 UI 布局管理器演示[/]\n")
    
    # 创建布局
    layout = TerminalLayout(show_header=True, sidebar_width=28)
    
    # 初始化挂件 (同步)
    update_widget("slot1", "等待数据...", title="🌤️ 天气")
    update_widget("slot2", "等待数据...", title="📰 新闻")
    update_widget("slot3", "自定义区域", title="⚙️ 系统")
    
    console.print("[dim]演示开始: 挂件将异步刷新 (不阻塞主界面)[/]\n")
    
    # 启动异步挂件刷新 (不阻塞)
    update_widget_async("slot1", demo_weather_fetch, title="🌤️ 天气")
    update_widget_async("slot2", demo_news_fetch, title="📰 新闻")
    
    # 模拟对话
    with Live(layout.render(), console=console, refresh_per_second=4, screen=True) as live:
        # 第一轮对话
        layout.update_main(user_input="你好，介绍一下你自己")
        layout.set_status("AI 思考中...")
        live.update(layout.render())
        time.sleep(1)
        
        # 模拟流式响应
        response_parts = ["我是", "老司机", "终端", "助手，", "有什么", "可以帮你的？"]
        for part in response_parts:
            layout.update_main(response=part, append_response=True)
            live.update(layout.render())
            time.sleep(0.3)
        
        layout.set_status("就绪")
        layout.commit_turn()
        live.update(layout.render())
        time.sleep(1)
        
        # 第二轮对话
        layout.update_main(user_input="天气如何？")
        layout.set_status("AI 思考中...")
        live.update(layout.render())
        time.sleep(1)
        
        layout.update_main(response="请查看右侧天气挂件 →")
        live.update(layout.render())
        time.sleep(2)
        
        layout.commit_turn()
        layout.set_status("演示完成")
        live.update(layout.render())
        time.sleep(3)
    
    console.print("\n[bold green]✅ 演示结束[/]")
    console.print("[dim]提示: update_widget(name, data) 可随时更新任意挂件[/]")


if __name__ == "__main__":
    main()
