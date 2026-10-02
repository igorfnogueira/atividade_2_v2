Status: ready-for-agent

## Problem Statement

O simulador deste trabalho executava o exemplo do seno: um número sintético entra numa rede pequena e outro número sai no monitor serial. O estudante já tem um mês de leituras reais de umidade da estufa e quer ver, no mesmo simulador, a umidade prevista para uma hora à frente a partir da umidade atual de dentro.

## Solution

Treinar uma rede de duas entradas e uma saída com as leituras limpas de `estufa_treino.csv`. A primeira entrada é a umidade atual da estufa. A segunda é o sinal da borda da luz calculado pelo canal real: −1 se a quantum board apaga na hora seguinte, +1 se acende, 0 se não muda. A saída é a umidade da estufa uma hora depois, em porcentagem. O bloco final no tempo serve de prova. O modelo quantizado substitui o anterior somente se o erro médio absoluto desse bloco for de no máximo 10 pontos percentuais, não for pior do que repetir a leitura atual, e reduzir o erro nas horas em que a luz realmente muda. O simulador varre a faixa de umidade vista no treino, alterna o sinal da borda e imprime a previsão de uma hora.

## User Stories

1. Como estudante da atividade, quero treinar o modelo só com as linhas cuja fonte de umidade é a principal e o ar-condicionado está desligado, para que o treino não misture leituras duplicadas nem o regime em que o quarto deixa de seguir o clima de fora.
2. Como estudante da atividade, quero que as entradas sejam a umidade atual da estufa e o sinal da borda da luz, e a saída seja a umidade uma hora depois, para que o modelo antecipe a queda das 16h e a subida das 10h.
3. Como estudante da atividade, quero que a saída seja a umidade relativa do ar da estufa, em porcentagem, para que o serial mostre a grandeza que o sensor da estufa mede.
4. Como estudante da atividade, quero o corte entre treino e prova feito pelo tempo, com os primeiros 80% das linhas úteis no treino e os últimos 20% na prova, para que o modelo não veja o futuro da série.
5. Como estudante da atividade, quero a rede no mesmo formato do exemplo atual, duas camadas ocultas de 16 unidades com ativação ReLU e uma saída linear, treinada com erro quadrático médio, para que ela caiba no interpretador que só executa camada fully connected.
6. Como estudante da atividade, quero a entrada e a saída em porcentagem, para que o ciclo do firmware não precise mais percorrer o intervalo de 0 a 2π.
7. Como estudante da atividade, quero ver o erro médio absoluto da prova antes de trocar o modelo embutido, para que um modelo fraco não substitua o seno.
8. Como estudante da atividade, quero que o modelo não seja embutido quando o erro médio absoluto da prova passar de 10 pontos percentuais, quando for pior do que repetir a leitura atual, ou quando as horas em que a luz muda não melhorarem, para que a troca só ocorra quando o erro das bordas da luz diminui.
9. Como estudante da atividade, quero o modelo quantizado em inteiro de 8 bits, para que o firmware leia dois inteiros de entrada e devolva um inteiro de saída.
10. Como estudante da atividade, quero o conjunto representativo da quantização feito com umidades reais da estufa do treino, para que a escala inteira cubra essa faixa e não o intervalo do seno.
11. Como estudante da atividade, quero o artefato quantizado convertido no array embutido no firmware, para que o simulador carregue o modelo novo no boot.
12. Como estudante da atividade, quero que a arena de tensores permaneça no tamanho atual, para que a rede do mesmo formato continue cabendo na memória já reservada.
13. Como estudante da atividade, quero que cada volta do simulador avance a umidade da estufa na faixa vista no treino, para que a demonstração percorra a entrada do modelo.
14. Como estudante da atividade, quero ler no serial a umidade atual da estufa, o sinal da borda da luz e a umidade prevista para uma hora, para que eu confira o trio sem interpretar o eixo do seno.
15. Como estudante da atividade, quero ver previsões dentro da faixa observada da estufa, para que uma saída entre −1 e 1 denuncie que o modelo antigo ainda está no lugar.
16. Como estudante da atividade, quero a prova automática no modelo quantizado, não no modelo em ponto flutuante, para que o número aceito seja o mesmo tipo de conta que o ESP32 faz.
17. Como estudante da atividade, quero que linhas com o ar-condicionado ligado fiquem de fora do treino e da prova, para que a série de uma hora use o mesmo recorte das provas anteriores.
18. Como estudante da atividade, quero que cidade, quarto, chuva, déficit de pressão de vapor e umidade do solo permaneçam fora da rede, para que a segunda entrada seja só o sinal da borda da luz.
19. Como estudante da atividade, quero o simulador só com a placa, sem sensor de umidade desenhado, para que a demonstração não dependa de um periférico que o simulador não mede.
20. Como estudante da atividade, quero repetir a varredura da umidade da estufa em ciclo, para que o serial continue produzindo uma sequência legível, como o exemplo do seno fazia.
21. Como estudante da atividade, quero que uma linha sem umidade da estufa seja ignorada, para que um campo vazio não entre na conta.
22. Como estudante da atividade, quero que a ordem temporal do arquivo seja preservada no corte, para que embaralhar as linhas não vaze a prova para o treino.
23. Como estudante da atividade, quero o relatório da prova com a quantidade de linhas, o intervalo de datas e o erro médio absoluto, para que eu saiba qual fatia do mês foi julgada.

