# Glosario

Términos del lab en palabras simples. Crece en cada sesión. La columna "En crédito" da la analogía cuando existe.

| Término | Qué es | En crédito |
|---|---|---|
| **AML** (*anti-money laundering*) | Prevención del lavado de dinero: detectar plata ilegal que se mueve entre cuentas para parecer legal | — |
| **BAF** (*Bank Account Fraud*) | Dataset de Feedzai (NeurIPS 2022): 1 M de solicitudes de apertura de cuenta online, 1,1% fraude, 8 meses, con 5 variantes de sesgo | Como Lending Club, pero la etiqueta es fraude en vez de mora |
| **Cuenta mula** | Cuenta abierta (con identidad falsa o prestada) para recibir y sacar plata de estafas | — |
| **DuckDB** | Motor SQL que corre dentro de Python y lee Parquet directo, sin servidor | — |
| **Fairness** | Que el modelo no perjudique de más a un grupo protegido (aquí, mayores de 50) | Igual que en crédito (no discriminar por edad o género) |
| **Fan-in / fan-out** | Tipologías de lavado: muchas cuentas envían a una (fan-in) o una envía a muchas (fan-out) | — |
| **FPR** (tasa de falsos positivos) | De cada 100 clientes buenos, a cuántos marca el modelo como sospechosos | Buenos rechazados por el corte |
| **Fricción** | La molestia al cliente bueno marcado por error: documentos, llamadas, bloqueo | El buen cliente rechazado que se va a la competencia |
| **GAN** | Dos redes que compiten (una genera filas falsas y otra las detecta) para crear datos sintéticos realistas | — |
| **Muestreo estratificado con peso** | Guardar todos los casos raros y una fracción de los comunes; el `peso` reconstruye la población | Como las muestras con factor de expansión |
| **Parquet** | Formato de archivo por columnas y comprimido: rápido de leer y liviano | — |
| **PaySim** | Simulador de transacciones de billetera móvil calibrado con logs reales de un país africano | — |
| **Partición temporal** | Entrenar con el pasado y evaluar con meses posteriores | *Out-of-time* (OOT) |
| **Recall @ 5% FPR** | Qué porcentaje del fraude atrapo si acepto molestar a 5 de cada 100 buenos | Un punto concreto de la curva ROC |
| **Datos sintéticos** | Datos generados por un modelo o simulador que imitan los reales sin copiar a personas | — |
| **Tipología** | "Forma" típica de un esquema de lavado (ciclo, fan-in, gather-scatter…) | — |
| **Variables de velocidad** | Cuántas solicitudes llegan en una ventana corta (6 h, 24 h, 4 semanas) | Consultas recientes al buró |
