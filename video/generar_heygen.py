"""Genera video/presentacion.mp4 con el avatar y la voz clonada de Álvaro en HeyGen (API v2).
Llave: variable HEYGEN_API_KEY o Llavero de macOS (servicio heygen-api-key). Nunca se imprime.
Uso: .venv/bin/python video/generar_heygen.py [--guion video/guion_presentacion_heygen.md]"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
AVATAR_ID = "7fe8f1efce524ef3bde2eee843eb19a8"   # avatar "Alvaro"
VOICE_ID = "1e2fc153c2ee4a26bcae3f03295d621c"    # voz clonada "Alvaro" (español)
API = "https://api.heygen.com"


def llave() -> str:
    k = os.environ.get("HEYGEN_API_KEY")
    if not k:
        k = subprocess.run(["security", "find-generic-password", "-s", "heygen-api-key", "-w"],
                           capture_output=True, text=True).stdout.strip()
    if not k:
        sys.exit("No hay llave de HeyGen (HEYGEN_API_KEY o Llavero heygen-api-key).")
    return k


def api(metodo: str, ruta: str, datos: dict | None = None) -> dict:
    cuerpo = json.dumps(datos).encode() if datos is not None else None
    req = urllib.request.Request(API + ruta, data=cuerpo, method=metodo,
                                 headers={"X-Api-Key": llave(), "Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def escenas(guion: str) -> list[str]:
    parrafos = [p.strip() for p in guion.split("\n\n") if p.strip() and not p.startswith("#")]
    # HeyGen limita el texto por escena; agrupa párrafos hasta ~900 caracteres
    out, actual = [], ""
    for p in parrafos:
        if actual and len(actual) + len(p) > 900:
            out.append(actual); actual = p
        else:
            actual = (actual + "\n\n" + p).strip()
    if actual:
        out.append(actual)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guion", default=str(RAIZ / "video" / "guion_presentacion_heygen.md"))
    ap.add_argument("--salida", default=str(RAIZ / "video" / "presentacion.mp4"))
    a = ap.parse_args()
    partes = escenas(Path(a.guion).read_text(encoding="utf-8"))
    print(f"{len(partes)} escenas, {sum(len(p) for p in partes)} caracteres")
    cuerpo = {
        "title": "Lawgic Revisor · presentación",
        "caption": False,
        "dimension": {"width": 1280, "height": 720},
        "video_inputs": [
            {
                "character": {"type": "avatar", "avatar_id": AVATAR_ID, "avatar_style": "normal"},
                "voice": {"type": "text", "input_text": p, "voice_id": VOICE_ID, "speed": 1.0},
                "background": {"type": "color", "value": "#0D0D0D"},
            }
            for p in partes
        ],
    }
    r = api("POST", "/v2/video/generate", cuerpo)
    if r.get("error"):
        sys.exit(f"HeyGen rechazó la solicitud: {r['error']}")
    vid = r["data"]["video_id"]
    print("video_id:", vid)
    t0 = time.time()
    while True:
        s = api("GET", f"/v1/video_status.get?video_id={vid}")["data"]
        estado = s.get("status")
        print(f"  [{int(time.time()-t0):4d}s] {estado}", flush=True)
        if estado == "completed":
            url = s["video_url"]
            break
        if estado == "failed":
            sys.exit(f"Falló: {s.get('error')}")
        time.sleep(20)
    destino = Path(a.salida)
    urllib.request.urlretrieve(url, destino)
    print(f"Descargado: {destino} ({destino.stat().st_size/1e6:.1f} MB) · duración HeyGen: {s.get('duration')} s")


if __name__ == "__main__":
    main()
