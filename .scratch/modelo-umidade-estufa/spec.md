Status: ready-for-agent

## Problem Statement

O simulador deste trabalho ainda executa o exemplo do seno: um número sintético entra numa rede pequena e outro número sai no monitor serial. O estudante já tem um mês de leituras reais de umidade e quer ver, no mesmo simulador, a umidade da estufa prevista a partir da umidade da cidade.

## Solution

Treinar uma rede de uma entrada e uma saída com as leituras em que a fonte da umidade é a principal e o ar-condicionado está desligado. A entrada é a umidade da cidade, em porcentagem. A saída é a umidade da estufa, em porcentagem. O bloco final no tempo serve de prova. Se o erro médio absoluto desse bloco for grande demais para a faixa da estufa, o modelo do seno permanece. Se o erro couber na faixa, o modelo quantizado substitui o seno e o simulador varre a umidade da cidade, imprimindo a umidade prevista da estufa.

## User Stories

1. Como estudante da atividade, quero treinar o modelo só com as linhas cuja fonte de umidade é a principal e o ar-condicionado está desligado, para que o treino não misture leituras duplicadas nem o regime em que o quarto deixa de seguir o clima de fora.
2. Como estudante da atividade, quero que a entrada seja a umidade relativa do ar da cidade, em porcentagem, para que o simulador receba a mesma grandeza que o clima horário observado.
3. Como estudante da atividade, quero que a saída seja a umidade relativa do ar da estufa, em porcentagem, para que o serial mostre a grandeza que o sensor da estufa mede.
4. Como estudante da atividade, quero o corte entre treino e prova feito pelo tempo, com os primeiros 80% das linhas úteis no treino e os últimos 20% na prova, para que o modelo não veja o futuro da série.
5. Como estudante da atividade, quero a rede no mesmo formato do exemplo atual, duas camadas ocultas de 16 unidades com ativação ReLU e uma saída linear, treinada com erro quadrático médio, para que ela caiba no interpretador que só executa camada fully connected.
6. Como estudante da atividade, quero a entrada e a saída em porcentagem, para que o ciclo do firmware não precise mais percorrer o intervalo de 0 a 2π.
7. Como estudante da atividade, quero ver o erro médio absoluto da prova antes de trocar o modelo embutido, para que um modelo fraco não substitua o seno.
8. Como estudante da atividade, quero que o modelo não seja embutido quando o erro médio absoluto da prova passar de 10 pontos percentuais, para que a troca só ocorra quando o erro ainda é pequeno diante da faixa da estufa, cerca de 44% a 90%.
9. Como estudante da atividade, quero o modelo quantizado em inteiro de 8 bits, para que o firmware continue lendo e devolvendo um único inteiro de 8 bits.
10. Como estudante da atividade, quero o conjunto representativo da quantização feito com umidades reais da cidade do treino, para que a escala inteira cubra 48% a 99% e não o intervalo do seno.
11. Como estudante da atividade, quero o artefato quantizado convertido no array embutido no firmware, para que o simulador carregue o modelo novo no boot.
12. Como estudante da atividade, quero que a arena de tensores permaneça no tamanho atual, para que a rede do mesmo formato continue cabendo na memória já reservada.
13. Como estudante da atividade, quero que cada volta do simulador apresente uma umidade de cidade entre 48% e 99%, para que a demonstração percorra a faixa em que o modelo foi treinado.
14. Como estudante da atividade, quero ler no serial a umidade da cidade enviada e a umidade da estufa prevista, para que eu confira o par sem interpretar o eixo do seno.
15. Como estudante da atividade, quero ver previsões dentro da faixa observada da estufa, para que uma saída entre −1 e 1 denuncie que o modelo antigo ainda está no lugar.
16. Como estudante da atividade, quero a prova automática no modelo quantizado, não no modelo em ponto flutuante, para que o número aceito seja o mesmo tipo de conta que o ESP32 faz.
17. Como estudante da atividade, quero que linhas com o ar-condicionado ligado fiquem de fora do treino e da prova, para que o comportamento do quarto com o aparelho ligado não contamine a relação cidade–estufa.
18. Como estudante da atividade, quero que temperatura, chuva e déficit de pressão de vapor da cidade permaneçam no arquivo e fora da rede, para que a primeira versão use só umidade do ar.
19. Como estudante da atividade, quero o simulador só com a placa, sem sensor de umidade desenhado, para que a demonstração não dependa de um periférico que o simulador não mede.
20. Como estudante da atividade, quero repetir a varredura da umidade da cidade em ciclo, para que o serial continue produzindo uma sequência legível, como o exemplo do seno fazia.
21. Como estudante da atividade, quero que uma linha sem umidade da cidade ou sem umidade da estufa seja ignorada, para que um campo vazio não entre na conta.
22. Como estudante da atividade, quero que a ordem temporal do arquivo seja preservada no corte, para que embaralhar as linhas não vaze a prova para o treino.
23. Como estudante da atividade, quero o relatório da prova com a quantidade de linhas, o intervalo de datas e o erro médio absoluto, para que eu saiba qual fatia do mês foi julgada.

