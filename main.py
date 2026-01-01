"""
老司机终端 - 极客聊天机器人 (经典稳健版)
Gemini + DeepSeek 双引擎
- 支持 Prompt Toolkit 异步交互
- 动态仪表盘 Prompt 集成
"""
import os
import sys
import asyncio
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich.prompt import Prompt, Confirm
from rich import box
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
import urllib.request
import time

# prompt_toolkit 引入
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI, HTML
from prompt_toolkit.application import get_app
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style
from prompt_toolkit.document import Document

# 引入统一 UI 模块
from utils.ui import console, print_banner, print_error, print_success, print_info

from core.client import get_client
from core.models import select_model
from core.chat import ChatSession
from core.deepseek import DeepSeekClient
from commands.handler import CommandHandler
from utils.storage import auto_save, has_last_session, load_last_session, clear_last_session
from config.settings import setup_proxy
from utils.news import news_fetcher
from utils.fortune import fortune_teller
from utils.weather import weather_fetcher

# 全局变量
current_model = None
current_backend = "gemini"
is_thinking = False # 标记是否处于思考状态，用于抑制后台任务

# 使用 ui.dashboard 获取仪表盘
from ui.dashboard import get_dashboard, render_static_dashboard, DashboardState

def fetch_weather_text():
    """获取天气信息 (今日+明日) - 使用和风天气API"""
    return weather_fetcher.fetch()

def show_banner():
    """(已弃用)"""
    pass

def show_banner_static():
    """显示静态仪表盘 (用于 /home)"""
    console.print(render_static_dashboard(
        "DeepSeek" if current_backend == "deepseek" else current_model
    ))

# === 输入语法高亮 Lexer ===
class ChatInputLexer(Lexer):
    """自定义语法高亮：命令、引号、数字着色"""
    
    def lex_document(self, document: Document):
        def get_line_tokens(line_number):
            line = document.lines[line_number]
            tokens = []
            i = 0
            
            while i < len(line):
                # 命令高亮 (以 / 开头)
                if i == 0 and line.startswith('/'):
                    # 找到命令结尾 (空格或行尾)
                    end = line.find(' ', 1)
                    if end == -1:
                        end = len(line)
                    tokens.append(('class:command', line[:end]))
                    i = end
                    continue
                
                # 引号内容高亮
                if line[i] in '"\'':
                    quote_char = line[i]
                    end = line.find(quote_char, i + 1)
                    if end != -1:
                        tokens.append(('class:string', line[i:end + 1]))
                        i = end + 1
                        continue
                
                # 数字高亮
                if line[i].isdigit():
                    start = i
                    while i < len(line) and (line[i].isdigit() or line[i] == '.'):
                        i += 1
                    tokens.append(('class:number', line[start:i]))
                    continue
                
                # 普通文本
                tokens.append(('class:text', line[i]))
                i += 1
            
            return tokens
        
        return get_line_tokens

# === 输入样式定义 ===
input_style = Style.from_dict({
    'command': '#ff79c6 bold',      # 命令: 粉色加粗
    'string': '#f1fa8c',            # 引号内容: 黄色
    'number': '#bd93f9',            # 数字: 紫色
    'text': '#f1fa8c bold',         # 普通文本: 金黄色加粗
    'bottom-toolbar': '#272935', # 工具栏: 灰色背景
})

