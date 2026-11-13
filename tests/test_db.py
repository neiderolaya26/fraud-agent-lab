import duckdb
import pytest

from fraud_lab import db


@pytest.fixture
def carpeta(tmp_path):
    con = duckdb.connect()
    con.execute(f"COPY (SELECT 1 AS a UNION ALL SELECT 2) TO '{(tmp_path / 'uno.parquet').as_posix()}' (FORMAT parquet)").fetchall()
    con.close()
    return tmp_path


def test_crea_una_vista_por_parquet(carpeta):
    con = db.conectar(carpeta)
    assert con.sql("SELECT sum(a) FROM uno").fetchall() == [(3,)]


def test_solo_lectura_no_escribe_ni_lee_fuera(carpeta, tmp_path_factory):
    afuera = tmp_path_factory.mktemp("afuera")
    con = db.conectar(carpeta)
    with pytest.raises(db.ConsultaNoPermitida):
        db.consultar(con, f"COPY uno TO '{(carpeta / 'x.csv').as_posix()}'")
    with pytest.raises(db.ConsultaNoPermitida):
        db.consultar(con, "SELECT 1; DROP VIEW uno")
    with pytest.raises(duckdb.Error):
        db.consultar(con, f"SELECT * FROM read_csv('{(afuera / 'y.csv').as_posix()}')")
    with pytest.raises(duckdb.Error):
        con.sql("SET enable_external_access = true").fetchall()
    assert not (carpeta / "x.csv").exists()
    assert db.consultar(con, "WITH t AS (SELECT * FROM uno) SELECT count(*) AS n FROM t")["n"].iloc[0] == 2

