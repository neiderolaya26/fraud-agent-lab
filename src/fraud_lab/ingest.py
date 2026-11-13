"""Convierte los CSV crudos de data/raw/ en Parquet (zstd) en data/interim/ e imprime los primeros hechos.

Uso:
    python -m fraud_lab.ingest            # todo
    python -m fraud_lab.ingest --resumen  # solo los hechos, sin reconvertir

Fuentes (descarga en el README):
- baf/        Bank Account Fraud (Feedzai, NeurIPS 2022): 6 variantes de 1 M de solicitudes de apertura de cuenta.
- paysim/     PaySim: 6,36 M de transacciones de dinero móvil simuladas (744 horas).
- ibm_aml/    IBM AML HI-Small (NeurIPS 2023): 5 M de transferencias entre cuentas + patrones de lavado.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import duckdb

from fraud_lab.db import INTERIM, RAIZ

RAW = RAIZ / "data" / "raw"

BAF_VARIANTES = {
    "baf_base": "Base.csv",
    "baf_v1": "Variant I.csv",
    "baf_v2": "Variant II.csv",
    "baf_v3": "Variant III.csv",
    "baf_v4": "Variant IV.csv",
    "baf_v5": "Variant V.csv",
}

# Nombres en snake_case; la fuente repite "Account" para origen y destino.
IBM_COLUMNAS = [
    "ts", "banco_origen", "cuenta_origen", "banco_destino", "cuenta_destino",
    "monto_recibido", "moneda_recibida", "monto_pagado", "moneda_pagada", "formato", "es_lavado",
]
IBM_TIPOS = {c: "VARCHAR" for c in IBM_COLUMNAS} | {
    "monto_recibido": "DOUBLE", "monto_pagado": "DOUBLE", "es_lavado": "TINYINT",
}

_PATRON_INICIO = re.compile(r"BEGIN LAUNDERING ATTEMPT - ([A-Z\-]+):?\s*(.*)")


def _copiar(con: duckdb.DuckDBPyConnection, sql: str, tabla: str) -> int:
    destino = (INTERIM / f"{tabla}.parquet").as_posix()
    con.execute(f"COPY ({sql}) TO '{destino}' (FORMAT parquet, COMPRESSION zstd)").fetchall()
    return con.execute(f"SELECT count(*) FROM read_parquet('{destino}')").fetchall()[0][0]


def parsear_patrones(texto: str) -> list[tuple]:
    """Lee HI-Small_Patterns.txt: bloques BEGIN/END con una transferencia por línea.

    Devuelve tuplas (patron_id, tipologia, detalle, ts, banco_origen, cuenta_origen,
    banco_destino, cuenta_destino, monto_pagado, moneda_pagada).
    """
    filas, patron_id, tipologia, detalle = [], 0, None, None
    for linea in texto.splitlines():
        linea = linea.strip()
        if m := _PATRON_INICIO.match(linea):
            patron_id += 1
            tipologia, detalle = m.group(1).lower(), m.group(2).strip()
        elif linea.startswith("END LAUNDERING ATTEMPT"):
            tipologia = None
        elif linea and tipologia:
            c = linea.split(",")
            filas.append((patron_id, tipologia, detalle, c[0], c[1], c[2], c[3], c[4], float(c[7]), c[8]))
    return filas


def ingerir() -> dict[str, int]:
    INTERIM.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    filas: dict[str, int] = {}

    for tabla, archivo in BAF_VARIANTES.items():
        ruta = (RAW / "baf" / archivo).as_posix()
        filas[tabla] = _copiar(con, f"SELECT * FROM read_csv('{ruta}', header=true)", tabla)

    paysim = next((RAW / "paysim").glob("*.csv")).as_posix()
    filas["paysim"] = _copiar(con, f"SELECT * FROM read_csv('{paysim}', header=true)", "paysim")

    trans = (RAW / "ibm_aml" / "HI-Small_Trans.csv").as_posix()
    filas["aml_transacciones"] = _copiar(
        con,
        f"""SELECT strptime(ts, '%Y/%m/%d %H:%M') AS ts, * EXCLUDE (ts)
            FROM read_csv('{trans}', header=true, columns={IBM_TIPOS!r})""",
        "aml_transacciones",
    )
    cuentas = (RAW / "ibm_aml" / "HI-Small_accounts.csv").as_posix()
    filas["aml_cuentas"] = _copiar(
        con,
        f"""SELECT "Bank Name" AS banco_nombre, CAST("Bank ID" AS VARCHAR) AS banco_id,
                   "Account Number" AS cuenta, "Entity ID" AS entidad_id, "Entity Name" AS entidad_nombre
            FROM read_csv('{cuentas}', header=true, all_varchar=true)""",
        "aml_cuentas",
    )

    patrones = parsear_patrones((RAW / "ibm_aml" / "HI-Small_Patterns.txt").read_text())
    con.execute(
        """CREATE TABLE p (patron_id INT, tipologia VARCHAR, detalle VARCHAR, ts VARCHAR, banco_origen VARCHAR,
           cuenta_origen VARCHAR, banco_destino VARCHAR, cuenta_destino VARCHAR, monto_pagado DOUBLE, moneda_pagada VARCHAR)"""
    ).fetchall()
    con.executemany("INSERT INTO p VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", patrones)
    filas["aml_patrones"] = _copiar(
        con, "SELECT * EXCLUDE (ts), strptime(ts, '%Y/%m/%d %H:%M') AS ts FROM p", "aml_patrones"
    )
    return filas


def resumen() -> None:
    from fraud_lab import db

    con = db.conectar(solo_lectura=False)
    q = lambda sql: con.execute(sql).fetchall()  # noqa: E731

    print("\n== Bank Account Fraud (solicitudes de apertura de cuenta)")
    for t in BAF_VARIANTES:
        n, tasa, meses = q(f"SELECT count(*), avg(fraud_bool), count(DISTINCT month) FROM {t}")[0]
        print(f"  {t:9s} {n:>9,} solicitudes · fraude {tasa:.2%} · {meses} meses")
    print("  fraude por mes (base):", [f"{m}:{t:.2%}" for m, t in q(
        "SELECT month, avg(fraud_bool) FROM baf_base GROUP BY 1 ORDER BY 1")])
    print("  fraude por edad (base):", [f"{e}:{t:.2%}" for e, t in q(
        "SELECT customer_age, avg(fraud_bool) FROM baf_base GROUP BY 1 ORDER BY 1")])

    print("\n== PaySim (transacciones de dinero móvil)")
    n, fraudes, horas = q("SELECT count(*), sum(isFraud), max(step) FROM paysim")[0]
    print(f"  {n:,} transacciones en {horas} horas · {fraudes:,} fraudes ({fraudes / n:.3%})")
    for tipo, nt, f, monto in q(
        "SELECT type, count(*), sum(isFraud), sum(amount) FILTER (isFraud = 1) FROM paysim GROUP BY 1 ORDER BY 2 DESC"
    ):
        print(f"  {tipo:9s} {nt:>9,} · fraudes {f:>5,} · monto defraudado {monto or 0:,.0f}")
    marcadas, aciertos = q("SELECT sum(isFlaggedFraud), sum(isFlaggedFraud * isFraud) FROM paysim")[0]
    print(f"  la regla del simulador (isFlaggedFraud) marca {marcadas} y acierta {aciertos} de {fraudes:,}")

    print("\n== IBM AML HI-Small (transferencias entre cuentas)")
    n, lav, d0, d1, cuentas = q(
        """SELECT count(*), sum(es_lavado), min(ts)::DATE, max(ts)::DATE,
                  count(DISTINCT banco_origen || cuenta_origen) FROM aml_transacciones""")[0]
    print(f"  {n:,} transferencias del {d0} al {d1} · {lav:,} de lavado ({lav / n:.3%}) · {cuentas:,} cuentas que envían")
    print("  formatos con lavado:", q(
        "SELECT formato, sum(es_lavado) FROM aml_transacciones GROUP BY 1 HAVING sum(es_lavado) > 0 ORDER BY 2 DESC"))
    print("  patrones etiquetados:", q(
        "SELECT tipologia, count(DISTINCT patron_id) AS n FROM aml_patrones GROUP BY 1 ORDER BY 2 DESC"))
    total_pat = q("SELECT count(*) FROM aml_patrones")[0][0]
    print(f"  {total_pat:,} de {lav:,} transferencias de lavado pertenecen a un patrón con tipología")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--resumen", action="store_true", help="solo imprime los hechos")
    args = ap.parse_args(argv)
    if not args.resumen:
        for tabla, n in ingerir().items():
            print(f"{tabla:20s} {n:>10,} filas")
    resumen()


if __name__ == "__main__":
    sys.exit(main())
