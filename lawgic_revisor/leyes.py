"""Herramienta `consultar_ley`: descarga el PDF oficial de la Cámara de Diputados en el momento
de la consulta, extrae el artículo pedido y devuelve su texto con su procedencia (URL, hash, hora,
fecha de última reforma). Es la prueba más fuerte de consulta en tiempo real."""
from __future__ import annotations

import hashlib
import io
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from claude_agent_sdk import create_sdk_mcp_server, tool
from pypdf import PdfReader

CDMX = ZoneInfo("America/Mexico_City")
BASE = "https://www.diputados.gob.mx/LeyesBiblio/pdf/{clave}.pdf"

CATALOGO = {
    "LGOAAC": "Ley General de Organizaciones y Actividades Auxiliares del Crédito",
    "LTOSF": "Ley para la Transparencia y Ordenamiento de los Servicios Financieros",
    "LPDUSF": "Ley de Protección y Defensa al Usuario de Servicios Financieros",
    "LGTOC": "Ley General de Títulos y Operaciones de Crédito",
    "LFPDPPP": "Ley Federal de Protección de Datos Personales en Posesión de los Particulares",
    "LRSIC": "Ley para Regular las Sociedades de Información Crediticia",
    "CCF": "Código Civil Federal",
    "CCom": "Código de Comercio",
    "LIC": "Ley de Instituciones de Crédito",
}


@dataclass
class LeyDescargada:
    clave: str
    url: str
    hora: str
    sha256: str
    paginas: int
    ultima_reforma: str | None
    texto: str


_cache: dict[str, LeyDescargada] = {}


def descargar_ley(clave: str) -> LeyDescargada:
    clave = clave.strip()
    if clave in _cache:
        return _cache[clave]
    if clave not in CATALOGO:
        raise ValueError(f"Clave desconocida: {clave}. Usa una de: {', '.join(CATALOGO)}")
    url = BASE.format(clave=clave)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 LawgicRevisor/0.1"})
    hora = datetime.now(CDMX).isoformat(timespec="seconds")
    datos = urllib.request.urlopen(req, timeout=90).read()
    lector = PdfReader(io.BytesIO(datos))
    paginas = [(p.extract_text() or "") for p in lector.pages]
    primera = paginas[0] if paginas else ""
    m = re.search(r"ltima\s+[Rr]eforma\s+(?:publicada\s+)?DOF\s+([\d\-]+)", primera)
    ley = LeyDescargada(
        clave=clave, url=url, hora=hora, sha256=hashlib.sha256(datos).hexdigest(),
        paginas=len(paginas), ultima_reforma=m.group(1) if m else None,
        texto="\n".join(paginas),
    )
    _cache[clave] = ley
    return ley


def _patron_articulo(numero: str) -> re.Pattern:
    # "8" → Artículo 8o. / 8.- ; "87-J" → Artículo 87-J ; "56 Bis" → Artículo 56 Bis
    n = re.escape(numero.strip()).replace(r"\ ", r"\s+").replace(r"\-", r"\s*-\s*")
    return re.compile(rf"^\s*Art[íi]culo\s+{n}\s*(?:o\.|º\.?|°\.?|\.|-|\s)", re.I | re.M)


def extraer_articulo(ley: LeyDescargada, numero: str, maximo: int = 3500) -> str | None:
    texto = ley.texto
    m = _patron_articulo(numero).search(texto)
    if not m:
        return None
    inicio = m.start()
    siguiente = re.compile(r"\n\s*Art[íi]culo\s+\d", re.I).search(texto, m.end() + 20)
    fin = siguiente.start() if siguiente else inicio + maximo
    fragmento = texto[inicio:min(fin, inicio + maximo)]
    return re.sub(r"[ \t]+", " ", fragmento).strip()


@tool(
    "consultar_ley",
    "Descarga EN ESTE MOMENTO el PDF oficial vigente de una ley federal mexicana desde la Cámara de Diputados "
    "(diputados.gob.mx/LeyesBiblio) y devuelve el texto del artículo pedido con su procedencia: URL, hora de descarga, "
    "SHA-256 del archivo y fecha de última reforma publicada en el DOF. Claves válidas: " + ", ".join(CATALOGO) + ". "
    "Ejemplos de 'articulo': '87-J', '8', '56 Bis', '170', '291'.",
    {"ley": str, "articulo": str},
)
async def consultar_ley(args: dict) -> dict:
    clave = str(args.get("ley", "")).strip()
    numero = str(args.get("articulo", "")).strip()
    try:
        ley = descargar_ley(clave)
    except Exception as e:  # noqa: BLE001
        return {"content": [{"type": "text", "text": f"ERROR al descargar {clave}: {e}"}], "is_error": True}
    procedencia = (
        f"FUENTE OFICIAL: {CATALOGO[clave]} ({clave})\n"
        f"URL: {ley.url}\n"
        f"Descargado: {ley.hora} (hora de Ciudad de México) · {ley.paginas} páginas · SHA-256 {ley.sha256[:16]}…\n"
        f"Última reforma publicada en el DOF: {ley.ultima_reforma or 'no detectada en la carátula'}\n"
    )
    cuerpo = extraer_articulo(ley, numero)
    if cuerpo is None:
        return {"content": [{"type": "text", "text": procedencia + f"\nNo se encontró el artículo {numero} en el texto extraído. "
                 "Prueba otra numeración (por ejemplo '8' en vez de '8o') o un artículo cercano."}]}
    return {"content": [{"type": "text", "text": procedencia + "\n" + cuerpo}]}


def servidor_leyes():
    return create_sdk_mcp_server(name="leyes", version="0.1.0", tools=[consultar_ley])
