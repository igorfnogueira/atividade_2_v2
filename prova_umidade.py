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


def provar(caminho: Path) -> Prova:
    linhas = _linhas_uteis(caminho)
    corte = int(len(linhas) * 0.8)
    treino = linhas[:corte]
    prova = linhas[corte:]
    modelo_quantizado, mae = _treinar_e_medir(treino, prova)
    resultado = Prova(
        linhas_treino=len(treino),
        linhas_prova=len(prova),
        inicio_prova=prova[0][0],
        fim_prova=prova[-1][0],
        mae=mae,
    )
    _registrar(resultado)
    if mae <= LIMITE_MAE:
        Path("umidade_int8.tflite").write_bytes(modelo_quantizado)
    return resultado


def _linhas_uteis(caminho: Path):
    linhas = []
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            if linha["fonte_umid"] != "principal":
                continue
            if linha["ac_ligado"].strip().lower() != "false":
                continue
            cidade = linha["umid_cidade_pct"].strip()
            estufa = linha["umid_estufa_pct"].strip()
            if not cidade or not estufa:
                continue
            linhas.append((linha["timestamp_iso"], float(cidade), float(estufa)))
    return linhas


def _rede():
    return tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(1,)),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(1),
        ]
    )


def _treinar_e_medir(treino, prova):
    tf.keras.utils.set_random_seed(7)
    entradas = np.array([[cidade] for _, cidade, _ in treino], dtype=np.float32)
    saidas = np.array([estufa for _, _, estufa in treino], dtype=np.float32)
    modelo = _rede()
    modelo.compile(optimizer="adam", loss="mse")
    modelo.fit(entradas, saidas, epochs=40, batch_size=64, shuffle=True, verbose=0)
    modelo_quantizado = _quantizar(modelo, entradas)
    return modelo_quantizado, _medir(modelo_quantizado, prova)


def _quantizar(modelo, entradas_treino) -> bytes:
    def amostras():
        passo = max(1, len(entradas_treino) // 500)
        for entrada in entradas_treino[::passo]:
            yield [entrada.reshape(1, 1)]

    conversor = tf.lite.TFLiteConverter.from_keras_model(modelo)
    conversor.optimizations = [tf.lite.Optimize.DEFAULT]
    conversor.representative_dataset = amostras
    conversor.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    conversor.inference_input_type = tf.int8
    conversor.inference_output_type = tf.int8
    return conversor.convert()


def _medir(modelo_quantizado: bytes, prova) -> float:
    interpretador = tf.lite.Interpreter(model_content=modelo_quantizado)
    interpretador.allocate_tensors()
    entrada = interpretador.get_input_details()[0]
    saida = interpretador.get_output_details()[0]
    escala_entrada, zero_entrada = entrada["quantization"]
    escala_saida, zero_saida = saida["quantization"]
    erros = []
    for _, cidade, estufa in prova:
        # O firmware converte com cast para int8, que corta em direção a zero.
        quantizado = int(np.trunc(cidade / escala_entrada + zero_entrada))
        quantizado = int(np.clip(quantizado, -128, 127))
        interpretador.set_tensor(
            entrada["index"], np.array([[quantizado]], dtype=np.int8)
        )
        interpretador.invoke()
        bruto = int(interpretador.get_tensor(saida["index"])[0][0])
        previsto = (bruto - zero_saida) * escala_saida
        erros.append(abs(previsto - estufa))
    return float(sum(erros) / len(erros))


def _registrar(prova: Prova) -> None:
    texto = (
        f"linhas_treino: {prova.linhas_treino}\n"
        f"linhas_prova: {prova.linhas_prova}\n"
        f"inicio_prova: {prova.inicio_prova}\n"
        f"fim_prova: {prova.fim_prova}\n"
        f"mae: {prova.mae:.4f}\n"
    )
    print(texto, end="")
    Path("prova_resultado.txt").write_text(texto, encoding="utf-8")
