from pathlib import Path

from prova_umidade import provar


def test_prova_quantizada_no_bloco_final_do_tempo():
    prova = provar(Path("treino_umidade.csv"))

    assert prova.linhas_prova == 2168
    assert prova.inicio_prova.startswith("2026-09-24T12:34")
    assert prova.fim_prova.startswith("2026-09-28T11:54")
    assert prova.mae <= 10
