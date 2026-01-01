"""
对话存储工具 - 自动存档与恢复
"""
import os
import json
from datetime import datetime
from rich.console import Console
from rich.prompt import Confirm

console = Console()

AUTO_SAVE_FILE = "last_session.json"


def get_exports_dir():
    """获取导出目录路径"""
    exports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
    os.makedirs(exports_dir, exist_ok=True)
    return exports_dir


def save_conversation(history, filename=None):
    """保存对话到JSON文件"""
    if not filename:
        filename = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(get_exports_dir(), filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    console.print(f"✅ 对话已保存至: exports/{filename}")


def auto_save(history):
    """退出时自动保存"""
    if not history:
        return
    filepath = os.path.join(get_exports_dir(), AUTO_SAVE_FILE)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    console.print("[dim]💾 对话已自动保存[/]")


def load_last_session():
    """加载上次对话"""
    filepath = os.path.join(get_exports_dir(), AUTO_SAVE_FILE)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def has_last_session():
    """检查是否有上次对话"""
    filepath = os.path.join(get_exports_dir(), AUTO_SAVE_FILE)
    return os.path.exists(filepath)


def clear_last_session():
    """清除上次对话存档"""
    filepath = os.path.join(get_exports_dir(), AUTO_SAVE_FILE)
    if os.path.exists(filepath):
        os.remove(filepath)


def estimate_tokens(history):
    """估算token数量"""
    total_chars = 0
    for msg in history:
        for part in msg.get("parts", []):
            text = part.get("text", "")
            total_chars += len(text)
    return int(total_chars * 1.5)


def check_token_limit(history, limit=900000):
    """检查是否接近token上限"""
    estimated = estimate_tokens(history)
    if estimated > limit:
        console.print(f"[bold]⚠️ 对话已使用约 {estimated:,} tokens，接近上限！建议新开对话[/]")
        return True
    return False


def load_conversation(filename):
    """从JSON文件加载对话"""
    filepath = os.path.join(get_exports_dir(), filename)
    
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
