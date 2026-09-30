# 01: Provar o modelo quantizado no bloco final do tempo

**What to build:** A partir das leituras cuja fonte de umidade é a principal e o ar-condicionado está desligado, treinar a rede de uma entrada e uma saída, quantizá-la em inteiro de 8 bits e mostrar o erro médio absoluto da prova temporal. A entrada é a umidade da cidade, em porcentagem. A saída é a umidade da estufa, em porcentagem. Se esse erro passar de 10 pontos percentuais, o modelo do seno permanece e o erro fica registrado.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [x] O treino usa só linhas com fonte principal e ar desligado, em ordem de tempo: os primeiros 80% treinam e os últimos 20% provam.
- [x] A rede é regressão fully connected, duas camadas ocultas de 16 unidades com ReLU e uma saída linear, com perda de erro quadrático médio.
- [x] A quantização inteira de 8 bits usa umidades reais da cidade do treino como conjunto representativo, na faixa de 48% a 99%.
- [x] A prova mede o erro médio absoluto no modelo já quantizado e informa a quantidade de linhas, o intervalo de datas e o erro.
- [x] Quando o erro passa de 10 pontos percentuais, o modelo embutido do seno não é substituído.

## Comments

Prova em 30/09/2026: 8.672 linhas de treino, 2.168 de prova, de 2026-09-24T12:34:30-03:00 a 2026-09-28T11:54:18-03:00. Erro médio absoluto do modelo quantizado: 10,5499. Acima de 10. O modelo do seno permanece. O ticket 02 continua bloqueado.
