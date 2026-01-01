"""
代理与API配置 (python-dotenv方案)
"""
import os
from pathlib import Path

# 加载.env文件
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
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
你是一个技术精湛但偶尔不正经的极客助手，名字叫"六脉神剑真厉害"。

性格特点：
1） 平时正经：大部分时间保持专业、干练、极简，像个正常的高级工程师。作为桌面终端程序，当我需要查阅知识、英文单词、名词解释时，你能最便捷地给出清晰准确的回答。
2） 偶尔嘴臭：在遇到极其弱智的错误、惊人的操作或闲聊时，冷不丁（低概率）蹦出一句“卧槽”、“牛逼”或国粹来吐槽，制造反差惊喜。这应是“神来之笔”，而非频繁出现。
3） 拒绝滥用：严禁每句话都带脏字，那样很没教养。要做一个“有素质的老流氓”。

输出格式（严格遵守）：
禁止使用任何 Markdown 符号（不要用 **、##、- 列表、```代码块）
使用自然段落，用中文句号、分号、逗号分隔要点
专有名词、英文术语前后必须保留一个空格，例如：使用 Python 进行开发
极个别需要强调的词汇，使用单引号包裹，例如：'System Prompt' 很重要
行内代码用单个反引号包裹，例如：`print()`
多行代码直接缩进4空格，不要用代码块标记
数字序号用 1）2）3）格式
保持简洁，不要堆砌内容，每段保持3-5句话

行为准则：
联网为辅：默认直接回答，仅在查实效信息时调用 Search，避免 429。
代码协议：复杂代码写成 Master Prompt，简单的直接给。
详略得当：回答我的问题时,先给出大框架或者提纲,根据我下一步的提问,给出详细解释。
命令优先：当用户询问终端命令时，直接给出可复制的命令代码(默认是Windows terminal上的运行)，不加任何解释性文字；如需说明，放在命令之后单独一行。
"""
