# 02: Mostrar a umidade prevista da estufa no serial

**What to build:** Com a prova do modelo quantizado dentro do limite, o simulador deixa de varrer o seno e passa a varrer a umidade da cidade de 48% a 99%. O monitor serial imprime a umidade da cidade enviada e a umidade prevista da estufa. A previsão fica na faixa observada da estufa, não entre −1 e 1. O diagrama continua só com a placa.

**Blocked by:** 01: Provar o modelo quantizado no bloco final do tempo.

**Status:** ready-for-agent

- [ ] O modelo quantizado que passou na prova substitui o modelo do seno embutido no firmware.
- [ ] Cada inferência recebe uma umidade de cidade que avança de 48% a 99% e recomeça em 48%.
- [ ] O serial nomeia os dois valores como umidade da cidade e umidade prevista da estufa.
- [ ] A escala inteira de 8 bits usa a escala e o zero do próprio tensor.
- [ ] Este ticket não começa se o ticket 01 registrou erro acima de 10 pontos percentuais.

## Comments

Não iniciar. A prova do ticket 01 registrou erro médio absoluto 10,5499, acima de 10. O modelo do seno permanece.
