"""Extrae el texto de un contrato en .md, .txt, .pdf o .docx."""
from pathlib import Path

FORMATOS = {".md", ".txt", ".pdf", ".docx"}


def extraer_texto(ruta: Path) -> str:
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo: {ruta}")
    ext = ruta.suffix.lower()
    if ext not in FORMATOS:
        raise ValueError(f"Formato no soportado: {ext}. Usa {', '.join(sorted(FORMATOS))}")
    if ext in {".md", ".txt"}:
        return ruta.read_text(encoding="utf-8")
    if ext == ".pdf":
        from pypdf import PdfReader
        lector = PdfReader(str(ruta))
        return "\n\n".join((p.extract_text() or "") for p in lector.pages)
    from docx import Document
    doc = Document(str(ruta))
    partes = [p.text for p in doc.paragraphs]
    for tabla in doc.tables:
        for fila in tabla.rows:
            partes.append(" | ".join(c.text for c in fila.cells))
    return "\n".join(partes)
