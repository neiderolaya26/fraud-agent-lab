# Datos publicados

Generados con `python -m fraud_lab.publicar` a partir de `data/interim/`. Todo en Parquet (zstd).

| Archivo | Fuente y licencia | Contenido |
|---|---|---|
| `baf_base_muestra`, `baf_v1_muestra` … `baf_v5_muestra` | [Bank Account Fraud](https://www.kaggle.com/datasets/sgpjesus/bank-account-fraud-dataset-neurips-2022), Jesus et al. (NeurIPS 2022), **CC BY-NC-SA 4.0** | Todos los fraudes (`peso = 1`) + 1 de cada 10 solicitudes sanas (`peso = 10`) |
| `paysim_muestra` | [PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1), Lopez-Rojas et al. (2016), **CC BY-SA 4.0** | Solo `TRANSFER` y `CASH_OUT`: todos los fraudes + 1 de cada 50 sanas (`peso = 50`) |
| `aml_lavado` | [IBM AML](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml), Altman et al. (NeurIPS 2023), **CDLA-Sharing 1.0** | Las 5.177 transferencias de lavado de HI-Small |
| `aml_patrones` | IBM AML, **CDLA-Sharing 1.0** | 3.209 transferencias dentro de 370 patrones, con su tipología |

- `fila` es el número de fila en el archivo original: la muestra es determinista y se puede volver a armar.
- `sum(peso)` reconstruye el tamaño de la población, y las tasas se calculan ponderando por `peso`.
- Las tres fuentes son sintéticas. Las cuentas de PaySim e IBM AML son códigos del simulador, no personas.
- Estos archivos se redistribuyen bajo la licencia de su fuente (CC BY-NC-SA, CC BY-SA y CDLA-Sharing, respectivamente), no bajo la licencia MIT del código.
