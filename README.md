# 🗡️ 六脉神剑真厉害 (Cyberpunk Gemini CLI)

<div align="center">
  <img src="screenshot/封面.png" width="800" alt="Cyberpunk Chatbot Header">
  
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
  [![Textual](https://img.shields.io/badge/framework-Textual-green.svg)](https://github.com/Textualize/textual)
  [![Gemini](https://img.shields.io/badge/AI-Gemini_2.0-magenta.svg)](https://ai.google.dev/)
  [![Zhipu](https://img.shields.io/badge/AI-GLM--4-orange.svg)](https://bigmodel.cn/)
</div>

---

> **"赛博朋克风格的终端 AI 助手，集成双引擎驱动与极客工作台。"**

这是一个基于 Python **Textual** 框架构建的高级 TUI (终端用户界面) 应用。它不仅支持流式对话，更是一个集成了系统监控、人格注入与多主题热切换的深夜极客伴侣。

## 🌟 核心亮点

### 🚀 双引擎极速响应 (Zhipu GLM + Google Gemini)
- **智能双待**：内置 **智谱 GLM-4** 与 **Google Gemini** 双 API 引擎。
- **自动灾备**：主服务连接失败时，秒级自动切换至备用引擎，确保对话不中断。
- **人格注入**：内置“六脉神剑”极客助手人格，默认启用技术精湛且带有个性化吐槽风格的系统指令。

### 🎨 深度定制的 TUI 美学
- **故障风 (Glitch) 渲染**：AI 回复过程伴随酷炫的解码动画。
- **Catppuccin 主题**：支持 Mocha、Macchiato、Frappe、Latte 四种专业色彩风味，`F12` 一键实时无损切换。
- **精致控件**：精心调优的滚动条交互（带悬停反馈）与完美对齐的快捷键菜单。

### 🛠️ 生产力极客工具
- **代码导出**：支持 `/save` 指令一键提取 AI 回复中的所有代码块并保存为本地文件。
- **热重载开发**：内置 `dev.py` 监控，支持代码修改后应用自动重载（Hot Reload），开发体验拉满。
- **内联式输入**：真正的命令行交互，支持多行输入与历史记录导航。

## � 快速部署

### 1. 环境构建
确保 Python 3.10+ 环境，推荐使用 PowerShell 环境运行：

```powershell
# 克隆项目
git clone https://github.com/HexBladeNB/Gemini_chatbot_Textual.git
cd Gemini_chatbot_Textual

# 初始化虚拟环境
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
```

### 2. 核心配置
编辑根目录下的 `.env` 文件：

```env
GEMINI_API_KEY=你的谷歌密钥
ZHIPU_API_KEY=你的智谱密钥

# 可选配置
PRIMARY_SERVICE=zhipu        # 默认主服务: zhipu 或 gemini
ENABLE_WEB_SEARCH=true       # 开启智谱联网搜索
```

### 3. 热力驱动
```powershell
# 直接启动应用
python app.py

# 开发模式（修改代码自动热重启）
python dev.py
```

## ⌨️ 快捷指令菜单

| 动作         | 快捷键   | Slash 指令 | 说明                           |
| :----------- | :------- | :--------- | :----------------------------- |
| **发送消息** | `Enter`  | -          | 提交对话内容                   |
| **切换服务** | `Ctrl+D` | `/service` | 在主/备引擎间热切换            |
| **切换模型** | -        | `/model`   | 轮换当前引擎下的可用模型       |
| **导出代码** | -        | `/save`    | 自动抓取最后一段 AI 代码块存盘 |
| **切换主题** | `F12`    | `/theme`   | 轮换 Catppuccin 界面风格       |
| **调整速度** | `Ctrl+S` | `/speed`   | 切换打字机输出频率             |
| **重置会话** | `F5`     | `/reset`   | 瞬间擦除记忆与屏幕             |
| **清空屏幕** | `F2`     | `/clear`   | 仅清理历史显示区域             |
| **退出系统** | `Ctrl+Q` | `/quit`    | 安全关闭神经连接               |

## 🏗️ 架构布局

```text
Gemini_chatbot- Textual/
├── app.py                # 系统中枢
├── dev.py                # 自动热重载调度器
├── services/             # API 引擎封装 (Gemini/Zhipu)
├── widgets/              # 自定义 UI 控件 (内联输入器/故障风标签)
├── styles/               # TUI 样式表 (TCSS + Catppuccin)
├── config/               # 系统与人格定义
└── screenshot/           # 视觉档案
```

## 📜 LICENSE
MIT License. Created by [HexBladeNB](https://github.com/HexBladeNB).

---
<p align="center">"Talk is cheap. Show me the code."</p>