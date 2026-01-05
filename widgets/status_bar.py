"""
多功能状态栏组件 - 异步插件系统
- 天气分两行（今天/明天）
- 新闻滚动
- 运势
- 系统监控（CPU/GPU/内存/磁盘/网络）
"""
from datetime import datetime
from textual.widgets import Static
from textual.reactive import reactive
from textual import work
from rich.text import Text
import random


class StatusBar(Static):
    """
    底部多功能状态栏 (极简版)
    - 天气分两行（今天/明天）
    - 系统监控（CPU/GPU/内存/磁盘/网络）
    """
    
    # 核心状态
    status_text: reactive[str] = reactive("就绪")
    
    # 系统监控
    cpu_percent: reactive[float] = reactive(0.0)
    cpu_freq: reactive[float] = reactive(0.0)
    cpu_name: reactive[str] = reactive("CPU")
    mem_percent: reactive[float] = reactive(0.0)
    mem_used_gb: reactive[float] = reactive(0.0)
    mem_total_gb: reactive[float] = reactive(64.0)
    gpu_percent: reactive[float] = reactive(0.0)
    gpu_temp: reactive[float] = reactive(0.0)
    gpu_name: reactive[str] = reactive("GPU")
    disk_name: reactive[str] = reactive("C:")
    disk_percent: reactive[float] = reactive(0.0)
    disk_used_gb: reactive[float] = reactive(0.0)
    disk_total_gb: reactive[float] = reactive(0.0)
    net_up: reactive[float] = reactive(0.0)
    net_down: reactive[float] = reactive(0.0)
    has_gpu: reactive[bool] = reactive(False)
    _disk_rotate_counter: int = 0
    
    # 插件数据
    weather_today: reactive[str] = reactive("🌤️ 今日天气加载中...")
    weather_tomorrow: reactive[str] = reactive("📅 明日天气加载中...")
    
    # 动态天气图标帧 (避免在 render() 中使用 time.time())
    weather_icon_frame: reactive[int] = reactive(0)
    
    # Token 统计 (仅用于动画触发，不显示)
    turn_tokens: reactive[int] = reactive(0)
    total_tokens: reactive[int] = reactive(0)
    _turn_target: int = 0
    _total_target: int = 0
    _animating: bool = False
    
    def on_mount(self) -> None:
        """启动各模块的异步刷新"""
        # 高频刷新 (每秒)
        self.set_interval(1.0, self._refresh_system)
        
        # 天气图标动画 (每0.5秒切换一帧)
        self.set_interval(0.5, self._update_weather_icon)
        
        # Token 动画 (每50ms) - 保留逻辑以支持心跳特效
        self.set_interval(0.05, self._animate_tokens)
        
        # 启动异步数据加载 (仅天气)
        self._load_weather()
        
        # 定时刷新 (每5分钟)
        self.set_interval(300.0, self._refresh_all_plugins)
    
    def _update_weather_icon(self) -> None:
        """更新天气图标帧 (避免 render() 中产生副作用)"""
        self.weather_icon_frame = (self.weather_icon_frame + 1) % 6
    
    # ============== Token 动画 ==============
    def add_tokens(self, turn_tokens: int) -> None:
        """添加本轮 Token 消耗，触发动画"""
        self._turn_target = turn_tokens
        self._total_target += turn_tokens
        self._animating = True
        self.turn_tokens = 0
    
    def _animate_tokens(self) -> None:
        """Token 数字滚动动画"""
        if not self._animating:
            return
        
        if self.turn_tokens < self._turn_target:
            step = max(1, int(self._turn_target * random.uniform(0.05, 0.15)))
            self.turn_tokens = min(self._turn_target, self.turn_tokens + step)
        
        if self.total_tokens < self._total_target:
            step = max(1, int((self._total_target - self.total_tokens) * random.uniform(0.1, 0.2)))
            self.total_tokens = min(self._total_target, self.total_tokens + step)
        
        if self.turn_tokens >= self._turn_target and self.total_tokens >= self._total_target:
            self._animating = False
    
    # ============== 实时刷新 ==============
    def _refresh_system(self) -> None:
        """每秒刷新系统监控"""
        try:
            from utils.system_monitor import system_monitor
            
            # 每5秒轮换一次磁盘显示
            self._disk_rotate_counter += 1
            if self._disk_rotate_counter >= 5:
                self._disk_rotate_counter = 0
                system_monitor.rotate_disk()
            
            s = system_monitor.get_stats()
            self.cpu_percent = s.cpu_percent
            self.cpu_freq = s.cpu_freq_ghz
            self.cpu_name = s.cpu_name
            self.mem_percent = s.memory_percent
            self.mem_used_gb = s.memory_used_gb
            self.mem_total_gb = s.memory_total_gb
            self.gpu_percent = s.gpu_percent
            self.gpu_temp = s.gpu_temp
            self.gpu_name = s.gpu_name
            self.disk_name = s.disk_name
            self.disk_percent = s.disk_percent
            self.disk_used_gb = s.disk_used_gb
            self.disk_total_gb = s.disk_total_gb
            self.net_up = s.net_sent_speed
            self.net_down = s.net_recv_speed
            self.has_gpu = system_monitor.has_gpu
        except Exception:
            pass  # 系统监控刷新失败不影响主流程
    
    # ============== 异步数据加载 ==============
    @work(thread=True, exclusive=False)
    def _load_weather(self) -> None:
        """后台加载天气"""
        try:
            from utils.weather import weather_fetcher
            today, tomorrow = weather_fetcher.fetch()
            import re
            today_clean = re.sub(r'\[/?[^\]]*\]', '', today)
            tomorrow_clean = re.sub(r'\[/?[^\]]*\]', '', tomorrow)
            self.weather_today = f"🌤️ 今日: {today_clean}"
            self.weather_tomorrow = f"📅 明日: {tomorrow_clean}"
        except Exception:
            self.weather_today = "🌤️ 今日: 天气服务异常"
            self.weather_tomorrow = "📅 明日: --"
    
    def _refresh_all_plugins(self) -> None:
        """定时刷新所有插件"""
        self._load_weather()
    
    # ============== 渲染 ==============
    def _make_bar(self, percent: float, width: int = 8) -> tuple[str, str]:
        """生成进度条和颜色 (扁平像素风)"""
        filled = int(percent / 100 * width)
        # 使用 ▰ (U+25B0) 和 ▱ (U+25B1) 替代粗大的 █
        bar = "▰" * filled + "▱" * (width - filled)
        color = "green" if percent < 60 else ("yellow" if percent < 85 else "red")
        return bar, color
    
    def render(self) -> Text:
        """渲染状态栏 (极简版)"""
        lines = []
        
        # 第1行: 今日天气 (使用预计算的图标帧，避免副作用)
        w_icons = ["☀️", "🌤️", "⛅", "🌤️", "☀️", "🌞"]
        weather_line = Text()
        weather_line.append(f"{w_icons[self.weather_icon_frame]} ", style="bright_yellow")
        weather_content = self.weather_today.replace("🌤️ ", "")
        weather_line.append(weather_content, style="bright_cyan")
        lines.append(weather_line)
        
        # 第2行: 明日天气
        lines.append(Text(self.weather_tomorrow, style="cyan"))
        
        # 第3行: 系统监控 (Emoji 版)
        line_sys = Text()
        
        # 动态心跳图标
        heartbeat = "💓" if self._animating else "🖤"
        if "思考" in self.status_text:
            heartbeat = "⚡"
        
        line_sys.append(f"{heartbeat} ", style="bold red")
        
        # CPU (💻 Laptop)
        cpu_bar, cpu_color = self._make_bar(self.cpu_percent, 5)
        line_sys.append(f"💻 {self.cpu_name} ", style="cyan")
        line_sys.append(cpu_bar, style=cpu_color)
        line_sys.append(f" {self.cpu_freq:.1f}GHz", style="dim")
        line_sys.append(" ┃ ", style="dim")
        
        # GPU (🎮 Game)
        if self.has_gpu:
            gpu_bar, gpu_color = self._make_bar(self.gpu_percent, 5)
            line_sys.append(f"🎮 {self.gpu_name} ", style="magenta")
            line_sys.append(gpu_bar, style=gpu_color)
            line_sys.append(f" {self.gpu_temp:.0f}°C", style="dim")
            line_sys.append(" ┃ ", style="dim")
        
        # 内存 (🧠 Brain)
        mem_bar, mem_color = self._make_bar(self.mem_percent, 5)
        line_sys.append("🧠 RAM ", style="dim")
        line_sys.append(mem_bar, style=mem_color)
        line_sys.append(f" {self.mem_used_gb:.0f}/{self.mem_total_gb:.0f}G", style="dim")
        line_sys.append(" ┃ ", style="dim")
        
        # 磁盘 (💾 Floppy)
        disk_bar, disk_color = self._make_bar(self.disk_percent, 4)
        line_sys.append(f"💾 {self.disk_name} ", style="yellow")
        line_sys.append(disk_bar, style=disk_color)
        line_sys.append(f" {self.disk_used_gb:.0f}/{self.disk_total_gb:.0f}G", style="dim")
        
        # 脉冲动画 (保留但不显示数字)
        if self._animating:
            line_sys.append(" ⚡", style="bold red blink")
        
        lines.append(line_sys)
        
        # 合并
        result = Text()
        for i, line in enumerate(lines):
            result.append_text(line)
            if i < len(lines) - 1:
                result.append("\n")
        
        return result
    
    # ============== 外部接口 ==============
    def set_status(self, status: str) -> None:
        self.status_text = status
    
    def set_model(self, model: str) -> None:
        pass  # 不再显示模型信息
