import psutil
from datetime import datetime
from dataclasses import dataclass

@dataclass
class SystemMetrics:
    """
    Métricas del sistema.
    dataclass genera automáticamente el constructor y otros métodos útiles.
    """
    timestamp:       datetime 
    cpu_percent:     float  # % de uso de CPU (0-100)
    memory_percent:  float  # % de uso de RAM (0-100)
    memory_used_gb:  float  # % de RAM usada
    memory_total_gb: float  # GB de RAM total
    disk_percent:    float  # % de uso de disco (0-100)
    disk_used_gb:    float  # GB de disco usado
    disk_total_gb:   float  # GB de disco total
    net_bytes_sent:  int    # Bytes enviados por la red
    net_bytes_recv:  int    # Bytes recibidos desde el boot
    top_processes:   list   # Lista de los procesos más consumidores de recursos

def collect_metrics() -> SystemMetrics:
    """
    Recopila las métricas del sistema utilizando psutil.
    Mide CPU durante 1 segundo para obtener un valor más preciso.
    """
    cpu     = psutil.cpu_percent(interval=1)  # Mide el uso de CPU durante 1 segundo
    memory  = psutil.virtual_memory()
    disk    = psutil.disk_usage('/')
    net     = psutil.net_io_counters()

    # Top 5 procesos por uso de CPU
    # Llamamos cpu_percent() para cada proceso para obtener su uso de CPU
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            if info['cpu_percent'] is not None:
                processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Si el proceso ya no existe o no tenemos permiso para acceder a él, se ignora
            pass

    top_processes = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:5]

    return SystemMetrics(
        timestamp=datetime.utcnow(),
        cpu_percent=cpu,
        memory_percent=memory.percent,
        memory_used_gb=round(memory.used / (1024 ** 3), 2),
        memory_total_gb=round(memory.total / (1024 ** 3), 2),
        disk_percent=disk.percent,
        disk_used_gb=round(disk.used / (1024 ** 3), 2),
        disk_total_gb=round(disk.total / (1024 ** 3), 2),
        net_bytes_sent=net.bytes_sent,
        net_bytes_recv=net.bytes_recv,
        top_processes=top_processes
    )

def format_metrics_summary(metrics: SystemMetrics) -> str:
    """
    Formatea un resumen de las métricas del sistema para su visualización.
    """
    top_procs = "\n".join([f"  - {p['name']} (PID {p['pid']}): CPU {p['cpu_percent']}% | MEM {p['memory_percent']:.1f}%" for p in metrics.top_processes])
    return f"""Sistema monitoreado: {metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC

CPU: {metrics.cpu_percent}% usado
Memoria: {metrics.memory_percent}% usado ({metrics.memory_used_gb}GB / {metrics.memory_total_gb}GB)
Disco: {metrics.disk_percent}% usado ({metrics.disk_used_gb}GB / {metrics.disk_total_gb}GB)
Red: ↑ {metrics.net_bytes_sent / (1024 ** 2):.1f}MB enviados | ↓ {metrics.net_bytes_recv / (1024 ** 2):.1f}MB recibidos

top procesos por CPU:
{top_procs if top_procs else '  No se encontraron procesos activos.'}"""