## Implementation Decisions

- O conjunto útil são as linhas cuja fonte de umidade é a principal e o ar-condicionado está desligado. Neste arquivo isso são 10.840 linhas, de 11/09/2026 00:00 a 28/09/2026 11:54, fuso −03:00. O treino vai até 24/09/2026 12:32 (8.672 linhas). A prova começa em 24/09/2026 12:34 (2.168 linhas).
- A entrada do treino é a coluna de umidade da cidade. A saída é a coluna de umidade da estufa. As duas ficam em porcentagem.
- A rede é regressão fully connected: 16 unidades ReLU, 16 unidades ReLU, 1 unidade linear, perda de erro quadrático médio.
- A quantização inteira de 8 bits usa como conjunto representativo valores de umidade da cidade tirados do treino, na faixa observada de 48% a 99%.
- O modelo substitui o que está embutido somente se o erro médio absoluto da prova, medido no modelo já quantizado, for de no máximo 10 pontos percentuais. Acima disso o seno permanece e o erro fica registrado.
- O ciclo do firmware deixa de gerar a posição no intervalo do seno. Cada inferência recebe uma umidade de cidade avançando pela faixa de 48% a 99%, e ao passar de 99% o ciclo recomeça em 48%.
- A quantização e a desquantização usam a escala e o zero do próprio tensor, como o laço atual já faz para um escalar.
- O log do serial nomeia os dois valores como umidade da cidade e umidade prevista da estufa.
- O diagrama do simulador continua apenas com a placa e o monitor serial.
- Temperatura da cidade, precipitação, déficit de pressão de vapor, umidade do quarto medida pelo ar-condicionado, setpoint e ventilação não entram nesta rede.

## Testing Decisions

Um bom teste olha o comportamento externo: dada a umidade da cidade de uma linha da prova, a umidade prevista da estufa se compara à umidade medida, e o resumo é o erro médio absoluto. Não se testa a ordem das camadas por dentro nem o texto do serial.

O único ponto de teste é a avaliação do modelo quantizado no bloco final do tempo, já filtrado. O teste falha se esse erro passar de 10 pontos percentuais. Não há suíte anterior no firmware para copiar. A leitura do monitor no simulador é conferência manual, fora desse teste.

## Out of Scope

- Incluir no modelo temperatura, chuva, déficit de pressão de vapor ou umidade do solo.
- Treinar ou provar com linhas em que o ar-condicionado está ligado, ou com linhas cuja fonte de umidade não é a principal.
- Aumentar o número de entradas da rede.
- Desenhar um sensor de umidade no simulador.
- Alterar o projeto FN Grow, o esquema do banco de leituras ou a coleta do clima.
- Trocar o kernel numérico do interpretador ou o tamanho da arena.
- Publicar o modelo se a prova quantizada estourar o limite de 10 pontos percentuais.

## Further Notes

A umidade da cidade é um valor horário repetido nas leituras de cerca de dois minutos. Vários alvos da estufa compartilham a mesma entrada. A rede aprende a umidade típica da estufa para cada umidade da cidade, não uma curva instantânea.

O estado real do ar-condicionado só existe numa minoria das linhas. Por isso o filtro usa a coluna de ligado, que está preenchida nas linhas principais, e não a umidade medida pelo próprio aparelho.
