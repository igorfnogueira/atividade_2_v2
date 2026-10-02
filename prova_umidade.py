import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import tensorflow as tf

LIMITE_MAE = 10.0


@dataclass(frozen=True)
class Prova:
    linhas_treino: int
    linhas_prova: int
    inicio_prova: str
    fim_prova: str
    mae: float
    persistencia: float
    mae_borda: float
    persistencia_borda: float


def provar(caminho: Path) -> Prova:
    pares = _pares(caminho)
    corte = int(len(pares) * 0.8)
    limite = pares[corte].entrada_iso
    treino = [par for par in pares if par.alvo_iso < limite]
    prova = [par for par in pares if par.entrada_iso >= limite]
    modelo_quantizado, erros = _treinar_e_medir(treino, prova)
    resultado = Prova(
        linhas_treino=len(treino),
        linhas_prova=len(prova),
        inicio_prova=prova[0].entrada_iso,
        fim_prova=prova[-1].alvo_iso,
        mae=_media(erros),
        persistencia=_persistencia(prova),
        mae_borda=_media_borda(prova, erros),
        persistencia_borda=_persistencia_borda(prova),
    )
    _registrar(resultado, _faixa_treino(treino))
    if _passa(resultado):
        Path("umidade_int8.tflite").write_bytes(modelo_quantizado)
    return resultado


def _passa(prova: Prova) -> bool:
    return (
        prova.mae <= LIMITE_MAE
        and prova.mae <= prova.persistencia
        and prova.mae_borda < prova.persistencia_borda
    )


@dataclass(frozen=True)
class _Par:
    entrada_iso: str
    alvo_iso: str
    entrada: float
    alvo: float
    borda: float
    indice_entrada: int
    indice_alvo: int


def _pares(caminho: Path):
    pares = []
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        for indice, linha in enumerate(csv.DictReader(arquivo)):
            if not linha["umid_em_1h"].strip() or linha["borda"] == "":
                continue
            pares.append(
                _Par(
                    linha["timestamp_iso"],
                    linha["alvo_iso"],
                    float(linha["umid_estufa_pct"]),
                    float(linha["umid_em_1h"]),
                    float(linha["borda"]),
                    indice,
                    indice,
                )
            )
    return pares


def _rede():
    return tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(2,)),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(1),
        ]
    )


def _treinar_e_medir(treino, prova):
    tf.keras.utils.set_random_seed(7)
    entradas = np.array(
        [[par.entrada, par.borda] for par in treino],
        dtype=np.float32,
    )
    saidas = np.array([par.alvo for par in treino], dtype=np.float32)
    modelo = _rede()
    modelo.compile(optimizer="adam", loss="mse")
    modelo.fit(entradas, saidas, epochs=40, batch_size=64, shuffle=True, verbose=0)
    modelo_quantizado = _quantizar(modelo, entradas)
    return modelo_quantizado, _medir(modelo_quantizado, prova)


def _quantizar(modelo, entradas_treino) -> bytes:
    def amostras():
        passo = max(1, len(entradas_treino) // 500)
        for entrada in entradas_treino[::passo]:
            yield [entrada.reshape(1, 2)]

    conversor = tf.lite.TFLiteConverter.from_keras_model(modelo)
    conversor.optimizations = [tf.lite.Optimize.DEFAULT]
    conversor.representative_dataset = amostras
    conversor.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    conversor.inference_input_type = tf.int8
    conversor.inference_output_type = tf.int8
    return conversor.convert()


def _medir(modelo_quantizado: bytes, prova) -> list[float]:
    interpretador = tf.lite.Interpreter(model_content=modelo_quantizado)
    interpretador.allocate_tensors()
    entrada = interpretador.get_input_details()[0]
    saida = interpretador.get_output_details()[0]
    escala_entrada, zero_entrada = entrada["quantization"]
    escala_saida, zero_saida = saida["quantization"]
    erros = []
    for par in prova:
        # O firmware converte com cast para int8, que corta em direção a zero.
        umidade_q = _para_int8(par.entrada, escala_entrada, zero_entrada)
        borda_q = _para_int8(par.borda, escala_entrada, zero_entrada)
        interpretador.set_tensor(
            entrada["index"],
            np.array([[umidade_q, borda_q]], dtype=np.int8),
        )
        interpretador.invoke()
        bruto = int(interpretador.get_tensor(saida["index"])[0][0])
        previsto = (bruto - zero_saida) * escala_saida
        erros.append(abs(previsto - par.alvo))
    return erros


def _media(valores) -> float:
    return float(sum(valores) / len(valores))


def _persistencia(prova) -> float:
    return _media([abs(par.alvo - par.entrada) for par in prova])


def _media_borda(prova, erros) -> float:
    escolhidos = [erro for par, erro in zip(prova, erros) if par.borda != 0]
    return _media(escolhidos)


def _persistencia_borda(prova) -> float:
    return _media(
        [abs(par.alvo - par.entrada) for par in prova if par.borda != 0]
    )


def _para_int8(valor: float, escala: float, zero: float) -> int:
    return int(np.clip(np.trunc(valor / escala + zero), -128, 127))


def _faixa_treino(treino):
    umidades = [par.entrada for par in treino]
    return min(umidades), max(umidades)


def _registrar(prova: Prova, faixa) -> None:
    umidade_min, umidade_max = faixa
    texto = (
        f"linhas_treino: {prova.linhas_treino}\n"
        f"linhas_prova: {prova.linhas_prova}\n"
        f"inicio_prova: {prova.inicio_prova}\n"
        f"fim_prova: {prova.fim_prova}\n"
        f"mae: {prova.mae:.4f}\n"
        f"persistencia: {prova.persistencia:.4f}\n"
        f"mae_borda: {prova.mae_borda:.4f}\n"
        f"persistencia_borda: {prova.persistencia_borda:.4f}\n"
        f"umidade_treino_min: {umidade_min}\n"
        f"umidade_treino_max: {umidade_max}\n"
    )
    print(texto, end="")
    Path("prova_resultado.txt").write_text(texto, encoding="utf-8")
