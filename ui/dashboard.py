"""
高保真动画仪表盘
- 极简数字噪音风格
- 静态布局 + 动态边框
- 消除高频闪烁
- Prompt Toolkit 集成支持
"""
import time
import sys
import os
import random
from enum import Enum, auto
from io import StringIO

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.console import Console, Group
from rich.layout import Layout
from rich import box

from utils.news import news_fetcher
from utils.fortune import fortune_teller
from utils.weather import weather_fetcher

# 主控制台
console = Console()
# 用于导出 ANSI 字符串的控制台
capture_console = Console(width=console.width if 'console' in globals() else 100, color_system="truecolor", legacy_windows=False)

LOGO_LINES = [
    r"    __  __          ____  __          __     _   ______ ",
    r"   / / / /__  _  __/ __ )/ /___ _____/ /__  / | / / __ )",
    r"  / /_/ / _ \| |/_/ __  / / __ `/ __  / _ \/  |/ / __  |",
    r" / __  /  __/>  </ /_/ / / /_/ / /_/ /  __/ /|  / /_/ / ",
    r"/_/ /_/\___/_/|_/_____/_/\__,_/\__,_/\___/_/ |_/_____/  ",
]

class DashboardState(Enum):
    STATIC = auto()

class AnimatedDashboard:
    """动画仪表盘控制器"""
    
    def __init__(self):
        self.frame = 0
        self.model_name = "gemini-2.5-flash"
        self.state = DashboardState.STATIC
        
        # 数据缓存
        self.weather_today = ""
        self.weather_tom = ""
        self.news_list = []
        self.fortune_data = {}
        self.status_message = "" # AI 自发消息
        
        # 动画状态
        self.noise_active = True 
        
        # 视觉配置
        self.thinking_colors = ["deep_sky_blue1", "magenta", "cyan1", "purple", "bright_cyan"]
        
    def refresh_data(self):
        """刷新所有数据"""
        self.weather_today, self.weather_tom = weather_fetcher.fetch()
        self.news_list = news_fetcher.get_top_stories(limit=5)
        self.fortune_data = fortune_teller.get_daily_fortune()
        
    def set_status_message(self, msg: str):
        """设置 AI 自发消息"""
        self.status_message = msg
    
    def set_model(self, model_name: str):
        """设置当前模型"""
        self.model_name = model_name

    def next_frame(self):
        """推进动画帧"""
        self.frame += 1
    
    def get_heartbeat(self) -> str:
        """生成心跳指示器 (用于调试动画循环)"""
        if not self.noise_active:
            return ""
        # 每一帧都切换颜色，更加显眼
        chars = ["●", "○", "■", "□"]
        char = chars[self.frame % len(chars)]
        color = "bright_white on red" if self.frame % 2 == 0 else "black on bright_green"
        return f"[{color}]{char}[/]"

    def set_state(self, state: DashboardState):
        """设置仪表盘状态"""
        self.state = state


    def _get_border_style(self) -> str:
        """生成边框样式 - 稳定暗灰"""
        return "grey30"

    def _get_header_title(self, text: str) -> str:
        """生成标题"""
        return text

    # ===== Logo (静态) =====
    def render_logo(self) -> Group:
        """渲染静态 Logo"""
        # 使用统一的青色，移除脉冲动画
        lines = []
        for line in LOGO_LINES:
            lines.append(Text(line, style="bold cyan", justify="left"))
        return Group(*lines)
    
    # ===== 副标题行 =====
    def render_subtitle(self) -> Table:
        """渲染副标题"""
        subtitle = Table.grid(expand=True)
        subtitle.add_column(justify="left", ratio=1)
        
        status_text = f"Gemini Pro · Flash · DeepSeek"
        
        # 静态/闲置模式
        status_line = f"[dim]{status_text}[/]"
        if self.status_message:
            status_line = f"[bold white on blue] 💬 {self.status_message} [/]"
        model_display = f"[bold cyan]📡 {self.model_name}[/]"

        subtitle.add_row(
            f"{model_display}   {status_line}"
        )
        return subtitle
    
    # ===== 天气区域 =====
    def render_weather(self) -> Table:
        """渲染天气 (极简版)"""
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        
        # 分隔线
        grid.add_row("[dim]" + "─" * 40 + " 天气预报 " + "─" * 40 + "[/]")
        
        content = f"  {self.weather_today}\n  {self.weather_tom}"
        grid.add_row(content)
        return grid
    
    # ===== 新闻区域 =====
    def render_news(self) -> Table:
        """渲染新闻 (极简版)"""
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        
        grid.add_row("[dim]" + "─" * 40 + " 科技热榜 " + "─" * 40 + "[/]")
        
        if not self.news_list:
            grid.add_row("  [dim]正在联网检索最新动态...[/]")
        else:
            for story in self.news_list[:2]:
                title = story.get('title', '未知')
                score = story.get('score', 0)
                grid.add_row(f"  [bold bright_cyan]• {title}[/] [yellow]({score})[/]")
        
        return grid
    
    # ===== 运势区域 =====
    def render_fortune(self) -> Table:
        """渲染今日运势 (极简版)"""
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        
        grid.add_row("[dim]" + "─" * 40 + " 今日运程 " + "─" * 40 + "[/]")
        
        if not self.fortune_data:
            grid.add_row("  [dim]正在观测星象方位...[/]")
        else:
            f = self.fortune_data
            star_count = f.get('stars', '⭐⭐⭐').count('⭐')
            stars_display = '⭐' * star_count
            geek_index = f.get('index', 80)
            
            bar = "[cyan]" + "▰" * (geek_index // 10) + "[dim]" + "▱" * (10 - geek_index // 10) + "[/]"
            
            grid.add_row(f"  [bold magenta]{f['sign']}运势:[/] [bold yellow]{stars_display}[/]")
            grid.add_row(f"  [bold green]宜:[/] {f['good']}   [bold red]忌:[/] {f['bad']}")
            grid.add_row(f"  [bold blue]幸运色:[/] {f['color']}   [bold cyan]极客指数:[/] {bar} {geek_index}%")
            
        return grid
    
    # ===== 完整仪表盘 (含 Logo) =====
    def render(self) -> Table:
        """渲染完整仪表盘 (Logo + 内容)"""
        dashboard = Table.grid(expand=True, padding=(0, 0))
        dashboard.add_column(ratio=1)
        
        # Logo & 副标题
        dashboard.add_row(self.render_logo())
        dashboard.add_row(self.render_subtitle())
        dashboard.add_row("") # Spacer
        
        # 信息面板
        dashboard.add_row(self.render_weather())
        dashboard.add_row(self.render_news())
        dashboard.add_row(self.render_fortune())
        
        return dashboard

    def render_dynamic_content(self) -> Table:
        """渲染动态内容 (极简无框版)"""
        grid = Table.grid(expand=True, padding=(0, 0))
        grid.add_column(ratio=1)
        
        # 1. 副标题
        grid.add_row(self.render_subtitle())
        grid.add_row("") # Spacer
        
        # 2. 信息区块
        grid.add_row(self.render_weather())
        grid.add_row(self.render_news())
        grid.add_row(self.render_fortune())
        
        return grid


    def get_ansi_string(self) -> str:
        """获取当前帧的 ANSI 字符串 (供 prompt_toolkit 使用)"""
        with capture_console.capture() as capture:
            capture_console.print(self.render_dynamic_content())
        return capture.get()


# 全局实例
_dashboard = None

def get_dashboard() -> AnimatedDashboard:
    """获取仪表盘实例"""
    global _dashboard
    if _dashboard is None:
        _dashboard = AnimatedDashboard()
    if not _dashboard.weather_today: # 首次加载数据
        _dashboard.refresh_data()
    return _dashboard

def display_home(model_name: str = "gemini-2.5-flash", animate_duration: float = 2.0):
    """(已弃用) 旧的显示主页仪表盘方法，现通过 Prompt 动态渲染"""
    pass

def render_static_dashboard(model_name: str = "gemini-2.5-flash") -> Group:
    """返回静态仪表盘 (供旧接口兼容)"""
    dashboard = get_dashboard()
    dashboard.set_model(model_name)
    dashboard.noise_active = False # 强制关闭噪音
    return dashboard.render()
