# 01: Provar o modelo quantizado no bloco final do tempo

**What to build:** A partir das leituras cuja fonte de umidade é a principal e o ar-condicionado está desligado, treinar a rede de uma entrada e uma saída para prever a umidade da estufa uma hora à frente, quantizá-la em inteiro de 8 bits e mostrar o erro médio absoluto da prova temporal. A entrada é a umidade atual da estufa. A saída é a umidade uma hora depois. O modelo do seno permanece se o erro passar de 10 pontos percentuais ou se for pior do que repetir a leitura atual.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [x] O treino usa só linhas com fonte principal e ar desligado, em ordem de tempo: os primeiros 80% treinam e os últimos 20% provam.
- [x] A rede é regressão fully connected, duas camadas ocultas de 16 unidades com ReLU e uma saída linear, com perda de erro quadrático médio.
- [x] A quantização inteira de 8 bits usa umidades reais da estufa do treino como conjunto representativo, na faixa de 43,7% a 89,8%.
- [x] A prova mede o erro médio absoluto no modelo já quantizado e informa a quantidade de linhas, o intervalo de datas e o erro.
- [x] Quando o erro passa de 10 pontos percentuais, ou fica pior do que repetir a leitura atual, o modelo embutido do seno não é substituído.

## Comments

Provas anteriores, no mesmo instante, ficaram acima de 10: só a cidade 10,5499; cidade e temperatura da cidade 14,5493; cidade e temperatura do SHT31 14,5149. Prova de uma hora só com a umidade: erro quantizado 2,1198, persistência 2,1491. Prova com a borda pelo canal real da luz, depois do ETL: erro quantizado 2,5465 contra persistência 2,6126. Nas horas em que a luz mudou, 4,6664 contra 5,2275. O modelo foi embutido.
