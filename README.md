# 🗡️ 六脉神剑真厉害 (Cyberpunk Gemini CLI)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Textual](https://img.shields.io/badge/framework-Textual-green.svg)
![Gemini](https://img.shields.io/badge/AI-Gemini_2.0-magenta.svg)

> **"赛博朋克风格的终端 AI 助手，集成实时系统监控与生活服务。"**

这是一个基于 Python **Textual** 框架构建的高级 TUI (终端用户界面) 应用。它不仅是一个支持流式对话的 AI 聊天机器人，更是一个集成了系统仪表盘、天气预报、科技新闻和极客运势的综合生产力工作台。

## ✨ 核心特性

### 🤖 强力 AI 核心
*   **多模型切换**: 支持 `gemini-2.5-flash`, `gemini-flash-latest` 等最新模型。
*   **流式响应**: 类似黑客电影的打字机输出效果。
*   **记忆对话**: 具备完整的上下文多轮对话能力。
*   **智能重连**: 内置 API Key 轮询与自动重试机制，抗网络抖动。

### 🎨 沉浸式体验
*   **赛博朋克 UI**: 高对比度极客风格，支持 **Catppuccin** 四色主题 (Latte/Frappe/Macchiato/Mocha) 一键热切换。
*   **内联输入**: 真正的终端命令行体验，支持多行编辑。
*   **动态特效**: 包含 AI 思考波纹、故障风 (Glitch) 文本特效。

### 🛠️ 极客工具箱 (Dashboard)
*   **📊 系统监控**: 实时可视化 CPU、内存、GPU (NVIDIA)、磁盘 I/O 和网络流量。
*   **☁️ 实时天气**: 集成 Open-Meteo，提供精确到分钟的本地天气与明日预报。
*   **📰 科技新闻**: 自动抓取 Google News 科技版块，AI 自动翻译标题，滚动播报。
*   **🔮 每日运势**: 程序员专属运势 (宜重构、忌上线)，每天根据哈希种子生成。

## 🚀 快速开始

### 1. 环境准备
确保你的系统安装了 Python 3.10 或更高版本。

```bash
# 克隆项目
git clone https://github.com/your-repo/gemini-chatbot-textual.git
cd gemini-chatbot-textual

# 创建虚拟环境 (推荐)
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key
在项目根目录创建或修改 `config/settings.py` (或设置环境变量)，填入你的 Google Gemini API Key。

### 3. 启动应用
```bash
python app.py
```

## ⌨️ 操作指南

应用支持 **Slash 指令** 和 **快捷键** 两种操作方式。

| 功能 | 指令 | 快捷键 | 说明 |
| :--- | :--- | :--- | :--- |
| **发送消息** | (直接输入) | `Enter` | 发送对话 |
| **换行** | - | `Shift+Enter` | 输入框换行 |
| **切换模型** | `/model` | - | 轮换 Gemini 模型 |
| **切换服务** | `/service` | `Ctrl+D` | 切换主备服务 (GLM/Gemini) |
| **切换主题** | `/theme` | `F12` | 轮换 Catppuccin 配色 |
| **调整速度** | `/speed` | `Ctrl+S` | 调整打字机输出速度 |
| **清屏** | `/clear` | `F2` | 清空屏幕日志 |
| **重置** | `/reset` | `F5` | 清空屏幕 + **遗忘记忆** |
| **帮助** | `/help` | - | 显示帮助菜单 |
| **退出** | `/quit` | `Ctrl+Q` | 退出程序 |

## 📂 项目结构

```text
E:\Gemini CLI 实战\Gemini_chatbot- Textual\
├── app.py                # 主程序入口
├── core/                 # 核心逻辑
│   ├── chat.py           # (旧版) CLI 对话逻辑
│   └── client.py         # Gemini 客户端封装
├── services/             # 服务层
│   └── gemini_service.py # AI 服务 (流式处理/历史管理)
├── ui/                   # (旧版) UI 组件
├── widgets/              # Textual UI 组件
│   ├── message_log.py    # 消息列表与输入框
│   ├── status_bar.py     # 底部多功能状态栏
│   └── glitch_label.py   # 特效标签
├── utils/                # 工具库
│   ├── system_monitor.py # 系统硬件监控
│   ├── weather.py        # 天气 API
│   ├── news.py           # 新闻 RSS + 翻译
│   └── fortune.py        # 运势算法
├── styles/               # CSS 样式表 (TCSS)
└── themes_cloned/        # Catppuccin 主题资源
```

## 🤝 贡献
欢迎提交 Issue 或 PR！
特别感谢 [Textual](https://github.com/Textualize/textual) 和 [Rich](https://github.com/Textualize/rich) 提供的底层支持。

## 📜 许可证
MIT License