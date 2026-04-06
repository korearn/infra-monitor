import time
import sys
import signal
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.rule import Rule

sys.path.insert(0, str(Path(__file__).parent))

from collector import collect_metrics
from analyzer import analyze
from alerter import print_metrics_live, print_alert, export_alert
from database import init_db, save_metrics, save_alert

load_dotenv()

console = Console()
INTERVAL = int(os.getenv("MONITOR_INTERVAL_SECONDS", 30))

# Variable global para controlar el loop principal
# Cuando recibimos señal de apagado se pone en False
running = True

def handle_shutdown(signum, frame):
    """Manejador de señales para una terminación limpia del programa."""
    global running
    running = False
    console.print("\n[yellow]Apagando monitor...[/yellow]")

def print_header():
    console.print(Rule("[bold blue]INFRA MONITOR - Sistema de Monitoreo con IA[/bold blue]"))
    console.print(f"[dim]Intervalo: {INTERVAL}s  | Iniciado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC[/dim]\n")

def main():
    # Registrar handler para apagado limpio
    # signal.sinal conecta una señal del SO con nuestra función de manejo
    signal.signal(signal.SIGTERM, handle_shutdown)  # Señal de terminación
    signal.signal(signal.SIGINT, handle_shutdown)

    print_header()

    # Incializar base de datos
    console.print("[bold]Inicializando base de datos...[/bold]")
    init_db()
    console.print("[green]✓[/green] Base de datos lista\n")
    console.print("[dim]Monitoreando sistema - Ctrl+C para salir[/dim]\n")

    cycle = 0

    while running:
        cycle += 1

        try:
            # 1. Recolectar métricas del sistema
            metrics = collect_metrics()

            # 2. Mostrar en terminal
            print_metrics_live(metrics)

            # 3. Guardar métricas en la base de datos
            save_metrics(metrics)

            # 4. Analizar métricas para detectar anomalías
            alerts = []
            alerts = analyze(metrics)

            # 5. Procesar alertas si las hay
            for alert in alerts:
                print_alert(alert)
                export_alert(alert)
                save_alert(
                    level=alert['level'],
                    metric=alert['metric'],
                    value=alert['value'],
                    threshold=alert['threshold'],
                    diagnosis=alert['diagnosis']
                )
            
            # 6. Separador visual cada 10 ciclos para legibilidad
            if cycle % 10 == 0:
                total = cycle * INTERVAL
                console.print(
                    f"[dim]-- {cycle} ciclos completados "
                    f"({total}s de monitoreo) --[/dim]"
                )

        except Exception as e:
            import traceback
            traceback.print_exc()
            # El daemon nunca debe caerse por un error en un ciclo
            console.print(f"[red]Error en ciclo {cycle}:[/red] {e}")

            # Esperar el intervalo definido antes de la siguiente recolección
        for _ in range(INTERVAL):
            if not running:
                break
            time.sleep(1)

    console.print("[green]Monitor detenido correctamente.[/green]")

if __name__ == "__main__":
    main()