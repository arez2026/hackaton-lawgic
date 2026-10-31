"""Lawgic Revisor · app web local.  Uso: streamlit run app.py"""
from __future__ import annotations

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

from lawgic_revisor.revisor import MODELO_POR_DEFECTO, guardar, revisar

RAIZ = Path(__file__).resolve().parent
EJEMPLO = RAIZ / "ejemplos" / "contrato_quirografario_sintetico.md"

st.set_page_config(page_title="Lawgic Revisor", page_icon="⚖️", layout="wide")
st.title("⚖️ Lawgic Revisor")
st.caption("Opinión legal de contratos de crédito con la ley oficial consultada en tiempo real · Hackatón Lawgic · prototipo académico, no sustituye a un abogado.")

with st.sidebar:
    st.header("Contrato")
    fuente = st.radio("Origen", ["Subir archivo", "Contrato de ejemplo", "Pegar texto"], label_visibility="collapsed")
    archivo = texto = None
    if fuente == "Subir archivo":
        archivo = st.file_uploader("Archivo .md, .txt, .pdf o .docx", type=["md", "txt", "pdf", "docx"])
    elif fuente == "Pegar texto":
        texto = st.text_area("Texto del contrato", height=260, placeholder="Pega aquí el contrato…")
    else:
        st.info("Contrato de crédito quirografario sintético con 7 defectos sembrados.")
        with st.expander("Ver el contrato"):
            st.markdown(EJEMPLO.read_text(encoding="utf-8"))
    modelo = st.text_input("Modelo", MODELO_POR_DEFECTO)
    revisar_btn = st.button("Revisar contrato", type="primary", use_container_width=True)
    st.markdown("---")
    st.markdown("**Cómo funciona**\n\n1. Lee el contrato.\n2. Descarga en ese instante el PDF oficial de cada ley (Diputados) y lee el artículo.\n3. Emite la opinión con artículo, última reforma y URL.\n4. Registra cada consulta con hora exacta.")


def _ruta_contrato() -> Path | None:
    if fuente == "Contrato de ejemplo":
        return EJEMPLO
    if fuente == "Subir archivo" and archivo is not None:
        destino = Path(tempfile.mkdtemp()) / archivo.name
        destino.write_bytes(archivo.getvalue())
        return destino
    if fuente == "Pegar texto" and texto and texto.strip():
        destino = Path(tempfile.mkdtemp()) / "contrato_pegado.md"
        destino.write_text(texto, encoding="utf-8")
        return destino
    return None


if revisar_btn:
    ruta = _ruta_contrato()
    if ruta is None:
        st.warning("Primero sube un archivo, pega el texto o elige el contrato de ejemplo.")
    else:
        st.subheader("Consultas en tiempo real")
        caja = st.empty()
        lineas: list[str] = []

        def en_vivo(evento: str):
            lineas.append(evento)
            caja.code("\n".join(lineas), language="text")

        with st.spinner("El agente está leyendo el contrato y consultando la ley vigente… (1 a 3 minutos)"):
            try:
                r = asyncio.run(revisar(ruta, modelo=modelo, en_vivo=en_vivo))
            except Exception as e:  # noqa: BLE001
                st.error(f"Error al revisar: {e}")
                st.stop()
        if not r.consultas:
            caja.info("El agente no hizo consultas.")
        carpeta = RAIZ / "salida" / "app" / f"{ruta.stem}_{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        ruta_opinion, ruta_fuentes = guardar(r, carpeta)
        st.session_state["resultado"] = {
            "opinion": r.opinion_md, "md": ruta_opinion.read_text(encoding="utf-8"),
            "json": ruta_fuentes.read_text(encoding="utf-8"), "consultas": r.consultas,
            "archivo": r.archivo, "duracion": r.duracion_s, "turnos": r.turnos,
        }

res = st.session_state.get("resultado")
if res:
    op = res["opinion"]
    sem = "ROJO" if "ROJO" in op else ("AMARILLO" if "AMARILLO" in op else ("VERDE" if "VERDE" in op else "—"))
    color = {"ROJO": "🔴", "AMARILLO": "🟡", "VERDE": "🟢"}.get(sem, "⚪")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Semáforo", f"{color} {sem}")
    c2.metric("Consultas en vivo", len(res["consultas"]))
    c3.metric("Duración", f"{res['duracion']:.0f} s")
    c4.metric("Turnos del agente", res["turnos"])
    d1, d2 = st.columns(2)
    d1.download_button("Descargar opinion.md", res["md"], file_name="opinion.md", mime="text/markdown", use_container_width=True)
    d2.download_button("Descargar fuentes.json", res["json"], file_name="fuentes.json", mime="application/json", use_container_width=True)
    pestañas = st.tabs(["Opinión legal", "Bitácora de fuentes"])
    with pestañas[0]:
        st.markdown(op)
    with pestañas[1]:
        st.caption("Cada fila es una llamada real hecha por el agente durante esta revisión, con su hora exacta (Ciudad de México).")
        st.dataframe(
            [{"#": c.orden, "Hora": c.hora[11:19], "Herramienta": c.herramienta, "Consulta": c.consulta,
              "Fuentes": ", ".join(c.urls_encontradas[:3]), "Error": "sí" if c.error else ""} for c in res["consultas"]],
            use_container_width=True, hide_index=True,
        )
else:
    st.markdown(
        """
### Cómo probarla
1. En el panel izquierdo elige **Contrato de ejemplo** (o sube el tuyo).
2. Pulsa **Revisar contrato**.
3. Observa las consultas apareciendo en vivo; al terminar verás el semáforo, la opinión y la bitácora.

> La revisión usa el modelo configurado con una API key de Anthropic o la sesión de Claude Code de esta máquina.
"""
    )
