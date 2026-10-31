"""Genera video/lawgic-revisor.mp4 (≤ 2 min): láminas con Pillow + narración + ensamble con ffmpeg.
Uso: .venv/bin/python video/hacer_video.py [carpeta_salida]
Narración: ~/bin/voz (ElevenLabs, voz Daniel); si falla, `say` de macOS."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "salida" / "contrato_quirografario_sintetico"
TRABAJO = RAIZ / "video" / "_trabajo"
TRABAJO.mkdir(parents=True, exist_ok=True)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FUENTES = Path.home() / "proyectos/ae-personal-toolkit/fonts"
LOGO = Path.home() / "proyectos/ae-personal-toolkit/assets/ae_logo_white_transparent.png"
W, H = 1920, 1080
FONDO, TEXTO, SUAVE, ACENTO, GRIS = "#0D0D0D", "#EFEAE0", "#D8D2C4", "#B8923A", "#9B9B9B"


def fuente(nombre: str, tam: int) -> ImageFont.FreeTypeFont:
    candidatos = [FUENTES / nombre, Path("/System/Library/Fonts/Supplemental/Arial.ttf")]
    for c in candidatos:
        if c.exists():
            return ImageFont.truetype(str(c), tam)
    return ImageFont.load_default()


TITULO = lambda t: fuente("PlayfairDisplay-Bold.ttf", t)
CUERPO = lambda t: fuente("Inter-Regular.ttf", t)
NEGRITA = lambda t: fuente("Inter-SemiBold.ttf", t)
MONO = lambda t: ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", t)


def lienzo(pie: str = "Lawgic Revisor · Hackatón Lawgic · 31 de octubre de 2026"):
    im = Image.new("RGB", (W, H), FONDO)
    d = ImageDraw.Draw(im)
    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA")
        logo.thumbnail((110, 110))
        im.paste(logo, (W - 110 - 70, 60), logo)
    d.line([(90, H - 90), (W - 90, H - 90)], fill=ACENTO, width=2)
    d.text((90, H - 72), pie, font=CUERPO(24), fill=GRIS)
    return im, d


def parrafo(d, xy, texto, f, color, ancho_chars, interlinea=1.35):
    x, y = xy
    for linea in textwrap.wrap(texto, ancho_chars):
        d.text((x, y), linea, font=f, fill=color)
        y += int(f.size * interlinea)
    return y


def lamina_portada():
    im, d = lienzo()
    d.text((90, 300), "Lawgic Revisor", font=TITULO(120), fill=TEXTO)
    parrafo(d, (90, 470), "Opinión legal de contratos de crédito con la ley consultada en tiempo real", CUERPO(46), SUAVE, 60)
    d.text((90, 720), "Proyecto para el Hackatón Lawgic · Álvaro Enríquez · AREZ Financiera", font=CUERPO(30), fill=ACENTO)
    d.text((90, 770), "Claude Opus 5.5 · Claude Agent SDK · Python", font=CUERPO(28), fill=GRIS)
    return im


def lamina_problema():
    im, d = lienzo()
    d.text((90, 110), "El problema", font=TITULO(80), fill=TEXTO)
    y = 270
    for t in [
        "Una SOFOM firma contratos de crédito con sus clientes todos los meses.",
        "Revisar cada contrato con un abogado cuesta tiempo y dinero.",
        "Un modelo de IA \"a secas\" cita artículos de memoria: a veces derogados, a veces inventados.",
    ]:
        d.ellipse([(90, y + 18), (110, y + 38)], fill=ACENTO)
        y = parrafo(d, (140, y), t, CUERPO(42), SUAVE, 70) + 36
    return im


def lamina_solucion():
    im, d = lienzo()
    d.text((90, 90), "Qué hicimos", font=TITULO(80), fill=TEXTO)
    cajas = [("Contrato", ".md · .pdf · .docx"), ("Agente\nClaude Opus 5.5", "lee, detecta riesgos"),
             ("Fuentes oficiales\nen tiempo real", "Diputados · DOF · CONDUSEF\nBanxico · SCJN"), ("Opinión legal", "semáforo · fundamento\n· bitácora con hora")]
    x, y, w, h, gap = 90, 270, 400, 230, 47
    for i, (t, s) in enumerate(cajas):
        x0 = x + i * (w + gap)
        d.rounded_rectangle([(x0, y), (x0 + w, y + h)], radius=18, outline=ACENTO, width=3)
        d.multiline_text((x0 + 24, y + 26), t, font=NEGRITA(34), fill=TEXTO, spacing=8)
        d.multiline_text((x0 + 24, y + 130), s, font=CUERPO(26), fill=GRIS, spacing=6)
        if i < len(cajas) - 1:
            d.text((x0 + w + 8, y + h // 2 - 22), "→", font=CUERPO(44), fill=ACENTO)
    y = 580
    for t in [
        "Regla: no puede citar una norma sin haberla leído en línea en esa misma sesión.",
        "consultar_ley descarga el PDF oficial vigente en ese instante: URL, hora, hash y última reforma.",
        "Cada consulta queda en una bitácora con hora exacta, generada por el programa, no por el modelo.",
    ]:
        d.ellipse([(90, y + 16), (108, y + 34)], fill=ACENTO)
        y = parrafo(d, (135, y), t, CUERPO(36), SUAVE, 82) + 26
    return im


def lamina_demo(fuentes: dict):
    im, d = lienzo()
    d.text((90, 80), "Demo: la bitácora de consulta en tiempo real", font=TITULO(62), fill=TEXTO)
    d.rounded_rectangle([(90, 190), (W - 90, 940)], radius=16, fill="#161616", outline="#333333", width=2)
    for i, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
        d.ellipse([(118 + i * 30, 208), (136 + i * 30, 226)], fill=c)
    y = 250
    d.text((120, y), f"$ python -m lawgic_revisor ejemplos/{fuentes['archivo']}", font=MONO(26), fill=SUAVE); y += 46
    d.text((120, y), "Consultando fuentes legales en tiempo real…", font=MONO(24), fill=GRIS); y += 44
    for c in fuentes["consultas"][:13]:
        hora = c["hora"][11:19]
        herr = c["herramienta"]
        color = ACENTO if herr == "LeyOficial" else "#7FB3D5"
        linea = c["consulta"]
        linea = linea if len(linea) <= 100 else linea[:97] + "…"
        d.text((120, y), f"• [{hora}]", font=MONO(24), fill=GRIS)
        d.text((120 + 190, y), f"{herr:<11}", font=MONO(24), fill=color)
        d.text((120 + 360, y), linea, font=MONO(24), fill=SUAVE)
        y += 40
    n = fuentes["total_consultas"]
    d.text((120, 880), f"{n} consultas · {fuentes['duracion_s']} s · {fuentes['turnos']} turnos · opinion.md + fuentes.json", font=MONO(24), fill=ACENTO)
    return im


def lamina_resultado(opinion: str):
    im, d = lienzo()
    d.text((90, 80), "Resultado sobre el contrato de prueba", font=TITULO(62), fill=TEXTO)
    sem = "ROJO" if re.search(r"\bROJO\b", opinion) else ("AMARILLO" if "AMARILLO" in opinion else "VERDE")
    color = {"ROJO": "#D64545", "AMARILLO": "#E0B341", "VERDE": "#3FA35B"}[sem]
    d.ellipse([(90, 200), (170, 280)], fill=color)
    d.text((200, 205), f"Semáforo {sem}", font=NEGRITA(54), fill=TEXTO)
    defectos = [
        ("Interés moratorio de 108 % (usura)", r"usura|morator"),
        ("Sin CAT", r"\bCAT\b"),
        ("Comisión de 10 % por pago anticipado", r"anticipad"),
        ("Pagaré en blanco", r"pagar[ée] en blanco|en blanco"),
        ("Vencimiento anticipado \"a su solo juicio\"", r"solo juicio|vencimiento anticipado"),
        ("Datos personales sin aviso de privacidad", r"privacidad"),
        ("Renuncia a la CONDUSEF · sin leyendas ni RECA", r"CONDUSEF"),
    ]
    y = 330
    for nombre, patron in defectos:
        ok = re.search(patron, opinion, re.I) is not None
        d.text((90, y), "✓" if ok else "✗", font=NEGRITA(40), fill=("#3FA35B" if ok else "#D64545"))
        d.text((150, y + 2), nombre, font=CUERPO(38), fill=SUAVE)
        y += 62
    d.text((90, 800), "Cada observación lleva artículo, ley, última reforma y URL verificada. Faltó el RECA del contrato.", font=CUERPO(28), fill=GRIS)
    return im


def lamina_cierre():
    im, d = lienzo()
    d.text((90, 160), "Todo está en el repositorio público", font=TITULO(72), fill=TEXTO)
    d.text((90, 300), "github.com/arez2026/hackaton-lawgic", font=MONO(44), fill=ACENTO)
    y = 420
    for t in ["Código del revisor, contrato sintético de prueba, opinión generada y bitácora de fuentes.",
              "Corre con una API key de Anthropic o con una sesión de Claude Code.",
              "Prototipo académico: no sustituye a un abogado, pero le ahorra la primera lectura."]:
        d.ellipse([(90, y + 16), (108, y + 34)], fill=ACENTO)
        y = parrafo(d, (135, y), t, CUERPO(38), SUAVE, 72) + 30
    return im


NARRACION = [
    "Lawgic Revisor: opinión legal de contratos de crédito con la ley consultada en tiempo real. Proyecto para el Hackatón Lawgic.",
    "AREZ Financiera es una SOFOM que firma contratos de crédito con sus clientes. Revisar cada contrato con un abogado cuesta tiempo y dinero. Y pedirle la revisión a un modelo de inteligencia artificial a secas tiene un defecto grave: cita artículos de memoria, a veces derogados o inventados.",
    "Construimos un agente que no puede citar una norma sin haberla leído en línea en esa misma sesión. Recibe el contrato, detecta las cláusulas con riesgo, descarga en ese instante el texto vigente de cada ley desde la Cámara de Diputados y emite una opinión con semáforo, artículo y enlace verificado. Cada consulta queda en una bitácora con hora exacta, generada por el programa, no por el modelo.",
    "Lo probamos con un contrato sintético con siete defectos sembrados: interés moratorio de usura, sin CAT, pagaré en blanco, vencimiento anticipado a su solo juicio, datos sin aviso de privacidad, renuncia a la CONDUSEF y comisión por pago anticipado. El agente consultó en vivo y lo registró con hora.",
    "Semáforo rojo. Detectó los defectos, los fundó en la ley vigente con su fecha de última reforma, y propuso la redacción correcta de cada cláusula.",
    "Todo el código, el contrato de prueba, la opinión generada y la bitácora están en el repositorio público. Es un prototipo académico: no sustituye a un abogado, pero le ahorra la primera lectura.",
]


def narrar(i: int, texto: str) -> Path:
    mp3 = TRABAJO / f"voz{i}.mp3"
    if mp3.exists() and mp3.stat().st_size > 1000:
        return mp3
    voz = Path.home() / "bin/voz"
    if voz.exists():
        r = subprocess.run([str(voz), "-n", "-o", str(mp3), texto], capture_output=True, text=True)
        if r.returncode == 0 and mp3.exists():
            return mp3
        print(f"  voz falló ({r.stderr.strip()[:120]}); uso `say`")
    aiff = TRABAJO / f"voz{i}.aiff"
    subprocess.run(["say", "-v", "Paulina", "-r", "175", "-o", str(aiff), texto], check=True)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(aiff), str(mp3)], check=True)
    return mp3


def duracion(archivo: Path) -> float:
    r = subprocess.run([FFMPEG, "-i", str(archivo)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def main():
    fuentes = json.loads((SALIDA / "fuentes.json").read_text(encoding="utf-8"))
    opinion = (SALIDA / "opinion.md").read_text(encoding="utf-8")
    laminas = [lamina_portada(), lamina_problema(), lamina_solucion(), lamina_demo(fuentes), lamina_resultado(opinion), lamina_cierre()]
    segmentos, total = [], 0.0
    for i, (im, texto) in enumerate(zip(laminas, NARRACION), start=1):
        png = TRABAJO / f"lamina{i}.png"; im.save(png)
        mp3 = narrar(i, texto)
        dur = duracion(mp3) / 1.05 + 0.4
        total += dur
        seg = TRABAJO / f"seg{i}.mp4"
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-loop", "1", "-framerate", "24", "-i", str(png), "-i", str(mp3),
                        "-t", f"{dur:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "24", "-preset", "medium",
                        "-filter:a", "atempo=1.05", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-shortest", str(seg)], check=True)
        segmentos.append(seg)
        print(f"  lámina {i}: {dur:.1f} s")
    lista = TRABAJO / "lista.txt"
    lista.write_text("".join(f"file '{s}'\n" for s in segmentos))
    final = RAIZ / "video" / "lawgic-revisor.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(final)], check=True)
    print(f"Video: {final} · {duracion(final):.1f} s · {final.stat().st_size/1e6:.1f} MB" + ("  ⚠ supera 120 s" if duracion(final) > 120 else ""))


if __name__ == "__main__":
    main()