# === 底部状态栏生成器 (三行版) ===
def create_status_bar(chat_session):
    """创建三行动态状态栏闭包"""
    from datetime import datetime
    import re
    
    # 缓存数据 (避免频繁刷新)
    _cache = {
        'weather_today': '',
        'weather_tomorrow': '',
        'news': [],
        'fortune': {},
        'news_index': 0,
        'last_update': 0,
    }
    
    def _strip_rich_markup(text):
        """移除 Rich markup 标签"""
        return re.sub(r'\[/?[^\]]*\]', '', text)
    
    def _refresh_data():
        """刷新缓存数据 (每5分钟)"""
        import time
        now_ts = time.time()
        if now_ts - _cache['last_update'] > 300:  # 5分钟
            try:
                # 天气
                w_today, w_tomorrow = weather_fetcher.fetch()
                _cache['weather_today'] = _strip_rich_markup(w_today) if w_today else ""
                _cache['weather_tomorrow'] = _strip_rich_markup(w_tomorrow) if w_tomorrow else ""
                
                # 新闻 (使用 get_top_stories，优先显示中文摘要)
                news_list = news_fetcher.get_top_stories(limit=3)
                if news_list:
                    _cache['news'] = [
                        f"{n.get('summary') or n['title']} (🔥{n['score']})" 
                        for n in news_list
                    ]
                
                # 运势 (使用 get_daily_fortune)
                fortune = fortune_teller.get_daily_fortune()
                if fortune:
                    _cache['fortune'] = fortune
                    
                _cache['last_update'] = now_ts
            except Exception:
                pass
    
    def get_status_bar():
        _refresh_data()
        
        import time as _time
        _frame = int(_time.time()) % 4  # 动画帧 (0-3)
        
        # 动态图标
        clock_icons = ['🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚', '🕛']
        weather_icons = ['☀️', '🌤', '⛅', '🌥']
        calendar_icons = ['📅', '📆', '🗓️', '📋']
        
        clock_icon = clock_icons[int(_time.time()) % 12]
        weather_icon = weather_icons[_frame]
        calendar_icon = calendar_icons[_frame]
        
        now = datetime.now().strftime("%H:%M:%S")
        
        # === 第一行: 时间 + 今日天气 ===
        weather_today = _cache.get('weather_today', '')
        if weather_today:
            line1 = f'{clock_icon} {now} │ {weather_today}'
        else:
            line1 = f'{clock_icon} {now} │ {weather_icon} 天气加载中...'
        
        # === 第二行: 明日天气 (独立一行) ===
        weather_tomorrow = _cache.get('weather_tomorrow', '')
        if weather_tomorrow:
            line2 = f'{calendar_icon} {weather_tomorrow}'
        else:
            line2 = f'{calendar_icon} 明日天气加载中...'
        
        # === 第三行: 新闻滚动 (跑马灯效果) ===
        news_list = _cache.get('news', [])
        if news_list:
            import time
            # 拼接所有新闻为一个长字符串
            all_news = "  ★  ".join(news_list)
            # 添加尾部填充，形成循环
            display_width = 80  # 显示宽度
            ticker_text = all_news + "  ★  " + all_news[:display_width]
            
            # 根据时间计算滚动位置 (每0.2秒移动1字符)
            scroll_pos = int(time.time() * 5) % len(all_news)
            visible_text = ticker_text[scroll_pos:scroll_pos + display_width]
            
            line3 = f'📰 {visible_text}'
        else:
            line3 = '📰 新闻加载中...'
        
        # === 第四行: 星座 + 宜忌 ===
        fortune = _cache.get('fortune', {})
        if fortune:
            line4 = (
                f"🔮 {fortune.get('sign', '')} {fortune.get('stars', '')} │ "
                f"👍 宜: {fortune.get('good', '')} │ "
                f"👎 忌: {fortune.get('bad', '')}"
            )
            # === 第五行: 幸运色 + 极客指数 + 对话轮数 ===
            turns = chat_session.get_turn_count() if chat_session else 0
            line5 = (
                f"🍀 幸运色: {fortune.get('color', '')} │ "
                f"💻 极客指数: {fortune.get('index', '')}% │ "
                f"💬 本轮对话: {turns} 轮 │ "
                f"⌨️ /help 查看指令"
            )
        else:
            line4 = '🔮 运势加载中...'
            line5 = '⌨️ /help 查看指令 │ /exit 退出'
        
        return HTML(
            f'<style fg="#8be9fd">{line1}</style>\n'
            f'<style fg="#8BE9FD">{line2}</style>\n'
            f'<style fg="#f1fa8c">{line3}</style>\n'
            f'<style fg="#ff79c6">{line4}</style>\n'
            f'<style fg="#bd93f9">{line5}</style>'
        )
    return get_status_bar


