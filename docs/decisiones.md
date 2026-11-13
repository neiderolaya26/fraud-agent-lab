# Registro de decisiones

Cada decisión importante del proyecto queda aquí, **escrita por Neider**: qué se decidió, qué alternativas había y por qué.

---

## 001 — Alcance, datos y métrica de éxito

- **Fecha:** 2026-11-13
- **Contexto** (`python -m fraud_lab.ingest`, `notebooks/01_panorama_fuentes.ipynb`):
  - El lab de crédito usa Lending Club, que **no trae etiquetas de fraude**. Para estudiar fraude hay que salir de ese dataset.
  - **Bank Account Fraud** (Feedzai, NeurIPS 2022): 6 variantes de 1 M de solicitudes de apertura de cuenta en 8 meses, 1,10% de fraude en todas, con sesgos controlados respecto a la edad (≥ 50). Trae `credit_risk_score` y `proposed_credit_limit`.
  - **PaySim**: 6,36 M de transacciones de dinero móvil en 743 horas, 0,13% de fraude, solo en `TRANSFER` y `CASH_OUT`.
  - **IBM AML HI-Small** (NeurIPS 2023): 5,08 M de transferencias en 18 días, 0,10% de lavado; 3.209 de esas transferencias están dentro de 370 patrones con 8 tipologías.
  - Licencias (metadatos de Kaggle): BAF CC BY-NC-SA 4.0, PaySim CC BY-SA 4.0, IBM AML CDLA-Sharing 1.0. Elliptic quedó fuera: es CC BY-NC-ND y no permite publicar derivados.
- **Opciones:**
  - **A) Ciclo completo:** solicitud (BAF) + transacción (PaySim) + red y lavado (IBM AML) + agente investigador de alertas.
  - **B) Solo onboarding (BAF):** el complemento más directo del lab de crédito, más corto y profundo.
  - **C) Solo transaccional:** monitoreo de tarjetas o dinero móvil; se aleja del lab de crédito.
- **Decisión:** **A) Ciclo completo**, con BAF como eje porque es el puente con el lab de crédito: la puerta antifraude va antes del motor de PD. El enlace entre labs es por el agente (el agente de crédito consulta el servidor MCP de fraude), no por los datos: las poblaciones no se cruzan.
- **Métrica de éxito, en dos niveles:**
  1. **Técnica:** recall con una tasa de falsos positivos del 5% (estándar del paper de BAF), comparable entre modelos y variantes.
  2. **Negocio:** pérdida neta evitada por cada 10.000 casos = fraude evitado − costo de revisión manual − fricción con clientes buenos. Los costos son supuestos y quedan como parámetros visibles.
  - Toda pieza que use la edad reporta además la brecha entre grupos (≥ 50 contra < 50).
- **Datos en el repo:** todo en Parquet (zstd). Los archivos completos pesan más de lo que acepta GitHub, así que en `data/processed/` publico muestras estratificadas: todos los fraudes y una fracción fija de los casos sanos, con una columna `peso` que reconstruye la población.
- **Por qué (en mis palabras):** Quiero el ciclo completo porque el fraude no ocurre en un solo momento: entra en la solicitud, se cobra en las transacciones y se esconde en la red. Pongo BAF en el centro porque ahí se ve el choque con mi lab de crédito: el fraude es 3,4% en el decil de mejor puntaje, contra 0,5% en el peor. Mido en dos niveles porque el recall con 5% de falsos positivos me deja comparar modelos sin supuestos, pero la decisión de negocio se toma en dinero, igual que en el P&L del lab de crédito.
