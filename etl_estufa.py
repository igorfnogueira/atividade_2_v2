"""Limpa as leituras da estufa e calcula a borda da luz pelo canal real.

A borda é +1 quando a quantum board acende na hora seguinte, -1 quando
apaga, e 0 quando o canal não muda. Não usa o relógio fixo das 17:00.
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path

ORIGEM = Path("estufa_leituras.csv")
DESTINO = Path("estufa_treino.csv")
RELATORIO = Path("docs/etl-estufa.md")
HORIZONTE = timedelta(minutes=60)
TOLERANCIA = timedelta(minutes=75)
SALTO = 8.0

APARELHOS = (
    "aquecedor_ligado",
    "umidificador_ligado",
    "desumidificador_ligado",
    "exaustor_ligado",
    "ventoinha_entrada_ligada",
)

COLUNAS = (
    "timestamp_iso",
    "alvo_iso",
    "cycle_id",
    "fase",
    "luz_horas_fase",
    "umid_min_fase",
    "umid_max_fase",
    "umid_estufa_pct",
    "umid_em_1h",
    "luz_ligada",
    "luz_ligada_depois",
    "borda",
    "aquecedor_ligado",
    "umidificador_ligado",
    "desumidificador_ligado",
    "exaustor_ligado",
    "ventoinha_entrada_ligada",
    "aparelhos_mudaram",
)


def _instante(texto: str) -> datetime:
    return datetime.fromisoformat(texto)


def _ligado(valor: str):
    texto = valor.strip().lower()
    if texto == "true":
        return True
    if texto == "false":
        return False
    return None


def _borda(antes, depois):
    if antes is None or depois is None:
        return ""
    if antes == depois:
        return "0"
    return "1" if depois else "-1"


def _mudaram(atual, seguinte) -> str:
    nomes = []
    for coluna in APARELHOS:
        antes = _ligado(atual[coluna])
        depois = _ligado(seguinte[coluna])
        if antes is None or depois is None or antes == depois:
            continue
        nomes.append(coluna.replace("_ligado", ""))
    return ",".join(nomes)


def _linhas(caminho: Path):
    linhas = []
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            if not linha["timestamp_iso"].startswith("2026"):
                continue
            if not linha["umid_estufa_pct"].strip():
                continue
            linhas.append(linha)
    linhas.sort(key=lambda linha: linha["timestamp_iso"])
    return linhas


def _completar(linhas):
    indice_alvo = 0
    saida = []
    for linha in linhas:
        instante = _instante(linha["timestamp_iso"])
        limite = instante + HORIZONTE
        while indice_alvo < len(linhas) and _instante(linhas[indice_alvo]["timestamp_iso"]) < limite:
            indice_alvo += 1
        registro = {coluna: linha.get(coluna, "") for coluna in COLUNAS}
        registro["alvo_iso"] = ""
        registro["umid_em_1h"] = ""
        registro["luz_ligada_depois"] = ""
        registro["borda"] = ""
        registro["aparelhos_mudaram"] = ""
        if indice_alvo < len(linhas):
            seguinte = linhas[indice_alvo]
            instante_alvo = _instante(seguinte["timestamp_iso"])
            if instante_alvo - instante <= TOLERANCIA and seguinte["umid_estufa_pct"].strip():
                registro["alvo_iso"] = seguinte["timestamp_iso"]
                registro["umid_em_1h"] = seguinte["umid_estufa_pct"]
                registro["luz_ligada_depois"] = seguinte["luz_ligada"]
                registro["borda"] = _borda(_ligado(linha["luz_ligada"]), _ligado(seguinte["luz_ligada"]))
                registro["aparelhos_mudaram"] = _mudaram(linha, seguinte)
        saida.append(registro)
    return saida


def _gravar(caminho: Path, linhas):
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def _adr(dia: str) -> str:
    notas = []
    if dia == "2026-09-22":
        notas.append("ADR-0045, temperatura no teto da fase e o ar em cool")
    if dia in ("2026-09-25", "2026-09-26"):
        notas.append("ADR-0050, aquecedor no dimmer com prioridade da umidade")
    if dia == "2026-09-26":
        notas.append("ADR-0051, pré-aquecimento antes da luz apagar")
    if dia >= "2026-09-28":
        notas.append("ADR-0054, estado real do ar-condicionado passa a ser gravado")
    return "; ".join(notas)


def _relatorio(linhas) -> str:
    pares = [linha for linha in linhas if linha["umid_em_1h"]]
    saltos = []
    for linha in pares:
        delta = float(linha["umid_em_1h"]) - float(linha["umid_estufa_pct"])
        if abs(delta) > SALTO:
            saltos.append((linha, delta))
    bordas = [linha["borda"] for linha in pares]
    texto = [
        "# ETL da estufa",
        "",
        "A tabela de treino sai de `estufa_leituras.csv`. Saem as linhas de 1969 e as sem umidade da estufa. A ordem é a do tempo, com os dois ciclos em sequência.",
        "",
        f"Linhas gravadas: {len(linhas)}. Pares de uma hora: {len(pares)}. Borda +1: {bordas.count('1')}. Borda -1: {bordas.count('-1')}. Borda 0: {bordas.count('0')}.",
        "",
        "A fase gravada na leitura oscila no primeiro ciclo entre germinação e plântula. O ETL não corrige esse rótulo. A borda usa o canal `luz_ligada`, não o relógio das 17:00 e não o nome da fase. Enquanto a placa permanece apagada, a borda fica 0. Um rótulo de germinação com a luz mudando é o campo de fase oscilando no meio de uma leitura em que o canal realmente trocou.",
        "",
        "Causas já escritas no FN Grow, citadas quando a data do salto coincide: ADR-0045 em 22/09, ADR-0050 em 25/09 e 26/09, ADR-0051 em 26/09, ADR-0054 a partir de 28/09.",
        "",
        f"Saltos de uma hora maiores que {SALTO:.0f} pontos: {len(saltos)}.",
        "",
    ]
    for linha, delta in saltos:
        dia = linha["timestamp_iso"][:10]
        aparelhos = linha["aparelhos_mudaram"] or "nenhum"
        nota = _adr(dia)
        extra = f" {nota}." if nota else ""
        texto.append(
            f"- {linha['timestamp_iso']} fase {linha['fase'] or 'vazia'}, "
            f"luz {linha['luz_ligada'] or 'vazia'} para {linha['luz_ligada_depois'] or 'vazia'}, "
            f"delta {delta:+.1f}, aparelhos que mudaram: {aparelhos}.{extra}"
        )
    texto.append("")
    return "\n".join(texto)


def main():
    linhas = _completar(_linhas(ORIGEM))
    _gravar(DESTINO, linhas)
    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO.write_text(_relatorio(linhas), encoding="utf-8")
    print(f"{DESTINO} {len(linhas)} linhas")
    print(f"{RELATORIO}")


if __name__ == "__main__":
    main()
