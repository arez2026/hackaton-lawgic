# Diseño · Lawgic Revisor (2026-10-31)

## Objetivo
Demostrar, en un proyecto pequeño, que un agente puede revisar un contrato de crédito de una SOFOM y fundamentar su opinión en leyes **consultadas en tiempo real**, dejando evidencia verificable de cada consulta.

## Decisiones
- **Motor**: Claude Opus 5.5 mediante el Claude Agent SDK (Python). Da acceso a las herramientas `WebSearch` y `WebFetch` sin montar infraestructura propia y funciona con API key o con sesión de Claude Code.
- **Prueba de tiempo real**: el programa (no el modelo) registra cada `ToolUseBlock` de WebSearch/WebFetch con la hora local y, al llegar su `ToolResultBlock`, las URL devueltas y un extracto. Se guarda en `fuentes.json` y se anexa como tabla al final de `opinion.md`.
- **Aislamiento**: `setting_sources=[]` para que el agente no cargue configuraciones ni `CLAUDE.md` locales; solo WebSearch y WebFetch permitidas; herramientas de archivos y shell prohibidas.
- **Formato de salida**: el modelo responde entre marcas `<<<OPINION>>>` y `<<<FIN>>>` para extraer la opinión limpia aunque haya texto intermedio.
- **Datos**: contrato sintético con defectos sembrados; el repositorio es público y no lleva datos reales de clientes.
- **Fuera de alcance**: interfaz web, base de datos, multiusuario.

## Flujo
contrato → `extraer_texto` → instrucción (fecha, archivo, texto) → `query()` del SDK → captura de bloques → `Resultado` → `guardar()` → `opinion.md` + `fuentes.json`.

## Verificación
Corrida real sobre el contrato sintético con los entregables en `salida/`. Se revisa que cada observación tenga artículo y URL, que la bitácora tenga horas crecientes y que los defectos sembrados aparezcan en la opinión.
