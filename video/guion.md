# Guion del video (≤ 2 minutos)

## 1 · Portada (0–10 s)
Lawgic Revisor: opinión legal de contratos de crédito con la ley consultada en tiempo real. Proyecto para el Hackatón Lawgic.

## 2 · El problema (10–32 s)
AREZ Financiera es una SOFOM que firma contratos de crédito con sus clientes. Revisar cada contrato con un abogado cuesta tiempo y dinero. Y pedirle la revisión a un modelo de inteligencia artificial a secas tiene un defecto grave: cita artículos de memoria, a veces derogados o inventados.

## 3 · Qué hicimos (32–60 s)
Construimos un agente que no puede citar una norma sin haberla leído en línea en esa misma sesión. Recibe el contrato, identifica las cláusulas con riesgo, busca y lee el texto vigente de cada ley en fuentes oficiales, y emite una opinión legal con semáforo, artículo y enlace verificado. Cada consulta a la web queda registrada con la hora exacta en una bitácora que genera el programa, no el modelo.

## 4 · Demo (60–88 s)
Lo probamos con un contrato de crédito sintético al que sembramos siete defectos: interés moratorio de usura, sin CAT, pagaré en blanco, vencimiento anticipado a su solo juicio, datos personales sin aviso de privacidad, renuncia a la CONDUSEF y comisión por pago anticipado. El agente hizo sus consultas en vivo, las registró con hora, y dio su veredicto.

## 5 · Resultado (88–108 s)
Semáforo rojo. Detectó los defectos, los fundó en la ley vigente y propuso la redacción correcta de cada cláusula.

## 6 · Cierre (108–120 s)
Todo el código, el contrato de prueba, la opinión generada y la bitácora están en el repositorio público. Es un prototipo académico: no sustituye a un abogado, pero le ahorra la primera lectura.
