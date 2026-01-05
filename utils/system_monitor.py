"""
系统监控模块 - CPU/内存/GPU/磁盘/网络实时监测
支持显示具体型号和多磁盘轮播
"""
import psutil
import time
import platform
from dataclasses import dataclass, field


@dataclass
class SystemStats:
    """系统状态数据"""
    # CPU
    cpu_percent: float = 0.0
    cpu_freq_ghz: float = 0.0
    cpu_name: str = "CPU"
    
    # 内存
    memory_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    
    # GPU (NVIDIA)
    gpu_percent: float = 0.0
    gpu_memory_percent: float = 0.0
    gpu_temp: float = 0.0
    gpu_name: str = ""
    
    # 当前显示的磁盘
    disk_name: str = "C:"
    disk_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    
    # 网络
    net_sent_speed: float = 0.0
    net_recv_speed: float = 0.0


class SystemMonitor:
    """系统资源监控器"""
    
    def __init__(self):
        self._last_net_io = psutil.net_io_counters()
        self._last_time = time.time()
        self._gpu_available = False
        self._cpu_name = self._get_cpu_name()
        self._disk_list = self._get_disk_list()
        self._disk_index = 0
        self._check_gpu()
    
    def _get_cpu_name(self) -> str:
        """获取 CPU 型号简称"""
        try:
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(
                    ["wmic", "cpu", "get", "name"],
                    capture_output=True, text=True, timeout=5
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    full_name = lines[1].strip()
                    # 提取简称：如 "Intel(R) Core(TM) i7-8700K" -> "i7-8700K"
                    if "i7-" in full_name:
                        start = full_name.find("i7-")
                        return full_name[start:start+10].split()[0]
                    elif "i9-" in full_name:
                        start = full_name.find("i9-")
                        return full_name[start:start+10].split()[0]
                    elif "i5-" in full_name:
                        start = full_name.find("i5-")
                        return full_name[start:start+10].split()[0]
                    elif "Ryzen" in full_name:
                        # AMD Ryzen 处理
                        parts = full_name.split()
                        for i, p in enumerate(parts):
                            if p == "Ryzen" and i + 2 < len(parts):
                                return f"R{parts[i+1]} {parts[i+2]}"
                    return full_name[:15]
            return "CPU"
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError, ValueError):
            return "CPU"
    
    def _get_disk_list(self) -> list:
        """获取所有磁盘分区"""
        disks = []
        try:
            for part in psutil.disk_partitions():
                if 'cdrom' in part.opts or part.fstype == '':
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disks.append({
                        'name': part.device.replace('\\', ''),  # C:
                        'mountpoint': part.mountpoint,
                        'total_gb': usage.total / (1024 ** 3),
                    })
                except (OSError, PermissionError):
                    pass  # 跳过无权限访问的磁盘
        except (OSError, PermissionError):
            pass
        return disks if disks else [{'name': 'C:', 'mountpoint': 'C:\\', 'total_gb': 0}]
    
    def _check_gpu(self):
        """检查 GPU 是否可用"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            self._gpu_available = len(gpus) > 0
        except (ImportError, Exception):
            self._gpu_available = False
    
    def get_stats(self) -> SystemStats:
        """获取当前系统状态"""
        current_time = time.time()
        time_delta = max(0.1, current_time - self._last_time)
        
        # === CPU ===
        cpu_percent = psutil.cpu_percent(interval=None)
        try:
            cpu_freq = psutil.cpu_freq()
            cpu_freq_ghz = cpu_freq.current / 1000 if cpu_freq else 0
        except (OSError, AttributeError):
            cpu_freq_ghz = 0
        
        # === 内存 ===
        mem = psutil.virtual_memory()
        
        # === 磁盘（轮播） ===
        if self._disk_list:
            disk_info = self._disk_list[self._disk_index % len(self._disk_list)]
            try:
                usage = psutil.disk_usage(disk_info['mountpoint'])
                disk_name = disk_info['name']
                disk_percent = usage.percent
                disk_used_gb = usage.used / (1024 ** 3)
                disk_total_gb = usage.total / (1024 ** 3)
            except (OSError, PermissionError):
                disk_name = "C:"
                disk_percent = 0
                disk_used_gb = 0
                disk_total_gb = 0
        else:
            disk_name = "C:"
            disk_percent = 0
            disk_used_gb = 0
            disk_total_gb = 0
        
        # === 网络 ===
        current_net = psutil.net_io_counters()
        net_sent_speed = (current_net.bytes_sent - self._last_net_io.bytes_sent) / time_delta / 1024
        net_recv_speed = (current_net.bytes_recv - self._last_net_io.bytes_recv) / time_delta / 1024
        self._last_net_io = current_net
        
        # === GPU (NVIDIA) ===
        gpu_percent = 0.0
        gpu_memory_percent = 0.0
        gpu_temp = 0.0
        gpu_name = ""
        
        if self._gpu_available:
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_percent = gpu.load * 100
                    gpu_memory_percent = gpu.memoryUtil * 100
                    gpu_temp = gpu.temperature
                    # 简化 GPU 名称
                    name = gpu.name
                    if "RTX" in name:
                        gpu_name = "RTX" + name.split("RTX")[1].split()[0]
                    elif "GTX" in name:
                        gpu_name = "GTX" + name.split("GTX")[1].split()[0]
                    else:
                        gpu_name = name[:12]
            except (ImportError, Exception):
                pass  # GPU 读取失败不影响其他功能
        
        self._last_time = current_time
        
        return SystemStats(
            cpu_percent=cpu_percent,
            cpu_freq_ghz=cpu_freq_ghz,
            cpu_name=self._cpu_name,
            memory_percent=mem.percent,
            memory_used_gb=mem.used / (1024 ** 3),
            memory_total_gb=mem.total / (1024 ** 3),
            gpu_percent=gpu_percent,
            gpu_memory_percent=gpu_memory_percent,
            gpu_temp=gpu_temp,
            gpu_name=gpu_name,
            disk_name=disk_name,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb,
            net_sent_speed=net_sent_speed,
            net_recv_speed=net_recv_speed,
        )
    
    def rotate_disk(self):
        """切换到下一个磁盘"""
        if self._disk_list:
            self._disk_index = (self._disk_index + 1) % len(self._disk_list)
    
    @property
    def has_gpu(self) -> bool:
        """是否有 GPU"""
        return self._gpu_available
    
    @property
    def disk_count(self) -> int:
        """磁盘数量"""
        return len(self._disk_list)


# 全局实例
system_monitor = SystemMonitor()
