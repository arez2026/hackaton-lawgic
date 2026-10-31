# Guion · presentación con avatar (HeyGen) · ~2 min

Hola, soy Álvaro Enríquez. Este es Lawgic Revisor, mi proyecto para el Hackatón Lawgic, y en dos minutos te cuento qué construimos y cómo probarlo.

El problema es sencillo. Una SOFOM como AREZ Financiera firma contratos de crédito con sus clientes todo el tiempo. Revisar cada contrato con un abogado cuesta tiempo y dinero. Y pedirle la revisión a una inteligencia artificial a secas tiene un defecto serio: cita artículos de memoria, a veces derogados, a veces inventados.

Lo que hicimos fue un agente que no puede citar una norma sin haberla leído en línea en esa misma sesión. Recibe el contrato, identifica las cláusulas con riesgo, descarga en ese instante el PDF oficial de cada ley desde la Cámara de Diputados, lee el artículo y emite una opinión legal: semáforo, observaciones por cláusula con artículo, fecha de última reforma y enlace, y una conclusión. Cada consulta queda registrada con la hora exacta en una bitácora que genera el programa, no el modelo. Esa es la prueba de que la ley se consultó en tiempo real.

Lo probamos con un contrato sintético al que sembramos siete defectos: interés moratorio de usura, sin CAT, pagaré en blanco, vencimiento anticipado a su solo juicio, datos personales sin aviso de privacidad, renuncia a la CONDUSEF y comisión por pago anticipado. El agente dio semáforo rojo, detectó los siete y propuso la redacción correcta de cada cláusula. Y donde no pudo verificar una fuente oficial, lo dijo, en vez de inventarla.

Todo está en el repositorio público de GitHub: el código, el contrato de prueba, la opinión generada, la bitácora y un video corto. Y esta misma página es la app: elige el contrato de ejemplo, pulsa "Revisar contrato" y verás las consultas aparecer en vivo, con la opinión y la bitácora al final.

Es un prototipo académico: no sustituye a un abogado, pero le ahorra la primera lectura. Gracias por revisarlo.
