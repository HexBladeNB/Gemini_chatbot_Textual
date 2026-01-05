"""
天气获取器 - 双源版
- 优先: Open-Meteo (免费、无需Key)
- 备用: 和风天气 (需要配置)
- 本地缓存 (15分钟有效)
"""
import os
import json
import time
import urllib.request
from pathlib import Path

# 缓存配置
CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_FILE = CACHE_DIR / "weather_cache.json"
CACHE_TTL = 15 * 60  # 15分钟

# 南宁坐标
NANNING_LAT = 22.82
NANNING_LON = 108.32

# Open-Meteo API (免费、无需 Key)
OPENMETEO_URL = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={NANNING_LAT}&longitude={NANNING_LON}"
    f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
    f"precipitation,weather_code,wind_speed_10m"
    f"&daily=weather_code,temperature_2m_max,temperature_2m_min,uv_index_max,"
    f"precipitation_probability_max,sunrise,sunset"
    f"&timezone=Asia%2FShanghai&forecast_days=2"
)

# WMO 天气代码映射
WMO_CODES = {
    0: "晴", 1: "晴", 2: "多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "小雨", 53: "中雨", 55: "大雨",
    56: "冻雨", 57: "冻雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨", 67: "冻雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    77: "雪粒", 80: "阵雨", 81: "阵雨", 82: "暴雨",
    85: "阵雪", 86: "阵雪",
    95: "雷暴", 96: "雷暴冰雹", 99: "雷暴冰雹"
}


class WeatherFetcher:
    """天气获取器 (Open-Meteo)"""
    
    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _request(self) -> dict:
        """发起 API 请求 (绕过代理)"""
        no_proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(no_proxy_handler)
        
        req = urllib.request.Request(OPENMETEO_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=8) as resp:
            return json.loads(resp.read().decode('utf-8'))
    
    def _load_cache(self) -> dict | None:
        """加载缓存"""
        if not CACHE_FILE.exists():
            return None
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if time.time() - data.get('timestamp', 0) > CACHE_TTL:
                return None
            return data
        except (json.JSONDecodeError, OSError, KeyError):
            return None
    
    def _save_cache(self, today: str, tomorrow: str):
        """保存缓存"""
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': time.time(),
                    'today': today,
                    'tomorrow': tomorrow
                }, f, ensure_ascii=False)
        except (OSError, IOError):
            pass  # 缓存保存失败不影响主流程
    
    def _get_weather_text(self, code: int) -> str:
        """WMO 代码转中文"""
        return WMO_CODES.get(code, "未知")
    
    def fetch(self) -> tuple[str, str]:
        """获取天气信息 (今日+明日)"""
        try:
            data = self._request()
            
            # 实时天气
            cur = data['current']
            temp = cur['temperature_2m']
            feels = cur['apparent_temperature']
            humid = cur['relative_humidity_2m']
            wind = cur['wind_speed_10m']
            precip = cur['precipitation']
            code = cur['weather_code']
            text = self._get_weather_text(code)
            
            today_str = (
                f"[bold cyan]📍 南宁:[/] [yellow]{text}[/] [bold red]{temp:.0f}°C[/] | "
                f"[dim]🌡️ 体感[/] [red]{feels:.0f}°C[/] | "
                f"[dim]💧 湿度[/] [blue]{humid}%[/] | "
                f"[dim]🌬️ 风速[/] [green]{wind:.0f}km/h[/] | "
                f"[dim]☂️ 降水[/] [cyan]{precip}mm[/]"
            )
            
            # 明日预报 (daily[1])
            daily = data['daily']
            tom_date = daily['time'][1]
            tom_code = daily['weather_code'][1]
            tom_text = self._get_weather_text(tom_code)
            tom_min = daily['temperature_2m_min'][1]
            tom_max = daily['temperature_2m_max'][1]
            tom_uv = daily['uv_index_max'][1]
            tom_rain = daily.get('precipitation_probability_max', [0, 0])[1]
            tom_sunrise = daily.get('sunrise', ['', ''])[1][-5:] if daily.get('sunrise') else ''
            tom_sunset = daily.get('sunset', ['', ''])[1][-5:] if daily.get('sunset') else ''
            
            tom_str = (
                f"[bold cyan]明日[/] [dim]({tom_date}):[/] [yellow]{tom_text}[/] "
                f"[blue]{tom_min:.0f}[/]~[red]{tom_max:.0f}°C[/] | "
                f"[dim]☔ 降水概率[/] [cyan]{tom_rain}%[/] | "
                f"[dim]☀️ UV[/] [magenta]{tom_uv:.0f}[/] | "
                f"[dim]🌅[/] {tom_sunrise} [dim]🌇[/] {tom_sunset}"
            )
            
            # 缓存
            self._save_cache(today_str, tom_str)
            
            return today_str, tom_str
            
        except Exception as e:
            # 尝试读取缓存
            cache = self._load_cache()
            if cache:
                return f"{cache['today']} [dim](缓存)[/dim]", cache['tomorrow']
            return f"⚠️ 天气服务异常 ({str(e)})", "明日数据不可用"


# 全局实例
weather_fetcher = WeatherFetcher()
