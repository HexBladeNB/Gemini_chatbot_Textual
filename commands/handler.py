"""
快捷指令处理器
"""
from utils.ui import console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box
import sys
from utils.storage import save_conversation, clear_last_session

# 指令注册表
COMMANDS = {
    "/help": "📖 显示帮助",
    "/model": "🔧 选择 AI 模型",
    "--- 工具指令 ---": "",
    "/check": "🏥 全能模型体检",
    "/weather": "🌤️ 刷新天气",
    "/refresh": "🔄 彻底清屏并重绘 UI",
    "/save": "💾 保存对话",
    "/speed": "⚡ 调整打字机速度",
    "/exit": "👋 退出程序"
}

class CommandHandler:
    """指令处理器"""
    
    def __init__(self, chat_session, model_selector, banner_func, deepseek_switcher=None, weather_refresher=None):
        self.chat = chat_session
        self.model_selector = model_selector
        self.show_banner = banner_func
        self.switch_to_deepseek = deepseek_switcher
        self.weather_refresher = weather_refresher
    
    def is_command(self, text):
        """判断是否为指令"""
        return text.strip().startswith('/')
    
    def is_exit(self, text):
        """判断是否为退出指令"""
        return text.strip().lower() in ['quit', 'exit', 'q', '/exit']
    
    def handle(self, command):
        """处理指令"""
        cmd_str = command.strip().lower()
        parts = cmd_str.split()
        base_cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if base_cmd == '/help':
            self._show_help()
            return True
        
        elif base_cmd == '/speed':
            if args:
                level = args[0]
                if self.chat.set_speed(level):
                     console.print(f"[green]⚡ 打字机速度已设置为: {level.upper()}[/]")
                else:
                     console.print("[red]❌ 无效速度。可选: fast, normal, slow[/]")
            else:
                # 交互式选择菜单
                console.print("[bold yellow]选择打字机速度:[/]")
                console.print("1. [bold cyan]Fast[/]   (极速)")
                console.print("2. [bold green]Normal[/] (默认)")
                console.print("3. [bold white]Slow[/]   (沉浸)")
                choice = Prompt.ask("请输入选项", choices=["1", "2", "3", "fast", "normal", "slow"], default="2")
                
                mapping = {"1": "fast", "2": "normal", "3": "slow"}
                level = mapping.get(choice, choice)
                self.chat.set_speed(level)
                console.print(f"[green]⚡ 打字机速度已设置为: {level.upper()}[/]")
            return True

        elif base_cmd == '/refresh':
            import os
            # 清屏 (兼容 Windows 和 Unix)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # 显示简洁提示 (dashboard 信息已在底部状态栏)
            console.print("[green]✅ 屏幕已刷新[/]")
            console.print("[dim]ℹ️ 天气/新闻/运势信息请查看底部状态栏[/]")
            
            return True
        
        elif base_cmd == '/save':
            save_conversation(self.chat.get_history())
            return True
        
        elif base_cmd == '/model':
            new_model = self.model_selector()
            self.chat.set_model(new_model)
            self.show_banner()
            return True

        elif base_cmd == '/check':
            import subprocess
            try:
                console.print("[dim]🚀 正在启动全能体检中心...[/]")
                subprocess.run([sys.executable, "check_models.py"])
                console.print("[dim]✅ 体检完成[/]\n")
                Prompt.ask("按回车键继续...")
            except Exception as e:
                console.print(f"[red]❌ 启动失败: {e}[/]")
            return True

        elif base_cmd == '/weather':
            if self.weather_refresher:
                console.print("[dim]🌤️ 正在刷新天气...[/]")
                self.weather_refresher()
            else:
                console.print("❌ 天气功能未就绪")
            return True
        
        else:
            console.print("⚠️ 未知指令，输入 /help 查看可用指令")
            return True
    
    def _show_help(self):
        """显示帮助信息"""
        table = Table(box=None, show_header=True, header_style="bold cyan")
        table.add_column("指令", style="cyan")
        table.add_column("功能", style="white")
        
        for cmd, desc in COMMANDS.items():
            if cmd.startswith("---"):
                # 分割线 / 标题行
                table.add_section()
                table.add_row(f"[bold]{cmd}[/]", "", end_section=True)
            else:
                table.add_row(cmd, desc)
        
        # 添加键盘操作说明
        table.add_section()
        table.add_row("[bold]--- 键盘操作 ---[/]", "", end_section=True)
        table.add_row("[dim]Tab[/]", "接受补全/历史建议")
        table.add_row("[dim]↑/↓[/]", "选择补全项/历史记录")
        table.add_row("[dim]Ctrl+C[/]", "取消当前输入")
        table.add_row("[dim]Ctrl+D[/]", "退出程序")
                
        console.print("[bold cyan]🛠️ 快捷指令系统[/]")
        console.print(table)

