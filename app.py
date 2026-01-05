"""
赛博朋克终端 - 多模型聊天机器人
基于 Textual 框架的现代 TUI 应用
支持 Gemini + 智谱 GLM 双引擎
"""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import ScrollableContainer
from textual.binding import Binding
from textual import work

from widgets.message_log import MessageLog, InlineInput, ShortcutTriggered
from services.gemini_service import GeminiService
from services.zhipu_service import ZhipuService
from config.settings import PRIMARY_SERVICE, ENABLE_WEB_SEARCH, ZHIPU_MODELS, DEFAULT_ZHIPU_MODEL


class CyberpunkChatApp(App):
    """🗡️ 六脉神剑真厉害 - 极客剑灵助手"""
    
    TITLE = "🗡️ 六脉神剑真厉害"
    CSS_PATH = [
        "styles/base.tcss",
        "styles/all_themes.tcss"
    ]
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "退出程序", show=True),
        Binding("f5", "reset_session", "重置会话", show=True),   # 清空对话历史
        Binding("f2", "clear_log", "清空屏幕", show=True),      # 清除屏幕消息
        Binding("f12", "switch_flavor", "切换主题", show=True), # 切换界面风格
        Binding("ctrl+s", "switch_speed", "切换速度", show=True),
        Binding("ctrl+d", "switch_service", "切换服务", show=True),  # 主/备服务切换
    ]


    def __init__(self):
        super().__init__()
        # 初始化两个服务
        self.zhipu_service = ZhipuService(enable_web_search=ENABLE_WEB_SEARCH)
        self.gemini_service = GeminiService()

        # 根据配置选择主服务
        if PRIMARY_SERVICE == "zhipu":
            self.primary_service = self.zhipu_service
            self.fallback_service = self.gemini_service
            self.current_model = DEFAULT_ZHIPU_MODEL  # 默认使用免费额度最多的模型
            self._is_zhipu_primary = True
        else:
            self.primary_service = self.gemini_service
            self.fallback_service = self.zhipu_service
            self.current_model = "gemini-2.5-flash"
            self._is_zhipu_primary = False

        self.using_primary = True  # 当前是否使用主服务
        self.current_flavor = "mocha"
        self.flavors = ["latte", "frappe", "macchiato", "mocha"]
        self._total_tokens = 0  # 会话总 token 统计

    @property
    def active_service(self):
        """获取当前活跃的服务"""
        return self.primary_service if self.using_primary else self.fallback_service

    @property
    def service_name(self) -> str:
        """获取当前服务名称"""
        if self.using_primary:
            return "智谱 GLM" if self._is_zhipu_primary else "Gemini"
        else:
            return "Gemini (备)" if self._is_zhipu_primary else "智谱 GLM (备)"

    def compose(self) -> ComposeResult:
        """构建 UI 布局"""
        yield Header(show_clock=True)
        yield MessageLog(id="message-log")
        # yield StatusBar(id="status-bar")  # 临时屏蔽，排查刷新问题
    
    def on_mount(self) -> None:
        """应用挂载后初始化"""
        import platform
        from datetime import datetime

        self.screen.add_class(f"theme-{self.current_flavor}")
        message_log = self.query_one("#message-log", MessageLog)

        # 获取系统信息
        os_info = f"{platform.system()} {platform.release()}"
        py_ver = platform.python_version()
        boot_time = datetime.now().strftime("%H:%M:%S")

        # 获取当前模型的详细信息
        if self.current_model.startswith("glm-"):
            model_info = ZHIPU_MODELS.get(self.current_model, {})
            model_display = f"{model_info.get('name', self.current_model)} [dim]({model_info.get('desc', '')})[/]"
        else:
            model_display = self.current_model

        # 极简启动自检风格 (Rich Markup)
        web_status = "[cyan]联网[/]" if ENABLE_WEB_SEARCH else "[dim]离线[/]"
        welcome_msg = rf"""
[bold bright_cyan]🗡️  SYSTEM ONLINE[/]   [dim]Target: {os_info}  ::  Python {py_ver}  ::  T={boot_time}[/]

[bold white]ENGINE:[/] [cyan]{self.service_name}[/]
[bold white]MODEL:[/]  [cyan]{model_display}[/]
[bold white]WEB:[/]    {web_status}

[bold white]CONTROLS:[/][dim]
  [bold green]F5   [/]  Reset Session       [bold green]F2     [/]  Clear Screen
  [bold green]F12  [/]  Switch Theme        [bold green]/save  [/]  Export Code
  [bold green]C+D  [/]  Switch Service      [bold green]↑ / ↓  [/]  History Nav
  [bold green]C+Q  [/]  Quit App[/]

[dim italic]Sword Spirit is listening...[/]
"""
        # 显示欢迎消息 (直接传给 Static 渲染 Markup)
        message_log.add_system_message(welcome_msg)
        # 创建内联输入框
        message_log.create_inline_input()
    
    def on_app_focus(self, event) -> None:
        """当应用获得焦点时，自动聚焦到输入框"""
        self._focus_input()
    
    def on_descendant_focus(self, event) -> None:
        """任何子组件获得焦点时，确保输入框可用"""
        pass  # 可以在这里添加额外逻辑
    
    def _focus_input(self) -> None:
        """聚焦到当前输入框"""
        try:
            message_log = self.query_one("#message-log", MessageLog)
            if message_log._current_input:
                message_log._current_input.focus()
        except Exception:
            pass
    
    # 已移除回车模式处理
    
    async def on_inline_input_submitted(self, event: "InlineInput.Submitted") -> None:
        """处理内联输入提交"""
        user_input = event.value.strip()
        if not user_input:
            return

        message_log = self.query_one("#message-log", MessageLog)

        # 移除当前输入框容器
        if event.input.parent:
            event.input.parent.remove()

        # 检查是否是指令
        if user_input.startswith("/"):
            await self._handle_command(user_input)
        else:
            # 显示用户消息
            message_log.add_user_message(user_input)
            # 启动异步 AI 响应
            self._stream_ai_response(user_input)

        # 无论是否是指令，如果不是流式响应（指令通常立即完成），都需要重新创建输入框
        # 注意：_stream_ai_response 会在 finally 中创建输入框，所以这里只需要处理指令的情况
        if user_input.startswith("/"):
             message_log.create_inline_input()

    def on_shortcut_triggered(self, event: ShortcutTriggered) -> None:
        """处理来自 InlineInput 的快捷键事件"""
        action = event.action

        # 调用对应的 action 方法
        if action == "quit":
            self.exit()
        elif action == "reset_session":
            self.action_reset_session()
        elif action == "clear_log":
            self.action_clear_log()
        elif action == "switch_flavor":
            self.action_switch_flavor()
        elif action == "switch_model":
            self.action_switch_model()
        elif action == "switch_speed":
            self.action_switch_speed()
        elif action == "switch_service":
            self.action_switch_service()
        else:
            self._add_system_message(f"❌ 未知快捷键: {action}")
        event.stop()  # 阻止事件继续传播

    async def _handle_command(self, command_str: str) -> None:
        """处理 Slash 指令"""
        parts = command_str.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd in ["/help", "/?", "/h"]:
            self.action_show_help()
        elif cmd in ["/usage", "/u"]:
            self.action_show_usage()
        elif cmd in ["/clear", "/cls"]:
            self.action_clear_log()
        elif cmd in ["/reset", "/restart"]:
            self.action_reset_session()
        elif cmd in ["/undo", "/pop"]:
            self.action_undo_last_turn()
        elif cmd in ["/save", "/save_code", "/code"]:
            filename = args[0] if args else "code_snippet.txt"
            self.action_save_code(filename)
        elif cmd in ["/model", "/m"]:
            self.action_switch_model()
        elif cmd in ["/theme", "/flavor", "/t"]:
            self.action_switch_flavor()
        elif cmd in ["/speed", "/s"]:
            self.action_switch_speed()
        elif cmd in ["/quit", "/exit", "/q"]:
            self.exit()
        elif cmd in ["/service", "/engine", "/switch"]:
            self.action_switch_service()
        else:
            self._add_system_message(f"❌ 未知指令: {cmd} (输入 /help 查看帮助)")

    def action_show_help(self) -> None:
        """显示帮助信息"""
        # 注意：Rich Markup 会误将 /xxx 解析为闭合标签，需用反斜杠转义
        help_text = f"""
[bold cyan]🛠️ 指令手册[/bold cyan]

[bold white]指令[/]          [bold white]快捷键[/]    [bold white]说明[/]
──────────────────────────────────────────────
[yellow]/usage[/]        -          查看额度消耗统计
[yellow]/help[/]         -          显示此帮助信息
[yellow]/undo[/]         -          撤销上一轮对话
[yellow]/save[/] <file>  -          保存代码块
[yellow]/model[/]        -          切换 AI 模型
[yellow]/service[/]      Ctrl+D     切换主备服务
[yellow]/theme[/]        F12        切换界面主题
[yellow]/speed[/]        Ctrl+S     切换打字机速度
[yellow]/clear[/]        F2         清空屏幕日志
[yellow]/reset[/]        F5         重置会话
[yellow]/quit[/]         Ctrl+Q     退出程序

[dim]当前服务: {self.service_name} | 模型: {self.current_model}[/]
"""
        self._add_system_message(help_text)

    def action_undo_last_turn(self) -> None:
        """撤销上一轮对话"""
        # 1. 服务层撤销
        success = self.active_service.undo_last_turn()
        if not success:
            self._add_system_message("⚠️ 无法撤销：历史记录不足或已空。")
            return
            
        # 2. UI 层撤销 (删除最后两个气泡: AI 和 User)
        message_log = self.query_one("#message-log", MessageLog)
        
        # 从子组件列表中从后往前找
        bubbles_to_remove = []
        found_ai = False
        found_user = False
        
        # 倒序遍历子组件
        children = list(message_log.children)
        for child in reversed(children):
            # 跳过输入框容器
            if "input-container" in child.classes:
                continue
            
            # 识别气泡类型 (通过类名判断更稳健)
            # GlitchAIBubble 没有显式的 class 属性判断，只能用类型或 looking at class list
            # 我们的气泡都在 message_log.py 里定义了
            from widgets.message_log import UserBubble, GlitchAIBubble
            
            if not found_ai and isinstance(child, GlitchAIBubble):
                bubbles_to_remove.append(child)
                found_ai = True
            elif found_ai and not found_user and isinstance(child, UserBubble):
                bubbles_to_remove.append(child)
                found_user = True
                break # 找到一对了，停止
        
        if found_ai and found_user:
            for bubble in bubbles_to_remove:
                bubble.remove()
            self._add_system_message("↩️ 已撤销上一轮对话")
        else:
            self._add_system_message("⚠️ UI 同步警告：未能完全匹配到最后的气泡对，仅撤销了记忆。")

    def action_save_code(self, filename: str) -> None:
        """提取最后一条 AI 回复中的代码块并保存"""
        # 获取最后一条 AI 消息的内容
        history = self.active_service.get_history()
        # 检查最后一条消息是否是 AI 回复 (model 或 assistant)
        if not history or history[-1][0] not in ["model", "assistant"]:
            self._add_system_message("⚠️ 无法保存：最后一条消息不是 AI 回复。")
            return
        
        content = history[-1][1]
        
        # 正则提取代码块
        import re
        # 匹配 ```language ... ``` 块
        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", content, re.DOTALL)
        
        if not code_blocks:
            self._add_system_message("⚠️ 未检测到代码块。")
            return
        
        # 如果有多个，全部合并保存
        full_code = "\n\n# === Code Block ===\n".join(code_blocks)
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(full_code)
            
            import os
            abs_path = os.path.abspath(filename)
            self._add_system_message(f"💾 代码已保存至:\n{abs_path}")
        except Exception as e:
            self._add_system_message(f"❌ 保存失败: {str(e)}")

    def action_show_usage(self) -> None:
        """显示额度消耗报告"""
        history_len = len(self.active_service._history) // 2
        service_type = "智谱 GLM" if self._is_zhipu_primary and self.using_primary else \
                       "Gemini" if not self._is_zhipu_primary and self.using_primary else \
                       "智谱 GLM (备)" if self._is_zhipu_primary else "Gemini (备)"

        usage_text = f"""
### 📊 额度消耗报告 (Usage Report)

*   **当前服务**: `{service_type}`
*   **当前模型**: `{self.current_model}`
*   **本会话总计**: `{self._total_tokens:,}` tokens (估算)
*   **已对话轮数**: `{history_len}` 轮

> 💡 **注**: 以上统计为估算值。智谱 GLM-4 约 10元/千tokens。
"""
        self._add_system_message(usage_text)

    def action_reset_session(self) -> None:
        """重置会话 (清空屏幕 + 历史)"""
        self.active_service.clear_history()
        self.action_clear_log()
        self._add_system_message("🧠 记忆已擦除，会话重置。")

    @work(exclusive=True, thread=True)
    def _stream_ai_response(self, user_input: str) -> None:
        """后台线程处理 AI 流式响应"""
        message_log = self.query_one("#message-log", MessageLog)

        # 创建 AI 消息气泡
        ai_bubble = self.call_from_thread(message_log.add_ai_message_streaming, self.current_model)

        try:
            # 调用流式 API
            for chunk in self.active_service.stream_chat_sync(user_input, self.current_model):
                # 检测重连信号
                if chunk.startswith("__RECONNECTING__:"):
                    parts = chunk.split(":")
                    attempt = int(parts[1])
                    max_attempts = int(parts[2])
                    self.call_from_thread(ai_bubble.set_reconnecting, attempt, max_attempts)
                    continue
                # 检测 Token 统计信号
                if chunk.startswith("__TOKEN_STATS__:"):
                    turn_tokens = int(chunk.split(":")[1])
                    self._total_tokens += turn_tokens
                    continue
                self.call_from_thread(ai_bubble.append_text, chunk)

            # 完成后显示
            self.call_from_thread(ai_bubble.finalize_with_glitch)

        except Exception as e:
            error_msg = str(e)
            self.call_from_thread(ai_bubble.set_error, error_msg)

            # 主服务失败时自动切换到备用服务
            if self.using_primary:
                self.using_primary = False
                # 更新当前模型为备用服务的默认模型
                if self._is_zhipu_primary:
                    # 从智谱切换到 Gemini
                    self.current_model = "gemini-2.5-flash"
                else:
                    # 从 Gemini 切换到智谱
                    self.current_model = "glm-4"

                self.call_from_thread(
                    self._add_system_message,
                    f"⚠️ 主服务不可用，已自动切换至备用服务 ({self.service_name})"
                )

        finally:
            # 创建新的内联输入框
            self.call_from_thread(message_log.create_inline_input)
    
    def _add_system_message(self, text: str) -> None:
        """添加系统消息"""
        message_log = self.query_one("#message-log", MessageLog)
        message_log.add_system_message(text)
    
    def action_clear_log(self) -> None:
        """清空消息记录"""
        message_log = self.query_one("#message-log", MessageLog)
        message_log.clear_messages()
        message_log.add_system_message("📝 消息已清空")
        message_log.create_inline_input()
    
    def action_switch_model(self) -> None:
        """切换模型 - 显示详细的模型列表"""
        # 判断当前是智谱还是 Gemini
        is_current_zhipu = self.current_model.startswith("glm-")

        if is_current_zhipu:
            # 智谱模型切换
            models = list(ZHIPU_MODELS.keys())
            current_idx = models.index(self.current_model) if self.current_model in models else 0
            next_model = models[(current_idx + 1) % len(models)]
            self.current_model = next_model
            self.zhipu_service.set_model(next_model)

            # 构建详细的模型列表消息
            lines = ["[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]"]
            lines.append("[bold yellow]🔄 模型已切换[/bold yellow]")
            lines.append("")
            lines.append("[bold white]可用智谱模型:[/]")

            for i, model_id in enumerate(models):
                info = ZHIPU_MODELS[model_id]
                is_current = model_id == next_model
                prefix = "[bold green]▶[/] " if is_current else "  "

                # 当前模型用醒目的颜色
                if is_current:
                    model_name = f"[bold green]{info['name']}[/]"
                    desc = f"[bold green]{info['desc']}[/]"
                else:
                    model_name = info['name']
                    desc = info['desc']

                lines.append(f"{prefix}{model_name} - {desc}")

            lines.append("")
            lines.append(f"[dim]当前使用: [cyan]{ZHIPU_MODELS[next_model]['name']}[/][/dim]")
            lines.append("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")

            self._add_system_message("\n".join(lines))
        else:
            # Gemini 模型切换
            models = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]
            current_idx = models.index(self.current_model) if self.current_model in models else 0
            next_model = models[(current_idx + 1) % len(models)]
            self.current_model = next_model

            # 构建 Gemini 模型列表消息
            lines = ["[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]"]
            lines.append("[bold yellow]🔄 Gemini 模型已切换[/bold yellow]")
            lines.append("")

            for i, model_id in enumerate(models):
                is_current = model_id == next_model
                prefix = "[bold green]▶[/] " if is_current else "  "
                model_name = f"[bold green]{model_id}[/]" if is_current else model_id
                lines.append(f"{prefix}{model_name}")

            lines.append("")
            lines.append(f"[dim]当前使用: [cyan]{next_model}[/][/dim]")
            lines.append("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")

            self._add_system_message("\n".join(lines))

    def action_switch_service(self) -> None:
        """手动切换主备服务"""
        self.using_primary = not self.using_primary

        # 更新当前模型
        if self.using_primary:
            # 切换到主服务
            if self._is_zhipu_primary:
                self.current_model = self.zhipu_service._model
            else:
                self.current_model = "gemini-2.5-flash"
        else:
            # 切换到备用服务
            if self._is_zhipu_primary:
                self.current_model = "gemini-2.5-flash"
            else:
                self.current_model = self.zhipu_service._model

        self._add_system_message(f"🔄 服务切换: 当前使用 {self.service_name} | 模型: {self.current_model}")
    
    def action_switch_speed(self) -> None:
        """切换自动播放速度"""
        from widgets.glitch_label import cycle_speed
        new_speed = cycle_speed()
        speed_names = {"slow": "🐢 慢速 (1秒/行)", "normal": "🚀 正常 (0.3秒/行)", "fast": "⚡ 快速 (0.1秒/行)"}
        self._add_system_message(f"速度: {speed_names.get(new_speed, new_speed)}")

    def action_switch_flavor(self) -> None:
        """切换 Catppuccin 风味 (Latte -> Frappe -> Macchiato -> Mocha)"""
        # 移除当前风味 class
        self.screen.remove_class(f"theme-{self.current_flavor}")
        
        # 循环切换
        current_idx = self.flavors.index(self.current_flavor)
        next_flavor = self.flavors[(current_idx + 1) % len(self.flavors)]
        
        # 添加新风味 class
        self.current_flavor = next_flavor
        self.screen.add_class(f"theme-{next_flavor}")
        
        self._add_system_message(f"🎨 主题风味: {next_flavor.title()}")



def main():
    """主入口"""
    app = CyberpunkChatApp()
    app.run()


if __name__ == "__main__":
    main()
