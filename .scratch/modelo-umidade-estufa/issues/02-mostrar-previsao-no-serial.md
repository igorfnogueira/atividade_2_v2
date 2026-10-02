# 02: Mostrar a umidade prevista da estufa no serial

**What to build:** Com a prova do modelo quantizado de uma hora dentro do limite, melhor que repetir a leitura e com as 10h e as 16h melhores, o simulador varre a umidade da estufa e alterna o sinal da borda da luz. O monitor serial imprime a umidade atual, o sinal da borda e a umidade prevista para uma hora. A previsão fica na faixa observada da estufa, não entre −1 e 1. O diagrama continua só com a placa.

**Blocked by:** 01: Provar o modelo quantizado no bloco final do tempo.

**Status:** ready-for-agent

- [x] O modelo quantizado que passou na prova substitui o modelo do seno embutido no firmware.
- [x] Cada inferência avança a umidade da estufa (43,7% a 89,8% no treino) e recomeça no mínimo.
- [x] O serial nomeia a umidade atual da estufa, o sinal da borda da luz e a umidade prevista para uma hora.
- [x] A escala inteira de 8 bits usa a escala e o zero do próprio tensor.
- [x] Este ticket não começa se o ticket 01 registrou erro acima de 10 pontos percentuais ou pior que repetir a leitura.

## Comments

Prova com a borda pelo canal real: erro quantizado 2,5465 contra persistência 2,6126; nas horas em que a luz mudou, 4,6664 contra 5,2275. O modelo `umidade_int8.tflite` foi embutido em `main/model_data.cc`. O serial varre a umidade e alterna a borda.
