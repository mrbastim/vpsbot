import psutil

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_ram_usage():
    ram = psutil.virtual_memory()
    return ram.percent

def get_disk_usage():
    disk_usage_info = []
    for part in psutil.disk_partitions(all=False):
        usage = psutil.disk_usage(part.mountpoint)
        disk_usage_info.append({
            'device': part.device,
            'total': usage.total,
            'used': usage.used,
            'free': usage.free,
            'percent': usage.percent,
            'fstype': part.fstype,
            'mountpoint': part.mountpoint
        })
    return disk_usage_info

def format_disk_usage(disk_usage):
    output = []
    for usage in disk_usage:
        output.append(f"{usage['device']}: Total: {usage['total']} Used: {usage['used']} Free: {usage['free']} Usage: {usage['percent']}%")
    return "\n".join(output)