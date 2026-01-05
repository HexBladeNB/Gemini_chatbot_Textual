"""
六脉神剑 - 极客热重载启动器 (Geek Hot-Reloader)
使用 watchdog 监控文件变化，自动重启应用。
支持 Rich 美化输出，智能防抖。
"""
import sys
import time
import subprocess
import signal
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("❌ 缺少 watchdog 库。请运行: pip install watchdog")
    sys.exit(1)

# 配置
PROJECT_DIR = Path(__file__).parent.resolve()
WATCH_EXTENSIONS = {".py", ".tcss", ".css", ".json", ".env"}
IGNORE_DIRS = {".git", ".venv", "__pycache__", ".idea", ".vscode", "logs", "screenshot", "doc"}
DEBOUNCE_DELAY = 1.0  # 防抖延迟 (秒) - 稍微调大一点保证文件写入完成

console = Console()

class HotReloader(FileSystemEventHandler):
    """智能热重载处理器"""

    def __init__(self):
        self.process = None
        self.last_change_time = 0
        self.needs_restart = True  # 初始启动
        self.running = True

    def _kill_process(self):
        """优雅地杀死子进程"""
        if self.process:
            try:
                # Windows 使用 taskkill 确保杀死进程树
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                        capture_output=True,
                        check=False
                    )
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except Exception:
                pass
            self.process = None

    def restart_application(self):
        """重启应用"""
        self._kill_process()
        
        console.print(Panel(
            Text("🔄 正在加载神经连接...", style="bold yellow"),
            border_style="yellow",
            padding=(0, 2)
        ))

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"  # 确保子进程立即输出

        try:
            # 启动子进程
            kwargs = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["preexec_fn"] = os.setsid

            self.process = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=PROJECT_DIR,
                env=env,
                **kwargs
            )
        except Exception as e:
            console.print(f"[bold red]❌ 启动失败:[/bold red] {e}")

    def on_modified(self, event):
        """文件变更回调"""
        if event.is_directory:
            return

        path = Path(event.src_path)
        
        # 检查忽略目录
        if any(p in path.parts for p in IGNORE_DIRS):
            return

        # 检查扩展名
        if path.suffix not in WATCH_EXTENSIONS:
            return

        # 记录变更
        current_time = time.time()
        # 简单防抖：如果距离上次变更很近，只更新时间
        self.last_change_time = current_time
        self.needs_restart = True
        
        rel_path = path.relative_to(PROJECT_DIR)
        console.print(f"[dim]� 检测到变更: {rel_path}[/dim]")

    def on_created(self, event):
        self.on_modified(event)

    def loop(self):
        """主循环"""
        observer = Observer()
        observer.schedule(self, str(PROJECT_DIR), recursive=True)
        observer.start()

        console.print(f"[bold green]🚀 六脉神剑监视器已激活[/bold green]")
        console.print(f"[dim]📁 监控目录: {PROJECT_DIR}[/dim]")
        
        try:
            while self.running:
                current_time = time.time()
                
                # 检查是否需要重启，并且防抖时间已过
                if self.needs_restart and (current_time - self.last_change_time > DEBOUNCE_DELAY):
                    self.needs_restart = False
                    self.restart_application()
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            console.print("\n[bold red]🛑 系统下线...[/bold red]")
        finally:
            observer.stop()
            observer.join()
            self._kill_process()

def main():
    reloader = HotReloader()
    reloader.loop()

if __name__ == "__main__":
    main()
