"""Motor: corre el agente, captura la bitácora de consultas web y escribe los entregables."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

from .extractor import extraer_texto
from .leyes import CATALOGO, servidor_leyes
from .prompt import SYSTEM_PROMPT, construir_instruccion

CDMX = ZoneInfo("America/Mexico_City")
MODELO_POR_DEFECTO = "claude-opus-5-5"
URL_RE = re.compile(r"https?://[^\s)\]>\"']+")


@dataclass
class Consulta:
    """Una consulta web hecha por el agente, con su hora exacta: la prueba de consulta en tiempo real."""
    orden: int
    herramienta: str            # LeyOficial | WebSearch | WebFetch
    hora: str                   # ISO 8601, hora de Ciudad de México
    consulta: str               # término buscado o URL leída
    tool_use_id: str
    urls_encontradas: list[str] = field(default_factory=list)
    extracto_resultado: str = ""
    error: bool = False


@dataclass
class Resultado:
    archivo: str
    modelo: str
    inicio: str
    fin: str
    duracion_s: float
    turnos: int
    costo_usd: float | None
    opinion_md: str
    consultas: list[Consulta]
    texto_crudo: str


def _ahora() -> datetime:
    return datetime.now(CDMX)


def _extraer_opinion(texto: str) -> str:
    m = re.search(r"<<<OPINION>>>(.*?)<<<FIN>>>", texto, re.S)
    return (m.group(1) if m else texto).strip()


def _resumir_resultado(contenido) -> tuple[str, list[str]]:
    if contenido is None:
        return "", []
    if isinstance(contenido, list):
        trozos = []
        for bloque in contenido:
            if isinstance(bloque, dict) and bloque.get("type") == "text":
                trozos.append(bloque.get("text", ""))
            else:
                trozos.append(json.dumps(bloque, ensure_ascii=False)[:2000])
        texto = "\n".join(trozos)
    else:
        texto = str(contenido)
    urls = []
    for u in URL_RE.findall(texto):
        u = u.rstrip(".,;")
        if u not in urls:
            urls.append(u)
    return texto[:600].replace("\n", " "), urls[:15]


async def revisar(ruta_contrato: Path, modelo: str = MODELO_POR_DEFECTO, en_vivo=None) -> Resultado:
    """Revisa el contrato. `en_vivo(evento: str)` recibe mensajes de progreso para la consola."""
    ruta_contrato = Path(ruta_contrato)
    texto = extraer_texto(ruta_contrato)
    inicio = _ahora()
    instruccion = construir_instruccion(texto, ruta_contrato.name, inicio.strftime("%Y-%m-%d %H:%M"))

    opciones = ClaudeAgentOptions(
        model=modelo,
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["WebSearch", "WebFetch", "mcp__leyes__consultar_ley"],
        mcp_servers={"leyes": servidor_leyes()},
        disallowed_tools=["Bash", "Read", "Write", "Edit", "Glob", "Grep", "Task", "NotebookEdit"],
        permission_mode="bypassPermissions",
        setting_sources=[],          # aislamiento: no carga CLAUDE.md ni settings locales
        max_turns=40,
    )

    consultas: list[Consulta] = []
    pendientes: dict[str, Consulta] = {}
    textos: list[str] = []
    turnos = 0
    costo = None

    async for mensaje in query(prompt=instruccion, options=opciones):
        if isinstance(mensaje, AssistantMessage):
            for bloque in mensaje.content:
                if isinstance(bloque, ToolUseBlock) and (bloque.name in {"WebSearch", "WebFetch"} or bloque.name.endswith("consultar_ley")):
                    if bloque.name.endswith("consultar_ley"):
                        nombre = "LeyOficial"
                        que = f"{bloque.input.get('ley', '?')} art. {bloque.input.get('articulo', '?')} (PDF oficial, Cámara de Diputados)"
                    else:
                        nombre = bloque.name
                        que = bloque.input.get("query") or bloque.input.get("url") or json.dumps(bloque.input, ensure_ascii=False)
                    c = Consulta(
                        orden=len(consultas) + 1,
                        herramienta=nombre,
                        hora=_ahora().isoformat(timespec="seconds"),
                        consulta=que,
                        tool_use_id=bloque.id,
                    )
                    consultas.append(c)
                    pendientes[bloque.id] = c
                    if en_vivo:
                        en_vivo(f"[{c.hora[11:19]}] {c.herramienta}: {que}")
                elif isinstance(bloque, TextBlock) and bloque.text.strip():
                    textos.append(bloque.text)
        elif isinstance(mensaje, UserMessage) and isinstance(mensaje.content, list):
            for bloque in mensaje.content:
                if isinstance(bloque, ToolResultBlock) and bloque.tool_use_id in pendientes:
                    c = pendientes.pop(bloque.tool_use_id)
                    c.extracto_resultado, c.urls_encontradas = _resumir_resultado(bloque.content)
                    c.error = bool(bloque.is_error)
        elif isinstance(mensaje, ResultMessage):
            turnos = mensaje.num_turns
            costo = getattr(mensaje, "total_cost_usd", None)

    fin = _ahora()
    crudo = "\n\n".join(textos)
    return Resultado(
        archivo=ruta_contrato.name,
        modelo=modelo,
        inicio=inicio.isoformat(timespec="seconds"),
        fin=fin.isoformat(timespec="seconds"),
        duracion_s=round((fin - inicio).total_seconds(), 1),
        turnos=turnos,
        costo_usd=costo,
        opinion_md=_extraer_opinion(crudo),
        consultas=consultas,
        texto_crudo=crudo,
    )


def _tabla_bitacora(consultas: list[Consulta]) -> str:
    filas = ["| # | Hora (CDMX) | Herramienta | Consulta | Fuentes devueltas |", "|---|---|---|---|---|"]
    for c in consultas:
        fuentes = "<br>".join(c.urls_encontradas[:4]) or ("error" if c.error else "—")
        filas.append(f"| {c.orden} | {c.hora[11:19]} | {c.herramienta} | {c.consulta.replace('|', '/')} | {fuentes} |")
    return "\n".join(filas)


def guardar(resultado: Resultado, carpeta_salida: Path) -> tuple[Path, Path]:
    carpeta_salida = Path(carpeta_salida)
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    ruta_opinion = carpeta_salida / "opinion.md"
    ruta_fuentes = carpeta_salida / "fuentes.json"

    encabezado = (
        f"# Opinión legal · {resultado.archivo}\n\n"
        f"- Generada: {resultado.inicio} → {resultado.fin} (hora de Ciudad de México), {resultado.duracion_s} s\n"
        f"- Modelo: `{resultado.modelo}` vía Claude Agent SDK, con las herramientas consultar_ley (PDF oficial), WebSearch y WebFetch\n"
        f"- Consultas web realizadas en esta sesión: **{len(resultado.consultas)}**\n\n"
        "> Documento generado por un sistema automatizado con fines académicos. No sustituye la asesoría de un abogado.\n\n---\n\n"
    )
    bitacora = (
        "\n\n---\n\n## Bitácora de consulta en tiempo real\n\n"
        "Cada fila es una llamada real a la web hecha por el agente durante la revisión, con la hora exacta en que ocurrió. "
        "El detalle completo está en `fuentes.json`.\n\n" + _tabla_bitacora(resultado.consultas) + "\n"
    )
    ruta_opinion.write_text(encabezado + resultado.opinion_md + bitacora, encoding="utf-8")

    datos = {
        "archivo": resultado.archivo,
        "modelo": resultado.modelo,
        "inicio": resultado.inicio,
        "fin": resultado.fin,
        "duracion_s": resultado.duracion_s,
        "turnos": resultado.turnos,
        "costo_usd": resultado.costo_usd,
        "total_consultas": len(resultado.consultas),
        "consultas": [asdict(c) for c in resultado.consultas],
    }
    ruta_fuentes.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta_opinion, ruta_fuentes
