# Textual TUI 赛博朋克聊天机器人重构

将现有 `prompt_toolkit + Rich` 架构重构为基于 **Textual** 的现代组件化 TUI 应用，追求极致赛博朋克视觉体验和流畅异步交互。

---

## User Review Required

> [!IMPORTANT]
> **重大架构变更**：重构后将完全放弃 `prompt_toolkit`，改用 Textual 的事件驱动模型。现有的 `main.py`、`ui/dashboard.py`、`ui/layout.py` 将被替换。

> [!WARNING]
> **依赖变化**：需新增 `textual>=0.52.0` 依赖，并确保 Windows Terminal 支持 24-bit 真彩色。

---

## 需保留的核心逻辑

| 模块           | 文件                                                                                                                                                                                                                               | 保留内容                                                  |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| **API 客户端** | [client.py](file:///e:/Gemini%20CLI%20实战/Gemini_chatbot/core/client.py)                                                                                                                                                          | `ClientPool` 多 Key 轮换机制                              |
| **聊天会话**   | [chat.py](file:///e:/Gemini%20CLI%20实战/Gemini_chatbot/core/chat.py)                                                                                                                                                              | `ChatSession` 对话历史管理、`UsageMonitor` 速率监控       |
| **数据获取**   | [weather.py](file:///e:/Gemini%20CLI%20实战/Gemini_chatbot/utils/weather.py), [news.py](file:///e:/Gemini%20CLI%20实战/Gemini_chatbot/utils/news.py), [fortune.py](file:///e:/Gemini%20CLI%20实战/Gemini_chatbot/utils/fortune.py) | `WeatherFetcher`、`NewsFetcher`、`FortuneTeller` 全套保留 |
| **配置管理**   | [settings.py](file:///e:/Gemini%20CLI%20实战/Gemini_chatbot/config/settings.py)                                                                                                                                                    | API Key 加载、代理设置、系统指令                          |

---

## Proposed Changes

### Milestone 1: Skeleton & Scaffolding

#### [NEW] [app.py](file:///e:/Gemini%20CLI%20实战/Gemini_chatbot/app.py)

Textual 主应用入口类：

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import ScrollableContainer

class CyberpunkChatApp(App):
    """赛博朋克终端 - Gemini 聊天机器人"""
    CSS_PATH = "styles/cyberpunk.tcss"
    BINDINGS = [
        ("q", "quit", "退出"),
        ("ctrl+l", "clear", "清屏"),
        ("ctrl+m", "switch_model", "切换模型"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield ScrollableContainer(id="message-log")
        yield StatusBar(id="status-bar")
        yield InputBar(id="input-bar")
        yield Footer()
```

#### [NEW] [services/gemini_service.py](file:///e:/Gemini%20CLI%20实战/Gemini_chatbot/services/gemini_service.py)

将 `ClientPool` 封装为异步服务层：

```python
import asyncio
from core.client import get_client

class GeminiService:
    """异步 Gemini API 服务"""
    
    async def stream_chat(self, message: str, history: list):
        """非阻塞流式聊天"""
        client = get_client()
        # 使用 asyncio.to_thread 包装同步 API
        async for chunk in self._async_stream(client, message, history):
            yield chunk
```

---

### Milestone 2: The "Glitch" Component

#### [NEW] [widgets/glitch_label.py](file:///e:/Gemini%20CLI%20实战/Gemini_chatbot/widgets/glitch_label.py)

黑客帝国风格解码动画组件：

```python
import random
from textual.widgets import Static
from textual.reactive import reactive

class GlitchLabel(Static):
    """矩阵式文字解码动画组件"""
    
    GLITCH_CHARS = "0123456789ABCDEF!@#$%^&*"
    DECODE_FPS = 30  # 每秒帧数
    DECODE_DURATION = 0.5  # 解码时长(秒)
    
    target_text: reactive[str] = reactive("")
    
    def set_text_with_glitch(self, text: str):
        """触发解码动画"""
        self.target_text = text
        self._start_decode_animation()
    
    def _start_decode_animation(self):
        """启动逐字符解码"""
        self._decoded_chars = 0
        self._frame = 0
        self.set_interval(1/self.DECODE_FPS, self._animate_frame, 
                          pause=False, name="glitch")
    
    def _animate_frame(self):
        """每帧更新：已解码字符 + 乱码"""
        text = self.target_text
        decoded = text[:self._decoded_chars]
        remaining = len(text) - self._decoded_chars
        
        if remaining == 0:
            self.update(text)
            self.remove_interval("glitch")
            return
        
        # 生成乱码
        glitch = "".join(random.choice(self.GLITCH_CHARS) 
                         for _ in range(min(remaining, 20)))
        self.update(decoded + glitch)
        
        # 逐步解码
        self._frame += 1
        chars_per_frame = len(text) / (self.DECODE_FPS * self.DECODE_DURATION)
        self._decoded_chars = min(int(self._frame * chars_per_frame), len(text))
```

---

### Milestone 3: Async Data Flow

#### [NEW] [widgets/message_log.py](file:///e:/Gemini%20CLI%20实战/Gemini_chatbot/widgets/message_log.py)

滚动消息区，支持流式渲染：

```python
from textual.widgets import Static
from textual.containers import ScrollableContainer
from textual.message import Message

class MessageLog(ScrollableContainer):
    """对话消息列表"""
    
    class StreamChunk(Message):
        """流式文本块事件"""
        def __init__(self, text: str):
            self.text = text
            super().__init__()
    
    def add_user_message(self, content: str):
        self.mount(UserBubble(content))
        self.scroll_end()
    
    def add_ai_message_streaming(self):
        """创建流式 AI 消息气泡"""
        bubble = AIBubble()
        self.mount(bubble)
        return bubble
    
    def on_stream_chunk(self, event: StreamChunk):
        """处理流式文本块"""
        # 追加到当前 AI 气泡
        ...
```

#### [MODIFY] [core/chat.py](file:///e:/Gemini%20CLI%20实战/Gemini_chatbot/core/chat.py)

改造 `ChatSession` 支持异步生成器：

```diff
- def send_message_stream(self, user_input, show_spinner=True):
-     """同步流式输出"""
+ async def send_message_stream_async(self, user_input) -> AsyncGenerator[str, None]:
+     """异步流式生成器 - 供 Worker 调用"""
+     # 使用 asyncio.to_thread 包装同步 API 调用
+     response = await asyncio.to_thread(
+         self.client.models.generate_content_stream, ...
+     )
+     for chunk in response:
+         yield chunk.text
```

---

### Milestone 4: Cyberpunk Styling (TCSS)

#### [NEW] [styles/cyberpunk.tcss](file:///e:/Gemini%20CLI%20实战/Gemini_chatbot/styles/cyberpunk.tcss)

```css
/* 全局变量 */
$matrix-green: #00FF41;
$cyber-purple: #FF00FF;
$neon-blue: #00D4FF;
$bg-dark: #0D0D0D;
$scanline-overlay: rgba(0, 0, 0, 0.1);

/* 全局样式 */
Screen {
    background: $bg-dark;
    color: $matrix-green;
}

/* 霓虹发光边框 */
#message-log {
    border: heavy $neon-blue;
    background: $bg-dark;
    scrollbar-color: $cyber-purple;
}

/* 用户消息气泡 */
.user-bubble {
    background: $bg-dark;
    border: round $cyber-purple;
    color: $cyber-purple;
    margin: 1 2;
    padding: 1 2;
}

/* AI 消息气泡 - 矩阵绿 */
.ai-bubble {
    background: $bg-dark;
    border: round $matrix-green;
    color: $matrix-green;
    margin: 1 2;
    padding: 1 2;
}

/* 状态栏 - 扫描线效果 */
#status-bar {
    dock: bottom;
    height: 3;
    background: $bg-dark;
    border-top: solid $neon-blue;
}

/* Header 霓虹效果 */
Header {
    background: $bg-dark;
    color: $neon-blue;
}

Footer {
    background: $bg-dark;
    color: $matrix-green 50%;
}
```

---

## 新增目录结构

```
Gemini_chatbot/
├── app.py              # [NEW] Textual 主入口
├── styles/
│   └── cyberpunk.tcss  # [NEW] 赛博朋克主题
├── widgets/
│   ├── __init__.py     # [NEW]
│   ├── glitch_label.py # [NEW] 解码动画组件
│   ├── message_log.py  # [NEW] 消息列表
│   ├── input_bar.py    # [NEW] 输入栏
│   └── status_bar.py   # [NEW] 状态栏
├── services/
│   └── gemini_service.py # [NEW] 异步 API 服务层
├── core/               # [KEEP] 保留
├── utils/              # [KEEP] 保留
├── config/             # [KEEP] 保留
├── ui/                 # [DEPRECATED] 重构后删除
└── main.py             # [DEPRECATED] 被 app.py 替代
```

---

## Verification Plan

### 1. 单元测试

由于项目目前没有现有测试套件，建议创建基础测试：

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 测试 GlitchLabel 动画逻辑
pytest tests/test_glitch_label.py -v
```

### 2. 手动验证

| 步骤 | 操作                 | 预期结果                                          |
| ---- | -------------------- | ------------------------------------------------- |
| 1    | 运行 `python -m app` | 应用启动，显示赛博朋克主题界面                    |
| 2    | 输入任意消息并回车   | 用户消息以紫色边框气泡显示                        |
| 3    | 等待 AI 响应         | AI 消息以矩阵绿边框显示，**文字应有乱码解码动画** |
| 4    | 连续发送 3 条消息    | 消息区应能滚动，无卡顿                            |
| 5    | 按 `Ctrl+M`          | 触发模型切换菜单                                  |
| 6    | 按 `Q`               | 应用正常退出                                      |

### 3. 用户验收

请用户确认：

1. **动画效果**：GlitchLabel 解码动画是否有"黑客帝国"感？
2. **配色方案**：霓虹配色在 Windows Terminal 下是否清晰美观？
3. **流畅度**：长对话场景下是否有明显卡顿？

---

## 依赖更新

```diff
# requirements.txt
  google-genai
  rich
  python-dotenv
  openai
+ textual>=0.52.0
```
