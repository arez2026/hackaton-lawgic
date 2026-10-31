"""Uso: python -m lawgic_revisor <contrato> [--salida carpeta] [--modelo id]"""
import argparse
import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from .revisor import MODELO_POR_DEFECTO, guardar, revisar

consola = Console()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="lawgic_revisor", description="Opinión legal de un contrato con consulta de leyes en tiempo real.")
    p.add_argument("contrato", type=Path, help="Ruta al contrato (.md, .txt, .pdf, .docx)")
    p.add_argument("--salida", type=Path, default=None, help="Carpeta de salida (por defecto salida/<nombre>)")
    p.add_argument("--modelo", default=MODELO_POR_DEFECTO)
    p.add_argument("--sin-render", action="store_true", help="No imprimir la opinión en consola")
    a = p.parse_args(argv)

    salida = a.salida or Path("salida") / a.contrato.stem
    consola.print(Panel.fit(f"[bold]Lawgic Revisor[/bold]\nContrato: {a.contrato}\nModelo: {a.modelo}", border_style="blue"))
    consola.print("[dim]Consultando fuentes legales en tiempo real…[/dim]")

    def en_vivo(evento: str):
        consola.print(f"  [cyan]•[/cyan] {evento}")

    try:
        r = asyncio.run(revisar(a.contrato, modelo=a.modelo, en_vivo=en_vivo))
    except Exception as e:  # noqa: BLE001
        consola.print(f"[red]Error:[/red] {e}")
        return 1

    ruta_opinion, ruta_fuentes = guardar(r, salida)

    t = Table(title="Bitácora de consultas", show_lines=False)
    t.add_column("#", justify="right"); t.add_column("Hora"); t.add_column("Herramienta"); t.add_column("Consulta")
    for c in r.consultas:
        t.add_row(str(c.orden), c.hora[11:19], c.herramienta, c.consulta[:90])
    consola.print(t)
    if not a.sin_render:
        consola.print(Markdown(r.opinion_md))
    consola.print(Panel.fit(
        f"Opinión: [bold]{ruta_opinion}[/bold]\nFuentes: [bold]{ruta_fuentes}[/bold]\n"
        f"{len(r.consultas)} consultas web · {r.duracion_s} s · {r.turnos} turnos",
        border_style="green"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
