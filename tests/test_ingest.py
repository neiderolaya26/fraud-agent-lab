import pytest

from fraud_lab import db
from fraud_lab.ingest import parsear_patrones

PATRONES = """BEGIN LAUNDERING ATTEMPT - FAN-OUT:  Max 2-degree Fan-Out
2022/09/01 00:06,021174,800737690,012,80011F990,2848.96,Euro,2848.96,Euro,ACH,1
2022/09/01 04:33,021174,800737690,020,80020C5B0,8630.40,Euro,8630.40,Euro,ACH,1
END LAUNDERING ATTEMPT - FAN-OUT

BEGIN LAUNDERING ATTEMPT - CYCLE:  Max 10 hops
2022/09/01 00:03,01467,8013C4030,020,80BC62F10,58702.10,Yuan,58702.10,Yuan,ACH,1
END LAUNDERING ATTEMPT - CYCLE
"""


def test_parsea_bloques_de_patrones():
    filas = parsear_patrones(PATRONES)
    assert len(filas) == 3
    assert [f[:2] for f in filas] == [(1, "fan-out"), (1, "fan-out"), (2, "cycle")]
    assert filas[0][2] == "Max 2-degree Fan-Out"
    assert filas[2][8] == pytest.approx(58702.10) and filas[2][9] == "Yuan"


@pytest.mark.skipif(not db.tablas(db.PROCESSED), reason="sin data/processed")
def test_muestras_reconstruyen_la_poblacion():
    con = db.conectar(db.PROCESSED)
    n, tasa = con.sql("SELECT sum(peso), sum(peso * fraud_bool) / sum(peso) FROM baf_base_muestra").fetchall()[0]
    assert abs(n - 1_000_000) < 1_000 and tasa == pytest.approx(0.011, abs=5e-4)
    # Todos los fraudes entran con peso 1.
    assert con.sql("SELECT count(*), max(peso) FROM baf_base_muestra WHERE fraud_bool = 1").fetchall()[0] == (11_029, 1)
    assert con.sql("SELECT sum(isFraud) FROM paysim_muestra").fetchall()[0][0] == 8_213
    assert con.sql("SELECT count(DISTINCT type) FROM paysim_muestra").fetchall()[0][0] == 2
    assert con.sql("SELECT count(*), min(es_lavado) FROM aml_lavado").fetchall()[0] == (5_177, 1)
    assert con.sql("SELECT count(DISTINCT tipologia) FROM aml_patrones").fetchall()[0][0] == 8
