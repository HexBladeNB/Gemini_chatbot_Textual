"""
代理与API配置 (python-dotenv方案)
"""
import os
from pathlib import Path

# 加载.env文件（override=True 让 .env 覆盖系统环境变量）
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path, override=True)
except ImportError:
    pass  # 如果没安装dotenv，使用系统环境变量

# 代理配置
PROXY_URL = os.getenv("PROXY_URL", "http://127.0.0.1:7897")

# 和风天气配置
QWEATHER_KEY = os.getenv("QWEATHER_KEY", "")
QWEATHER_HOST = os.getenv("QWEATHER_HOST", "devapi.qweather.com") # 专属 Host
QWEATHER_LOCATION = os.getenv("QWEATHER_LOCATION", "101300101")  # 默认南宁

# 打字机效果配置 (slow=40ms, normal=15ms, fast=5ms, instant=0ms)
_SPEED_MAP = {"slow": 0.04, "normal": 0.015, "fast": 0.005, "instant": 0}
TYPEWRITER_SPEED = os.getenv("TYPEWRITER_SPEED", "slow")
TYPEWRITER_DELAY = _SPEED_MAP.get(TYPEWRITER_SPEED.lower(), 0.015)

def setup_proxy():
    """设置系统代理环境变量"""
    os.environ['HTTP_PROXY'] = os.environ['HTTPS_PROXY'] = PROXY_URL
    os.environ['http_proxy'] = os.environ['https_proxy'] = PROXY_URL
    os.environ['all_proxy'] = PROXY_URL

def load_api_keys():
    """从环境变量加载 API 密钥列表 (支持逗号分隔多Key)"""
    val = os.getenv("GEMINI_API_KEY", "")
    if not val:
        return []
    # 支持 , 或 ; 分隔，并去除空格
    keys = [k.strip() for k in val.replace(';', ',').split(',') if k.strip()]
    return keys

# 系统指令 - 人格定义
SYSTEM_INSTRUCTION = """
你是一个技术精湛、嗅觉敏锐且偶尔不正经的极客黑客助手，代号"六脉神剑真厉害"。

### 🧠 核心思维 (Critical Thinking)
1. **情报优先 (Intel First)**：
   - 你时刻关注科技最前沿。遇到任何不确定的术语、新出的工具（如 'Project IDX', 'Antigravity', 'DeepSeek-V3'）或即时新闻，**必须立刻调用 Google Search**。
   - 严禁不懂装懂。如果知识库里没有，就去网上搜，搜不到就老实说。
   - 你的目标是提供准确、实时的技术情报，而不是背诵过期的文档。

2. **输出规范 (Format Protocol)**：
   - **全面启用 Markdown**：使用 **加粗** 强调重点，使用 `Code` 标记术语。
   - **代码块必须规范**：所有代码必须包裹在 ```language ... ``` 中。这非常重要，因为用户有自动化工具提取这些代码。
   - **层级分明**：使用 `###` 标题分隔段落，使用 `-` 列表展示要点。

3. **性格特征 (Persona)**：
   - **硬核极客**：平时专业、干练、极简。能用一行代码解决的，绝不废话十句。
   - **有素质的吐槽**：在遇到极其弱智的错误或惊人的操作时，允许冷不丁（低概率）蹦出一句“卧槽”、“牛逼”或国粹来吐槽。
   - **反差萌**：是一个“有素质的老流氓”，技术过硬，说话好听（偶尔难听）。

### 🛡️ 行为准则 (Rules of Engagement)
- **代码输出**：
  - 默认提供 Windows PowerShell 兼容的命令。
  - 复杂代码直接给出完整实现，不要像便秘一样一点点挤。
- **教学模式**：
  - 回答复杂问题时，先给出 **[大纲/架构]**，待用户确认感兴趣的点后，再展开 **[详细解释]**。
  - 不要一次性输出几千字的长文，没人看。
- **关于 Antigravity (Google IDE)**：
  - 特别注意：如果你不知道 'Antigravity' 是什么，去搜！(提示：这可能是 Project IDX 的别名或者是某种新的 Python 调试概念，具体看语境)。不要急着否认它的存在。

> "Talk is cheap. Show me the code."
"""


# ==================== 智谱 AI 配置 ====================

def load_zhipu_api_keys():
    """从环境变量加载智谱 API 密钥"""
    val = os.getenv("ZHIPU_API_KEY", "")
    if not val:
        return []
    # 智谱稳定，只需要一个 Key
    return [val.strip()]


# 智谱模型配置（根据用户实际配额更新于 2026-01-05）
ZHIPU_MODELS = {
    # 赠送额度（按 tokens 降序排列，优先使用）
    "glm-4.5-air": {"name": "GLM-4.5 Air", "desc": "947万 免费", "type": "free"},
    "glm-4.6": {"name": "GLM-4.6", "desc": "700万 免费", "type": "free"},
    "glm-4.6v": {"name": "GLM-4.6V", "desc": "600万 免费", "type": "free"},
    # 付费额度
    "glm-4.7": {"name": "GLM-4.7", "desc": "588万 付费", "type": "paid"},
}

# 主备服务配置
PRIMARY_SERVICE = os.getenv("PRIMARY_SERVICE", "zhipu").lower()
ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"

# 智谱默认模型（优先使用赠送额度最多的）
DEFAULT_ZHIPU_MODEL = "glm-4.5-air"
