import datetime
import hashlib
import random

class FortuneTeller:
    def __init__(self, birthday="1986-03-16"):
        self.birthday = birthday
        # 双鱼座 (3.16)
        self.sign = "双鱼座"
        
        # 混合文案库 (极客 + 生活)
        self.activities_good = [
            # 极客篇
            "重构代码", "学习新库", "提交PR", "写技术博客", "可以试试 1.5 Flash",
            # 生活篇
            "早睡早起", "运动健身", "和朋友聚餐", "看一部好电影", "整理房间",
            "给家人打电话", "尝试新餐厅", "读一本好书", "户外散步", "冥想放松",
            "做一顿美食", "购物犒劳自己", "学习新技能", "约会", "旅行规划"
        ]
        
        self.activities_bad = [
            # 极客篇
            "周五上线", "相信产品经理", "写正则表达式", "改祖传代码",
            # 生活篇
            "熬夜", "暴饮暴食", "冲动消费", "和人争吵", "拖延重要事项",
            "忽略身体信号", "过度加班", "刷短视频超过1小时", "喝太多咖啡",
            "忘记约会", "忽视家人", "信用卡分期", "酒后开车", "空腹喝酒"
        ]
        
        self.colors = [
            "樱花粉", "天空蓝", "薄荷绿", "柠檬黄", "珊瑚橙", 
            "薰衣草紫", "奶茶棕", "雾霾蓝", "抹茶绿", "蜜桃粉",
            "极客蓝", "终端绿", "深空灰", "月光白", "暖阳金"
        ]
        
    def _get_seed(self):
        """根据日期和生日生成唯一的每日种子"""
        today = datetime.date.today().isoformat()
        seed_str = f"{self.birthday}-{today}-geek"
        # 使用 sha256 生成稳定的整数种子
        hash_val = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
        return hash_val

    def get_daily_fortune(self):
        """生成每日运势"""
        seed = self._get_seed()
        rng = random.Random(seed)
        
        # 1. 综合运势 (1-5级)
        stars = rng.randint(3, 5) 
        # 简洁文字描述
        levels = {5: "🌟大吉🌟", 4: "✨小吉", 3: "💫平稳", 2: "⚡小凶", 1: "💥大凶"}
        star_str = levels.get(stars, "💫")
        
        # 2. 宜/忌
        # 随机取样，不重复
        good = rng.sample(self.activities_good, 2)
        bad = rng.sample(self.activities_bad, 2)
        
        # 3. 极客指数
        geek_index = rng.randint(60, 100)
        
        # 4. 幸运元素
        color = rng.choice(self.colors)
        number = rng.randint(0, 1024)
        
        return {
            "sign": self.sign,
            "stars": star_str,
            "good": f"{good[0]}、{good[1]}",
            "bad": f"{bad[0]}、{bad[1]}",
            "color": color,
            "number": number,
            "index": geek_index
        }
    
    def get_display_text(self):
        """获取展示文本"""
        f = self.get_daily_fortune()
        return (
            f"[bold magenta]🔮 {f['sign']}运势:[/] [bold yellow]{f['stars']}[/]   "
            f"[bold green]👍 宜: {f['good']}[/]   [bold red]👎 忌: {f['bad']}[/]   "
            f"[bold blue]🍀 幸运色: {f['color']}[/]"
        )

# 全局实例
fortune_teller = FortuneTeller()