## Implementation Decisions

- O conjunto útil são as linhas cuja fonte de umidade é a principal e o ar-condicionado está desligado. O par de uma hora usa a primeira leitura com pelo menos 60 minutos de diferença e no máximo 75, para que um buraco da série não vire rótulo de uma hora. O corte continua nos primeiros 80% das linhas úteis. O alvo de um par de treino fica antes desse corte. A prova são os pares cuja entrada está no bloco final.
- As entradas são a umidade atual da estufa, em porcentagem, e o sinal da borda da luz (−1, 0 ou +1) calculado pelo canal `luz_ligada` entre a leitura e a leitura de uma hora depois. A saída é a umidade da estufa uma hora depois, em porcentagem.
- A rede é regressão fully connected: 16 unidades ReLU, 16 unidades ReLU, 1 unidade linear, perda de erro quadrático médio. Não há busca de hiperparâmetros.
- A quantização inteira de 8 bits usa como conjunto representativo pares de umidade da estufa e sinal da borda tirados do treino. No treino a umidade vai de 43,7% a 89,8%.
- O modelo substitui o que está embutido somente se o erro médio absoluto da prova, medido no modelo já quantizado, for de no máximo 10 pontos percentuais, não for pior do que repetir a leitura atual, e o erro nas horas em que a luz muda cair. Fora disso o modelo anterior permanece.
- O ciclo do firmware deixa de gerar a posição no intervalo do seno. Cada inferência avança a umidade da estufa na faixa do treino e alterna o sinal da borda, e recomeça no mínimo.
- A quantização e a desquantização usam a escala e o zero do próprio tensor. O corte do inteiro é em direção a zero.
- O log do serial nomeia a umidade atual da estufa, o sinal da borda da luz e a umidade prevista para uma hora.
- O diagrama do simulador continua apenas com a placa e o monitor serial.
- Cidade, quarto, precipitação, déficit de pressão de vapor, umidade do solo, setpoint e ventilação não entram nesta rede.
- A prova de 01/10/2026 com a borda pelo canal real, em `estufa_treino.csv`, registrou erro quantizado de 2,5465, contra 2,6126 de repetir a leitura. Nas horas em que a luz mudou, o erro foi 4,6664, contra 5,2275. O modelo foi embutido.

## Testing Decisions

Um bom teste olha o comportamento externo: dadas a umidade atual da estufa e o sinal da borda de um par da prova, a umidade prevista para uma hora se compara à umidade medida, e o resumo é o erro médio absoluto. Não se testa a ordem das camadas por dentro nem o texto do serial. Não se varre hiperparâmetro.

O único ponto de teste é a avaliação do modelo quantizado no bloco final do tempo, já filtrado. O teste falha se esse erro passar de 10 pontos percentuais, se for pior do que repetir a leitura atual, ou se as horas em que a luz muda não melhorarem. Não há suíte anterior no firmware para copiar. A leitura do monitor no simulador é conferência manual, fora desse teste.

## Out of Scope

- Incluir no modelo chuva, déficit de pressão de vapor ou umidade do solo.
- Treinar ou provar com linhas em que o ar-condicionado está ligado, ou com linhas cuja fonte de umidade não é a principal.
- Buscar camadas, épocas ou taxa de aprendizado olhando a prova.
- Desenhar um sensor de umidade no simulador.
- Alterar o projeto FN Grow, o esquema do banco de leituras ou a coleta do clima.
- Trocar o kernel numérico do interpretador ou o tamanho da arena.
- Publicar o modelo se a prova quantizada estourar o limite de 10 pontos percentuais, se o erro for pior do que repetir a leitura atual, ou se as horas em que a luz muda não melhorarem.

## Further Notes

Prever a estufa no mesmo instante a partir da cidade não coube no limite: só a umidade da cidade errou 10,55; com a temperatura da cidade, 14,55; com a temperatura do SHT31 do quarto, 14,51. A prova de uma hora só com a umidade da estufa errou 2,1198, contra 2,1491 de repetir a leitura. Com a borda calculada pelo canal real da luz, o erro quantizado foi 2,5465 no geral e 4,6664 nas horas em que a luz mudou, contra 2,6126 e 5,2275 de repetir a leitura. Esse modelo foi embutido.

O estado real do ar-condicionado só existe numa minoria das linhas. Por isso o filtro usa a coluna de ligado, que está preenchida nas linhas principais, e não a umidade medida pelo próprio aparelho.
