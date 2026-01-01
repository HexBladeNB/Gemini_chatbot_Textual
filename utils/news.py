"""
新闻获取器 - 带 AI 中文摘要
- 获取 HackerNews 热门新闻
- 用 Gemini Flash 生成中文摘要
- 文件缓存 (10分钟有效，避免频繁调用)
"""
import urllib.request
import json
import time
from pathlib import Path

# 缓存配置
CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_FILE = CACHE_DIR / "news_cache.json"
CACHE_TTL = 10 * 60  # 10分钟


class NewsFetcher:
    def __init__(self, cache_ttl=600):
        self.cache_ttl = cache_ttl
        self._current_index = 0
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_cache(self):
        """加载文件缓存"""
        if not CACHE_FILE.exists():
            return None
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if time.time() - data.get('timestamp', 0) > CACHE_TTL:
                return None
            return data.get('news', [])
        except:
            return None
    
    def _save_cache(self, news_list):
        """保存文件缓存"""
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': time.time(),
                    'news': news_list
                }, f, ensure_ascii=False)
        except:
            pass
    
    def _fetch_hn_stories(self, limit=3):
        """获取 HackerNews 原始新闻"""
        try:
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            req = urllib.request.Request(url, headers={'User-Agent': 'Python-CLI'})
            with urllib.request.urlopen(req, timeout=5) as response:
                ids = json.loads(response.read().decode())[:limit]
            
            stories = []
            for item_id in ids:
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
                with urllib.request.urlopen(item_url, timeout=3) as resp:
                    item = json.loads(resp.read().decode())
                    stories.append({
                        "title": item.get('title', 'Unknown'),
                        "url": item.get('url', ''),
                        "score": item.get('score', 0),
                        "summary": ""  # 待 AI 填充
                    })
            return stories
        except Exception:
            return []
    
    def _generate_summaries(self, stories):
        """用 Gemini Flash 生成中文摘要"""
        try:
            from core.client import get_client
            client = get_client()
            
            # 批量筛选+生成简介 (一次请求)
            titles = [f"{i+1}. {s['title']}" for i, s in enumerate(stories)]
            prompt = (
                "你是科技新闻编辑。从以下 Hacker News 标题中，选出最符合【AI/大模型/游戏/极客/编程】领域的3条。\n"
                "对每条用中文写一句话简介（50字内），让读者理解核心内容。\n"
                "格式：序号|中文简介（只返回3行，不要其他内容）\n\n"
                + "\n".join(titles)
            )
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            # 解析结果 (格式: "序号|中文简介")
            lines = response.text.strip().split('\n')
            filtered_stories = []
            for line in lines[:3]:  # 最多取3条
                line = line.strip()
                if '|' in line:
                    parts = line.split('|', 1)
                    try:
                        idx = int(parts[0].strip().rstrip('.')) - 1
                        summary = parts[1].strip()
                        if 0 <= idx < len(stories):
                            story = stories[idx].copy()
                            story['summary'] = summary
                            filtered_stories.append(story)
                    except (ValueError, IndexError):
                        pass
            
            # 如果筛选失败，返回原始前3条
            if filtered_stories:
                return filtered_stories
            else:
                for story in stories[:3]:
                    story['summary'] = story['title']
                return stories[:3]
                    
        except Exception:
            # AI 失败时保留原标题
            for story in stories[:3]:
                story['summary'] = story['title']
            return stories[:3]
    
    def get_top_stories(self, limit=3):
        """获取新闻 (优先使用缓存)"""
        # 1. 尝试读取缓存
        cached = self._load_cache()
        if cached:
            return cached
        
        # 2. 获取更多新闻供 AI 筛选 (获取10条，筛选出3条)
        stories = self._fetch_hn_stories(limit=10)
        if not stories:
            return []
        
        # 3. AI 生成中文摘要
        stories = self._generate_summaries(stories)
        
        # 4. 保存缓存
        self._save_cache(stories)
        
        return stories
    
    def get_ticker(self):
        """获取一条轮播新闻"""
        stories = self.get_top_stories(limit=3)
        if not stories:
            return "📰 暂无最新资讯"
        
        story = stories[self._current_index % len(stories)]
        self._current_index += 1
        
        # 优先显示中文摘要
        display = story.get('summary') or story['title']
        return f"[bright_cyan]{display}[/] [yellow](🔥{story['score']})[/]"


# 全局单例
news_fetcher = NewsFetcher()
