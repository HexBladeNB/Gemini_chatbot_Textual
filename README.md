# 🤖 Gemini CLI 极客终端 (Gemini CLI Chatbot)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Rich](https://img.shields.io/badge/UI-Rich-purple)](https://github.com/Textualize/rich)

一个专为极客打造的高性能、沉浸式命令行聊天机器人。集成了 **Google Gemini** 与 **DeepSeek** 双引擎，拥有炫酷的动态仪表盘、实时资讯流和极致的交互体验。

![Screenshot](https://via.placeholder.com/800x450.png?text=Gemini+CLI+Dashboard+Preview)
*(此处可替换为项目实际运行截图)*

## ✨ 核心特性

*   **⚡ 双核驱动**: 支持 **Google Gemini** (Pro/Flash) 与 **DeepSeek** (Coder/Chat) 模型无缝切换。
*   **🎨 沉浸式 UI**: 基于 `Rich` 和 `Prompt Toolkit` 构建，拥有动态刷新率、打字机流式输出和代码高亮。
*   **📰 智能资讯**: 
    *   **实时天气**: 集成 Open-Meteo 与和风双源天气，精准预报。
    *   **科技热榜**: 自动抓取 Hacker News 热门话题，并由 AI 实时生成中文摘要。
    *   **每日运势**: 极客专属的“黄历”与星座运势。
*   **🛠️ 开发者友好**:
    *   支持完整的 Markdown 渲染与代码语法高亮。
    *   智能命令补全 (IntelliSense-like)。
    *   多线程异步架构，拒绝界面卡顿。
*   **📡 网络优化**: 内置完善的代理支持 (HTTP/SOCKS5)，解决 API 连接问题。

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/HexBladeNB/Gemini_chatbot.git
cd Gemini_chatbot
```

### 2. 安装依赖
建议使用 Conda 或 venv 创建虚拟环境：
```bash
pip install -r requirements.txt
```

### 3. 环境配置
复制配置文件模板并填入你的 API Key：
```bash
cp .env.example .env
```
编辑 `.env` 文件：
```ini
# Google Gemini API Key
GEMINI_API_KEY=your_gemini_key_here

# DeepSeek API Key (可选)
DEEPSEEK_API_KEY=your_deepseek_key_here

# 网络代理 (可选，如不需要请留空)
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

### 4. 启动终端
```bash
python main.py
```

## ⌨️ 指令手册

在对话过程中，随时输入 `/` 呼出命令菜单：

| 指令 | 功能描述 |
| :--- | :--- |
| `/help` | 📖 显示完整的帮助菜单 |
| `/model` | 🔧 切换 AI 模型 (Gemini / DeepSeek) |
| `/check` | 🏥 运行全能模型体检脚本 (网络/API诊断) |
| `/weather` | 🌤️ 强制刷新天气数据 |
| `/refresh` | 🔄 也是清屏，彻底重绘 UI |
| `/save` | 💾 手动保存当前对话记录 |
| `/exit` | 👋 安全退出程序 |

## 📂 项目结构

```text
Gemini_chatbot/
├── commands/           # 指令处理逻辑
├── config/             # 配置加载与环境变量
├── core/               # LLM 核心客户端 (Gemini/DeepSeek)
├── data/               # 缓存数据 (天气/新闻)
├── ui/                 # 仪表盘与界面渲染
├── utils/              # 工具库 (News/Weather/Fortune)
├── main.py             # 程序主入口
└── requirements.txt    # 项目依赖
```

## 🛠️ 技术栈

*   **Language**: Python 3.10+
*   **UI Framework**: Rich, Prompt Toolkit
*   **API SDK**: Google Generative AI, OpenAI (for DeepSeek)
*   **Data Source**: Open-Meteo, Hacker News API

## 🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request！如果你喜欢这个项目，请给它一个 ⭐️ Star！

---
*Built with ❤️ by HexBladeNB*