async def run_async_chat(chat, cmd_handler):
    """异步流式对话循环 (Prompt Toolkit)"""
    
    # 1. 初始化 Prompt Session (语法高亮 + 动态状态栏 + 自动补全)
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    
    # 指令补全器
    command_completer = WordCompleter([
        '/help', '/model', '/check', '/weather', '/refresh', '/save', '/speed', '/exit', 
        'exit', 'quit'
    ], ignore_case=True)

    from prompt_toolkit.key_binding import KeyBindings

    # 前面已导入 WordCompleter 等...
    
    # === 自定义快捷键 ===
    bindings = KeyBindings()

    @bindings.add("tab")
    def _(event):
        """Tab 键仅用于接受补全建议 (AutoSuggest)"""
        b = event.current_buffer
        if b.suggestion:
            b.insert_text(b.suggestion.text)
        # 不再绑定菜单触发，菜单会自动弹出或通过方向键交互

    session = PromptSession(
        lexer=ChatInputLexer(),
        style=input_style,
        bottom_toolbar=create_status_bar(chat),
        refresh_interval=0.2,
        completer=command_completer,
        complete_while_typing=True,  # 输入时自动弹出菜单 (列表可有可无，用方向键选)
        auto_suggest=AutoSuggestFromHistory(),
        key_bindings=bindings,
    )
    
    # 2. 准备仪表盘
    dashboard = get_dashboard()
    
    # 3. 简洁的输入提示词
    def get_prompt_message():
        return HTML(
            '<style fg="ansibrightcyan" bold="true">User</style> '
            '<style fg="ansibrightmagenta" bold="true">❯</style> '
        )

    # 4. 后台数据刷新任务 (低频，且只在 IDLE 时更新)
    async def data_refresh_loop():
        while True:
            try:
                await asyncio.sleep(60 * 5)
                # 仅当 App 运行时更新，且不处于 Thinking 模式
                if session.app and session.app.is_running:
                    await asyncio.to_thread(dashboard.refresh_data)
                    # 仅在后台静默更新数据，不强制刷新 UI
            except Exception:
                pass

    # 6. AI 自发消息任务
    async def ai_spontaneous_loop():
        import random
        witty_messages = [
            "正在思考宇宙终极答案...",
            "DeepSeek 引擎预热中...",
            "Gemini 正在观察你...",
            "喝杯咖啡休息一下？",
            "代码如诗，Bug 如歌...",
            "检测到高能极客力场...",
            "正在加载今日份的冷笑话...",
            "Python 是世界上最好的语言 (确信)",
            "记得 commit 你的代码...",
            "按 Alt+F4 可以获得... 并没有什么 :)"
        ]
        
        while True:
            await asyncio.sleep(random.randint(60, 180))
            try:
                # 30% 概率触发，且仅在 Session 活跃 (Input 阶段) 时，且不在思考中
                if session.app and session.app.is_running and random.random() < 0.3 and not is_thinking:
                    msg = random.choice(witty_messages)
                    dashboard.set_status_message(msg)
                    session.app.invalidate()
                        
                    # 显示 10 秒后清除
                    await asyncio.sleep(10)
                    dashboard.set_status_message("")
                    if session.app and session.app.is_running and not is_thinking:
                        session.app.invalidate()
            except Exception:
                pass

    # 启动后台任务 (移除 animation_loop)
    asyncio.create_task(data_refresh_loop())
    asyncio.create_task(ai_spontaneous_loop())
    
    print_info("输入 /help 查看指令，/exit 退出 (Ctrl+D 也可以退出)")

    # 5. 主交互循环
    while True:
        try:
            # === INPUT PHASE (State: STATIC) ===
            # 等待用户输入
            user_input = await session.prompt_async(message=get_prompt_message())
            user_input = user_input.strip()
            
            if not user_input:
                continue
            
            # 处理指令
            if cmd_handler.is_command(user_input):
                if cmd_handler.is_exit(user_input):
                    break
                
                    
                cmd_handler.handle(user_input)
                continue
                
            # === THINKING PHASE (State: THINKING - EXPLOSIVE) ===
            # console.print() # 空行 - 移除以防止刷屏
            
            
            
            try:
                # 在线程中运行阻塞的 API 调用 (ChatSession 现在支持回调和隐藏 Spinner)
                await asyncio.to_thread(
                    chat.send_message_stream, 
                    user_input, 
                    show_spinner=True
                )
            
            except Exception as e:
                print_error(f"Error: {e}")
            
            console.print()

        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:
            import traceback
            console.print("[bold red]─" * console.width + "[/]")
            traceback.print_exc()
            console.print("[bold red]─" * console.width + "[/]")
            print_error(f"发生错误: {e}")



def main():
    global current_model, current_backend
    
    setup_proxy()
    
    # 初始化系统
    try:
        client = get_client()
    except Exception as e:
        print_error(f"Gemini 初始化失败: {e}")
        return
    
    deepseek_client = None
    try:
        from core.deepseek import DeepSeekClient
        deepseek_client = DeepSeekClient()
    except Exception as e:
        pass
        
    time.sleep(0.5)
    
    print_success("系统初始化完成")
    
    current_model = "gemini-2.5-flash" 
    print_info(f"默认装载: {current_model}")
    
    chat = ChatSession(client, current_model)
    if deepseek_client:
        chat.bind_deepseek(deepseek_client)
    
    # 历史记录恢复功能已禁用
    # if has_last_session():
    #     if Confirm.ask("🔄 发现历史对话，是否恢复？", default=True):
    #         history = load_last_session()
    #         chat.set_history(history)
    #         print_success(f"已恢复 {len(history)//2} 轮对话")
    
    console.print()
    
    def model_selector():
        global current_model
        current_model = select_model(client)
        return current_model
    
    def switch_to_deepseek():
        global current_backend
        if deepseek_client:
            chat.set_backend("deepseek", deepseek_client)
            current_backend = "deepseek"

    def show_weather_now():
        w, t = fetch_weather_text()
        console.print(f"[bold blue]实时天气[/]\n{w}\n{t}")

    cmd_handler = CommandHandler(
        chat, 
        model_selector, 
        show_banner_static, 
        switch_to_deepseek, 
        weather_refresher=show_weather_now
    )
    
    try:
        # 启动 Async Loop
        asyncio.run(run_async_chat(chat, cmd_handler))

    finally:
        auto_save(chat.get_history())
        print_info("已保存会话")
        console.print("[bold cyan]👋 下次见，老司机！[/]")
        # 恢复终端光标闪烁 (ANSI: DECSCUSR 1 = 闪烁块状光标)
        import sys
        sys.stdout.write("\x1b[1 q")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
