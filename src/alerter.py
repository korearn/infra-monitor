from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from datetime import datetime
from pathlib import Path

console = Console()

ALERTS_DIR = Path(__file__).parent.parent / "data" / "alerts"

def print_metrics_live(metrics) -> None:
    """
    Muestra las métricas actuales en la terminal de forma compacta.
    Se llama en cada ciclo del loop - diseñado para ser rápido y no saturar la salida.
    """
    cpu_color   = "red" if metrics.cpu_percent    >= 80 else "green"
    mem_color   = "red" if metrics.memory_percent >= 85 else "green"
    disk_color  = "red" if metrics.disk_percent   >= 90 else "green"

    timestamp = metrics.timestamp.strftime("%H:%M:%S")

    console.print(
        f"[dim]{timestamp}[/dim] | "
        f"CPU: [{cpu_color}]{metrics.cpu_percent:5.1f}%[/{cpu_color}] | "
        f"RAM: [{mem_color}]{metrics.memory_percent:5.1f}%[/{mem_color}] | "
        f"[dim]({metrics.memory_used_gb}GB/{metrics.memory_total_gb}GB)[/dim] | "
        f"DISK: [{disk_color}]{metrics.disk_percent:5.1f}%[/{disk_color}]"
    )

def print_alert(alert: dict) -> None:
    """
    Muestra una alerta detallada en la terminal utilizando Rich.
    Se llama cuando se detecta una anomalía que supera los umbrales definidos.
    """
    level   = alert["level"]
    border  = "red" if level == "CRITICAL" else "yellow"
    icon    = "🔴" if level == "CRITICAL" else "⚠️"

    title = f"{icon} {level} - {alert['metric'].upper()} al {alert['value']}%"

    content = (
        f"[bold]Threshold superado:[/bold] {alert['threshold']}%\n\n"
        f"[bold]Diagnóstico IA:[/bold]\n{alert['diagnosis']}"
    )

    console.print(Panel(content, title=title, border_style=border))

def print_alerts_history(alerts: list) -> None:
    """Muestra el historial de alertas recientes en formato tabla."""
    if not alerts:
        console.print("[green]Sin alertas recientes.[/green]")
        return

    table = Table(title="Alertas Recientes", show_lines=True, box=box.ROUNDED)
    table.add_column("Timestamp", style="cyan")
    table.add_column("Nivel",     style="red")
    table.add_column("Métrica",   style="yellow")
    table.add_column("Valor",     justify="right")
    table.add_column("Threshold", justify="right")
    
    for alert in alerts:
        table.add_row(
            alert['timestamp'],
            alert['level'],
            alert['metric'].upper(),
            f"{alert['value']}%",
            f"{alert['threshold']}%"
        )

    console.print(table)

def export_alert(alert: dict) -> None:
    """
    Exporta la alerta a archivo de texto con timestamp.
    En producción, se podría enviar a un sistema de alertas o base de datos.
    """
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename  = ALERTS_DIR / f"alert_{alert['metric']}_{timestamp}.txt"

    content = (
        f"ALERTA DE INFRAESTRUCTURA\n"
        f"{'='*50}\n"
        f"Timestamp: {datetime.utcnow().isoformat()}\n"
        f"Nivel:     {alert['level']}\n"
        f"Métrica:   {alert['metric'].upper()}\n"
        f"Valor:     {alert['value']}%\n"
        f"Threshold: {alert['threshold']}%\n"
        f"\nDiagnóstico IA:\n{alert['diagnosis']}\n"
    )

    filename.write_text(content, encoding="utf-8")