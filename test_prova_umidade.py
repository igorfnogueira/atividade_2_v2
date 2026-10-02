from pathlib import Path

from prova_umidade import provar


def test_prova_quantizada_no_bloco_final_do_tempo():
    prova = provar(Path("estufa_treino.csv"))

    assert prova.mae <= 10
    assert prova.mae <= prova.persistencia
    assert prova.mae_borda < prova.persistencia_borda
