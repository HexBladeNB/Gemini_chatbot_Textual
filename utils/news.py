"""
新闻获取器 - Google News RSS + AI 翻译
- 使用 Google News RSS (免费无需 Key)
- Gemini 批量翻译 (省流)
- 本地缓存 (30分钟有效)
- 支持滚动效果
"""
import urllib.request
import json
import time
import re
from pathlib import Path
from html import unescape

# 缓存配置
CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_FILE = CACHE_DIR / "news_cache.json"
CACHE_TTL = 30 * 60  # 30分钟

# Google News RSS (中国科技新闻)
GOOGLE_NEWS_RSS = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"


class NewsFetcher:
    """新闻获取器 (Google News + AI 翻译)"""
    
    def __init__(self):
        self._news_list = []
        self._current_index = 0
        self._scroll_offset = 0
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_cache(self) -> list | None:
        """加载缓存"""
        if not CACHE_FILE.exists():
            return None
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if time.time() - data.get('timestamp', 0) > CACHE_TTL:
                return None
            return data.get('news', [])
        except (json.JSONDecodeError, OSError, KeyError) as e:
            return None
    
    def _save_cache(self, news_list: list):
        """保存缓存"""
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': time.time(),
                    'news': news_list
                }, f, ensure_ascii=False)
        except (OSError, IOError) as e:
            pass  # 缓存保存失败不影响主流程
    
    def _fetch_google_news(self, limit: int = 10) -> list:
        """从 Google News RSS 获取新闻"""
        try:
            import feedparser
        except ImportError:
            # 如果没有 feedparser，使用简单解析
            return self._fetch_google_news_simple(limit)
        
        try:
            feed = feedparser.parse(GOOGLE_NEWS_RSS)
            stories = []
            for entry in feed.entries[:limit]:
                title = unescape(entry.title)
                # 移除来源标识 (如 " - TechCrunch")
                title = re.sub(r'\s*-\s*[^-]+$', '', title)
                stories.append({
                    'title': title,
                    'source': entry.get('source', {}).get('title', 'Google News'),
                    'link': entry.link,
                    'summary': '',  # 待翻译
                })
            return stories
        except Exception:
            return []
    
    def _fetch_google_news_simple(self, limit: int = 10) -> list:
        """简单 RSS 解析 (无 feedparser 时)"""
        try:
            req = urllib.request.Request(
                GOOGLE_NEWS_RSS,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode('utf-8')
            
            # 简单正则提取
            items = re.findall(r'<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?</item>', content, re.DOTALL)
            stories = []
            for title, link in items[:limit]:
                title = unescape(re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title))
                title = re.sub(r'\s*-\s*[^-]+$', '', title)
                stories.append({
                    'title': title,
                    'source': 'Google News',
                    'link': link,
                    'summary': '',
                })
            return stories
        except (urllib.error.URLError, ValueError) as e:
            return []
    
    def _translate_batch(self, stories: list) -> list:
        """批量翻译新闻标题 (省流: 一次 API 调用)"""
        if not stories:
            return stories
        
        try:
            from core.client import get_client
            client = get_client()
            
            # 构建批量翻译请求
            titles = [f"{i+1}. {s['title']}" for i, s in enumerate(stories)]
            prompt = (
                "将以下英文科技新闻标题翻译成简洁的中文（每条不超过50字）。\n"
                "格式：序号|中文翻译\n"
                "只返回翻译结果，不要其他内容。\n\n"
                + "\n".join(titles)
            )
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            # 解析结果
            lines = response.text.strip().split('\n')
            for line in lines:
                if '|' in line:
                    parts = line.split('|', 1)
                    try:
                        idx = int(parts[0].strip().rstrip('.')) - 1
                        translation = parts[1].strip()[:50]
                        if 0 <= idx < len(stories):
                            stories[idx]['summary'] = translation
                    except (ValueError, IndexError):
                        pass  # 解析失败时跳过此条
            
            # 未翻译的保留原标题
            for s in stories:
                if not s['summary']:
                    s['summary'] = s['title'][:50]
            
            return stories
            
        except Exception:
            # 翻译失败，使用原标题
            for s in stories:
                s['summary'] = s['title'][:50]
            return stories
    
    def get_top_stories(self, limit: int = 5) -> list:
        """获取新闻 (优先使用缓存)"""
        # 1. 尝试缓存
        cached = self._load_cache()
        if cached:
            self._news_list = cached
            return cached
        
        # 2. 抓取新闻
        stories = self._fetch_google_news(limit=limit * 2)  # 多抓一些
        if not stories:
            return []
        
        # 3. 批量翻译 (省流)
        stories = self._translate_batch(stories[:limit])
        
        # 4. 保存缓存
        self._save_cache(stories)
        self._news_list = stories
        
        return stories
    
    def get_ticker(self) -> str:
        """获取一条轮播新闻"""
        if not self._news_list:
            self.get_top_stories()
        
        if not self._news_list:
            return "📰 暂无最新资讯"
        
        story = self._news_list[self._current_index % len(self._news_list)]
        self._current_index += 1
        
        # 优先显示翻译
        display = story.get('summary') or story['title'][:50]
        source = story.get('source', '')[:10]
        return f"📰 {display} [{source}]"
    
    def _display_width(self, text: str) -> int:
        """计算字符串的显示宽度（中文算2，英文算1）"""
        width = 0
        for char in text:
            # 中日韩字符占2格
            if '\u4e00' <= char <= '\u9fff' or \
               '\u3400' <= char <= '\u4dbf' or \
               '\uf900' <= char <= '\ufaff' or \
               '\U00020000' <= char <= '\U0002a6df':
                width += 2
            else:
                width += 1
        return width
    
    def _truncate_to_width(self, text: str, max_width: int) -> str:
        """按显示宽度截断字符串"""
        result = []
        current_width = 0
        for char in text:
            char_width = 2 if ('\u4e00' <= char <= '\u9fff' or 
                              '\u3400' <= char <= '\u4dbf' or
                              '\uf900' <= char <= '\ufaff') else 1
            if current_width + char_width > max_width:
                break
            result.append(char)
            current_width += char_width
        # 用空格填充到精确宽度
        while current_width < max_width:
            result.append(' ')
            current_width += 1
        return ''.join(result)

    def get_scrolling_text(self, width: int = 60) -> str:
        """
        获取新闻文本 (翻页式轮播，每4秒切换一条)
        """
        if not self._news_list:
            self.get_top_stories()
        
        prefix = "📰 "
        prefix_width = 3  # emoji(2) + 空格(1)
        display_width = max(10, width - prefix_width)
        
        if not self._news_list:
            return self._truncate_to_width(prefix + "新闻加载中...", width)
        
        # 检查是否需要切换到下一条 (每4秒切换)
        current_time = time.time()
        if not hasattr(self, '_last_flip_time'):
            self._last_flip_time = current_time
            self._flip_index = 0
        
        if current_time - self._last_flip_time >= 4.0:
            self._last_flip_time = current_time
            self._flip_index = (self._flip_index + 1) % len(self._news_list)
        
        # 获取当前新闻
        story = self._news_list[self._flip_index]
        headline = story.get('summary') or story['title'][:50]
        source = story.get('source', '')[:8]
        
        # 格式: 📰 标题 [来源]
        text = f"{headline} [{source}]"
        
        return prefix + self._truncate_to_width(text, display_width)


# 全局单例
news_fetcher = NewsFetcher()
