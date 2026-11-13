"""Publica en data/processed/ muestras y derivados de las tres fuentes (Parquet zstd, < 50 MB por archivo).

Uso:
    python -m fraud_lab.publicar

Las tres licencias permiten redistribuir (BAF: CC BY-NC-SA 4.0; PaySim: CC BY-SA 4.0;
IBM AML: CDLA-Sharing 1.0), pero los archivos completos pesan más de lo que GitHub acepta.
Por eso se publican muestras estratificadas: **todos los casos de fraude o lavado** y una
fracción fija de los casos sanos, con una columna `peso` que reconstruye la población
(sum(peso) = filas originales). La muestra es determinista: depende solo del número de fila.

Las tres fuentes son sintéticas y no traen datos de personas: los identificadores de cuenta
de PaySim e IBM AML son códigos generados por el simulador.
"""

from __future__ import annotations

import duckdb

from fraud_lab.db import INTERIM, PROCESSED
from fraud_lab.ingest import BAF_VARIANTES

# Fracción de casos sanos que entra en la muestra (1 de cada N filas).
UNO_DE_CADA = {"baf": 10, "paysim": 50}


def _muestra(tabla: str, etiqueta: str, n: int, filtro: str = "TRUE") -> str:
    fuente = (INTERIM / f"{tabla}.parquet").as_posix()
    return f"""
        SELECT * EXCLUDE (file_row_number), file_row_number AS fila,
               CASE WHEN {etiqueta} = 1 THEN 1 ELSE {n} END AS peso
        FROM read_parquet('{fuente}', file_row_number = true)
        WHERE ({filtro}) AND ({etiqueta} = 1 OR file_row_number % {n} = 0)
        ORDER BY fila"""


def consultas() -> dict[str, str]:
    c = {
        f"{t}_muestra": _muestra(t, "fraud_bool", UNO_DE_CADA["baf"]) for t in BAF_VARIANTES
    }
    # En PaySim solo hay fraude en TRANSFER y CASH_OUT: el resto de tipos no aporta al modelo.
    c["paysim_muestra"] = _muestra(
        "paysim", "isFraud", UNO_DE_CADA["paysim"], "type IN ('TRANSFER', 'CASH_OUT')"
    )
    aml = (INTERIM / "aml_transacciones.parquet").as_posix()
    c["aml_lavado"] = f"SELECT * FROM read_parquet('{aml}') WHERE es_lavado = 1 ORDER BY ts"
    c["aml_patrones"] = f"SELECT * FROM read_parquet('{(INTERIM / 'aml_patrones.parquet').as_posix()}')"
    return c


def publicar() -> dict[str, int]:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    filas = {}
    for tabla, sql in consultas().items():
        destino = (PROCESSED / f"{tabla}.parquet").as_posix()
        con.execute(f"COPY ({sql}) TO '{destino}' (FORMAT parquet, COMPRESSION zstd)").fetchall()
        filas[tabla] = con.execute(f"SELECT count(*) FROM read_parquet('{destino}')").fetchall()[0][0]
    return filas


if __name__ == "__main__":
    for tabla, n in publicar().items():
        tam = (PROCESSED / f"{tabla}.parquet").stat().st_size / 1e6
        print(f"{tabla:20s} {n:>9,} filas · {tam:5.1f} MB")
