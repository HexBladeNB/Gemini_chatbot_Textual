"""
开发专用启动器 - 支持热重载 (Hot Reload)
当检测到代码修改时，自动彻底重启主程序，无需手动关闭再打开。
"""
import os
import sys
import time
import subprocess
from pathlib import Path

# 监控的文件扩展名
EXTENSIONS = {'.py', '.env'}
# 忽略的目录
# 忽略的目录 (全小写比较)
IGNORE_DIRS = {'__pycache__', '.git', '.gemini', 'exports', 'data', 'venv', 'env', '.idea', '.vscode'}

def get_file_mtimes(root_dir):
    """获取所有受监控文件的修改时间"""
    mtimes = {}
    for root, dirs, files in os.walk(root_dir):
        # 过滤忽略的目录 (不区分大小写)
        dirs[:] = [d for d in dirs if d.lower() not in IGNORE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in EXTENSIONS:
                path = os.path.join(root, file)
                try:
                    mtime = os.stat(path).st_mtime
                    mtimes[path] = mtime
                except OSError:
                    continue
    return mtimes

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    target_script = os.path.join(root_dir, "main.py")
    
    print(f"🔧 热重载模式已启动 | 监控目录: {root_dir}")
    print(f"🚀 正在启动: {target_script}")
    
    process = None
    last_mtimes = get_file_mtimes(root_dir)
    
    while True:
        # 启动子进程
        if process is None:
            # 使用当前 Python 解释器启动 main.py
            # 继承 stdin/stdout 以保留交互能力
            process = subprocess.Popen([sys.executable, target_script])
        
        try:
            time.sleep(1) # 每秒检查一次
            
            # 🔍 检测子进程是否异常退出
            if process and process.poll() is not None:
                ret = process.returncode
                if ret != 0:
                    print(f"\n[⚠️ 主程序异常退出，代码: {ret}] 正在等待代码修复...")
                    process = None # 标记为 None，等待文件修改后重启
                    # 不自动重启，直到用户修改了代码，防止死循环重启
        except KeyboardInterrupt:
            # 允许 Ctrl+C 退出 dev.py 本身
            if process:
                process.terminate()
            print("\n👋 开发模式已退出")
            break
            
        # 检查文件变化
        try:
            current_mtimes = get_file_mtimes(root_dir)
            changed_files = []
            
            # 找出具体是哪个文件变了
            if current_mtimes != last_mtimes:
                # 检查新增或修改
                for path, mtime in current_mtimes.items():
                    if path not in last_mtimes or last_mtimes[path] != mtime:
                        changed_files.append(path)
                # 检查删除
                for path in last_mtimes:
                    if path not in current_mtimes:
                        changed_files.append(f"{path} (deleted)")
                        
                if changed_files:
                    print(f"\n[⚡ 触发重启的文件]: {', '.join(changed_files)}")
                    print("[正在重载...]")
                    
                    if process:
                        process.terminate()
                        process.wait()
                        process = None
                    
                    last_mtimes = current_mtimes
                    
                    # 只有在真重启时才清屏，避免报错信息被刷掉
                    # os.system('cls' if os.name == 'nt' else 'clear')
                
        except Exception as e:
            print(f"监控出错: {e}")

if __name__ == "__main__":
    main()
