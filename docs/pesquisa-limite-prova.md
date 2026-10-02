# Prova do modelo de umidade e o limite 10

O que decide se a umidade da estufa entra no ESP32 no lugar do seno, e o que significa falhar em 10. Cada afirmação aponta para o arquivo ou a página que a sustenta.

## O processo

O conjunto útil são as linhas em que `fonte_umid` é `principal` e o ar-condicionado está desligado (`ac_ligado` igual a `false`). Linha sem umidade da cidade, sem temperatura da cidade ou sem umidade da estufa fica de fora. A ordem do arquivo é a ordem do tempo. Fontes: `_linhas_uteis` em `prova_umidade.py` e `.scratch/modelo-umidade-estufa/spec.md`.

O corte é temporal. O treino são os primeiros 80% das linhas úteis. A prova são os últimos 20%. Nesta série isso são 8.672 linhas de treino e 2.168 de prova. A prova vai de 2026-09-24T12:34:30-03:00 a 2026-09-28T11:54:18-03:00. Fontes: o corte `int(len(linhas) * 0.8)` em `prova_umidade.py`, a contagem e as datas em `prova_resultado.txt`, e o mesmo recorte na spec (treino até 24/09/2026 12:32, prova a partir de 24/09/2026 12:34).

A rede que `provar` treina tem duas entradas, a umidade relativa da cidade em porcentagem e a temperatura da cidade em graus Celsius, e uma saída, a umidade da estufa em porcentagem. São duas camadas ocultas de 16 unidades com ReLU e uma saída linear. O treino usa perda de erro quadrático médio. Em seguida o modelo é quantizado para inteiro de 8 bits, com pares reais de umidade e temperatura da cidade do treino como conjunto representativo. O erro aceito é o do modelo já quantizado. Fontes: `_rede`, `compile(..., loss="mse")`, `_quantizar` e `_medir` em `prova_umidade.py`, e a spec.

Se esse erro for de no máximo 10, `provar` grava `umidade_int8.tflite`. Acima de 10 o arquivo não é escrito e o modelo do seno permanece. Fontes: `LIMITE_MAE` e `if mae <= LIMITE_MAE` em `prova_umidade.py`, e a spec.

O firmware ainda alimenta a rede com uma varredura sintética. Em `loop`, a entrada é um escalar, `position * kXrange`, quantizado para um único `int8`. Esse arquivo não lê sensor de umidade. Fonte: `main/main_functions.cc`.

## O que é o erro médio absoluto

É a média de |umidade prevista da estufa menos umidade medida da estufa|, em pontos percentuais. No Keras, `MeanAbsoluteError` é `mean(abs(y_true - y_pred))`. Fonte: [métricas de regressão do Keras](https://keras.io/api/metrics/regression_metrics/). O número desta prova é a mesma conta feita à mão em `_medir`: a soma de `|previsto - estufa|` dividida pela quantidade de linhas da prova. O script não chama essa API. A perda do treino continua sendo `mse`.

## O que o 10 significa

O 10 é o teto escrito na spec: o erro médio absoluto da prova, no modelo já quantizado, tem de ser de no máximo 10 pontos percentuais. Acima disso o seno permanece, porque o erro deixou de ser pequeno diante da faixa da estufa, cerca de 44% a 90%. Fonte: `.scratch/modelo-umidade-estufa/spec.md` (histórias 8 e 16, decisões de implementação e de teste). `LIMITE_MAE = 10.0` em `prova_umidade.py` repete esse teto. Não é constante do TensorFlow.

## O que a última prova mediu

Com só a umidade da cidade, o modelo quantizado errou 10,5499. Com umidade e temperatura da cidade, errou 14,5493. Os dois ficam acima de 10, então o seno permanece. Fontes: o comentário em `.scratch/modelo-umidade-estufa/issues/01-provar-modelo-quantizado.md` e `prova_resultado.txt`, que registra `mae: 14.5493` para as duas entradas. A spec arredonda a rede de uma entrada para 10,55 e repete 14,5493.

O firmware segue na varredura sintética de `main/main_functions.cc`.
