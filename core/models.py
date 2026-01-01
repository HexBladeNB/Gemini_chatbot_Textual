"""
模型选择 - 简洁版 (不依赖theme.py)
"""
from utils.ui import console
from rich.table import Table
from rich.prompt import Prompt
from rich import box

# 模型列表
RECOMMENDED_MODELS = [
    # ID, 名称, 描述, 额度 (参考 Google AI Studio Free Tier)
    ("gemini-2.5-flash-preview-09-2025", "🚀 2.5 Flash", "神级隐藏款！完美联网", "待定"),
    ("gemini-flash-latest", "🛡️ 1.5 Flash", "最稳版本，永不掉线", "1500次/日"),
    ("gemini-3-flash-preview", "⚡ 3.0 Flash", "速度平衡 (建议离线)", "待定"),
    ("gemini-2.5-flash-lite-preview-09-2025", "🍃 2.5 Lite", "极速响应，超低延迟", "待定"),
    ("gemini-robotics-er-1.5-preview", "🤖 Robotics", "实体交互，支持联网", "待定"),
]

def select_model(client):
    """模型选择"""
    console.print("\n[bold]═══════════════════════════════════════[/]")
    console.print("[bold]         🎮 选 择 AI 引 擎         [/]")
    console.print("[bold]═══════════════════════════════════════[/]\n")
    
    # 构建表格
    table = Table(box=None, show_header=True, header_style="bold")
    
    table.add_column("序号", justify="center", width=6)
    table.add_column("引擎", width=16)
    table.add_column("特点", width=20)
    table.add_column("额度", width=16)

    for i, (model_id, name, desc, quota) in enumerate(RECOMMENDED_MODELS, 1):
        table.add_row(str(i), name, desc, quota)
    
    console.print(table)
    console.print("\n[dim]提示: 更多可用模型见项目根目录 available_models.md[/]")
    console.print("[dim]DeepSeek 用 /deepseek 切换 (纯离线推理)[/]")
    
    # 只有一个选项时直接返回
    if len(RECOMMENDED_MODELS) == 1:
        console.print(f"✅ 默认装载: {RECOMMENDED_MODELS[0][1]}\n")
        return RECOMMENDED_MODELS[0][0]

    choices = [str(i) for i in range(1, len(RECOMMENDED_MODELS) + 1)]
    choice = Prompt.ask(
        "选择引擎", 
        choices=choices, 
        default="1" # 默认选 2.5 Flash
    )
    
    selected = RECOMMENDED_MODELS[int(choice)-1]
    console.print(f"✅ 已选择: {selected[1]}\n")
    return selected[0]
