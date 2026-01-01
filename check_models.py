"""
全能 AI 模型诊断工具
功能：检测所有可用模型、联网能力、响应速度及额度估算
"""
import sys
import os
import time
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from google.genai import types

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.client import get_client
from core.deepseek import DeepSeekClient

console = Console()

def estimate_quota(model_id):
    """根据模型ID估算额度"""
    if "flash" in model_id:
        return "1500次/日"
    elif "pro" in model_id:
        return "50次/日"
    elif "embedding" in model_id:
        return "共享API额度"
    else:
        return "未知/API分配"

def scan_all_models(client):
    """全能扫描：可用性 + 联网 + 额度"""
    console.print("\n[bold cyan]🔍 正在进行全网模型深度体检...[/]")
    
    try:
        # 获取所有模型
        all_models = list(client.models.list())
        # 过滤
        target_models = [m for m in all_models if "gemini" in m.name.lower() and "embedding" not in m.name.lower()]
        target_models.sort(key=lambda x: x.name, reverse=True) # 新版本通常在前面
        
        table = Table(show_header=True, header_style="bold", title="Gemini 全系模型诊断报告")
        table.add_column("模型 ID", style="cyan")
        table.add_column("基础连接", justify="center")
        table.add_column("联网搜素", justify="center")
        table.add_column("响应速度", justify="right")
        table.add_column("估算额度", style="dim")
        
        console.print(f"共发现 {len(target_models)} 个模型，开始逐一测试...\n")
        
        # 使用 rich 进度条
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("扫描中...", total=len(target_models))
            
            for model in target_models:
                # 🛡️ 强制延时 5 秒，防止触发 Google 429 风控
                time.sleep(5)
                
                model_id = model.name.split("/")[-1]
                progress.update(task, description=f"正在测试 {model_id}...")
                
                # 排除非对话模型
                if any(x in model_id for x in ["vision", "audio", "computer-use"]):
                    table.add_row(model_id, "[dim]跳过[/]", "-", "-", estimate_quota(model_id))
                    progress.advance(task)
                    continue

                # 1. 基础连接测试
                basic_status = "❌"
                start_time = time.time()
                try:
                    client.models.generate_content(model=model_id, contents="Hi", config=types.GenerateContentConfig(response_mime_type="text/plain"))
                    basic_status = "✅"
                except Exception as e:
                    if "429" in str(e): basic_status = "⚠️ 429"
                    elif "404" in str(e): basic_status = "❌ 404"
                    else: basic_status = "❌ err"
                
                conn_duration = time.time() - start_time
                
                # 2. 联网搜索测试 (只有基础连接通过且非429才测)
                search_status = "-"
                total_duration = conn_duration
                
                if basic_status == "✅":
                    try:
                        s_start = time.time()
                        # 尝试调用搜索
                        client.models.generate_content(
                            model=model_id,
                            contents="Time now?",
                            config=types.GenerateContentConfig(
                                tools=[types.Tool(google_search=types.GoogleSearch())]
                            )
                        )
                        search_status = "[green]✅ 支持[/]"
                        total_duration += (time.time() - s_start)
                    except Exception as e:
                        if "429" in str(e): search_status = "[yellow]⚠️ 429[/]" # 联网导致限流
                        elif "400" in str(e): search_status = "[red]不支持[/]"
                        else: search_status = "[red]❌ 异常[/]"

                # 格式化输出
                duration_str = f"{total_duration:.2f}s"
                
                # 颜色高亮推荐模型
                display_id = model_id
                if "gemini-2.5-flash" in model_id and "preview" in model_id and search_status == "[green]✅ 支持[/]":
                    display_id = f"[bold green]{model_id}[/]"
                    
                table.add_row(display_id, basic_status, search_status, duration_str, estimate_quota(model_id))
                progress.advance(task)

        console.clear()
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]扫描失败: {e}[/]")

def test_deepseek():
    """测试 DeepSeek"""
    console.print("\n[bold]🌙 DeepSeek 离线推理测试[/]")
    table = Table(show_header=True)
    table.add_column("模型")
    table.add_column("ID")
    table.add_column("状态")
    
    try:
        ds = DeepSeekClient()
        
        # V3
        sys.stdout.write("Testing V3...\r")
        ds.set_model("v3")
        try:
            # 简单测试，不打印内容
            list(ds.chat_stream([{"role": "user", "content": "Hi"}]))
            v3_status = "[green]✅ 可用[/]"
        except: v3_status = "[red]❌ 失败[/]"
        
        # R1
        sys.stdout.write("Testing R1...\r")
        ds.set_model("r1")
        try:
            list(ds.chat_stream([{"role": "user", "content": "Hi"}]))
            r1_status = "[green]✅ 可用[/]"
        except: r1_status = "[red]❌ 失败[/]"
        
        table.add_row("DeepSeek V3", "deepseek-chat", v3_status)
        table.add_row("DeepSeek R1", "deepseek-reasoner", r1_status)
        
    except Exception as e:
        table.add_row("DeepSeek", "Client", f"[red]配置错误: {e}[/]")
        
    console.print(table)

def main():
    console.print("\n[bold]🏥 AI 模型全能体检中心[/]\n")
    
    # 1. Gemini 体检
    try:
        client = get_client()
        scan_all_models(client)
    except Exception as e:
        console.print(f"[red]Gemini 初始化失败: {e}[/]")

    # 2. DeepSeek 体检
    test_deepseek()
    
    console.print("\n[dim]提示: 推荐使用带有 [green]✅ 支持[/] 联网且响应速度快的模型及作为主力[/]")

if __name__ == "__main__":
    main()
