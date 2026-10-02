# Dados de umidade para o novo modelo

Pesquisa de fontes para treinar um modelo de umidade do ar e colocá-lo no firmware TensorFlow Lite Micro deste repositório. Cada afirmação abaixo aponta para a página que a sustenta.

## O que o firmware aceita

O firmware atual é o exemplo hello world, não um modelo de sensor. Em `main/main_functions.cc` o interpretador registra só `FullyConnected`, quantiza um escalar para `int8` e devolve um `int8`. O valor de entrada é sintético, de 0 a 2π (`kXrange` em `main/constants.h`).

O treino oficial dessa rede é regressão de um escalar para outro: `Dense(16, relu)` com `input_shape=(1,)`, outro `Dense(16, relu)` e `Dense(1)`, com perda `mse`. Fonte: [train.py do tflite-micro](https://github.com/tensorflow/tflite-micro/blob/main/tensorflow/lite/micro/examples/hello_world/train.py).

O teste do microcontrolador registra um único operador, `AddFullyConnected()`, e lê um elemento de entrada e um de saída. Fonte: [hello_world_test.cc](https://github.com/tensorflow/tflite-micro/blob/main/tensorflow/lite/micro/examples/hello_world/hello_world_test.cc).

O script de treino gera um modelo float. O `int8` é um segundo passo, `ptq.py`, que fixa `inference_input_type` e `inference_output_type` em `tf.int8` e usa um `representative_dataset` de 500 amostras no intervalo do seno, `[0, 2π]`. Fontes: [README](https://github.com/tensorflow/tflite-micro/blob/main/tensorflow/lite/micro/examples/hello_world/README.md) e [ptq.py](https://github.com/tensorflow/tflite-micro/blob/main/tensorflow/lite/micro/examples/hello_world/quantization/ptq.py).

Um modelo de umidade que entre no lugar deste, sem mudar a forma da rede, precisa continuar com um escalar na entrada, um escalar na saída e só camadas fully connected. O conjunto representativo da quantização tem de cobrir a faixa real de umidade (0–100%). O conjunto do seno não serve para calibrar essa escala.

## Recomendação

O treino sai do log próprio: mais de um mês de leituras já alinhadas no tempo. Dado público entra só para conferir ou completar a umidade do ar da cidade, no mesmo período e no mesmo lugar. Não substitui quarto, estufa nem solo.

O primeiro par que cabe nesta rede é umidade do ar da cidade (ou do quarto) na entrada e umidade do ar da estufa na saída, no mesmo instante. O rótulo tem de ser a estufa medida aqui. Temperatura fica de fora nesta versão.

Ordem de coleta, da fonte que mais parece o sensor local para a mais distante:

1. O log próprio (cidade, quarto, estufa).
2. INMET, estação automática mais próxima, mesma janela de tempo.
3. Open-Meteo, se a coleta for por coordenada.
4. NASA POWER, só como terceira conferência.

## Log próprio

Exporte só as colunas de umidade do ar (cidade, quarto, estufa), com o timestamp. Separe treino e teste por tempo, sem embaralhar linhas. Um mês em passo horário dá cerca de 720 pares. Se o sensor grava a cada poucos minutos, essa série é mais densa que qualquer API horária e é a que deve ir para o treino.

Umidade do solo fica de fora. Na Open-Meteo, umidade do ar é `%` (`relative_humidity_2m`) e umidade do solo é teor volumétrico em `m³/m³` (`soil_moisture_*`). Fonte: [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api). O sensor de solo local não está nessa escala.

## INMET

Dado medido em estação automática, público e gratuito. Os valores das automáticas são brutos, sem validação. Falha pode aparecer como `9999`, `Null` ou vazio. O horário é UTC; para o horário de Brasília, subtrair 3 horas. Fonte: [como acessar os dados no site do INMET](https://portal.inmet.gov.br/noticias/saiba-como-acessar-os-dados-meteorologicos-disponiveis-no-site-do-inmet).

Pacotes anuais de todas as estações automáticas: [dados históricos](https://portal.inmet.gov.br/dadoshistoricos). Essa página não nomeia a coluna de umidade.

Pedido de uma estação em CSV, por e-mail: [BDMEP](https://bdmep.inmet.gov.br/). O cartão de serviço do gov.br descreve o BDMEP de forma mais estreita, como séries diárias de estações convencionais, atualizadas a cada 90 dias: [BDMEP — dados históricos](https://portal.inmet.gov.br/servicos/bdmep-dados-historicos).

No catálogo de atributos da estação automática, a variável horária é o código `I105`, “UMIDADE RELATIVA DO AR, HORARIA”, periodicidade horária, unidade `%`, classe Umidade, “Dado Observado”. Fonte: [atributos A301/H](https://apitempo.inmet.gov.br/BNDMET/atributos/A301/H). Máxima e mínima da hora anterior são outros códigos (`I617` e `I618`). A média diária automática é `I120`, “UMIDADE RELATIVA DO AR, MEDIA DIARIA (AUT)”: [atributos A301/D](https://apitempo.inmet.gov.br/BNDMET/atributos/A301/D).

Uma estação automática integra observações minuto a minuto e publica a cada hora; o conjunto de sensores inclui umidade relativa do ar. Fonte: [boletim informativo 76 do INMET](https://portal.inmet.gov.br/uploads/boletinsinmet/boletimInformativo_76.pdf) (PDF).

Não foi encontrada uma página de licença no estilo CC. O uso, segundo a notícia do portal, é de responsabilidade de quem baixa os dados.

O cabeçalho dentro do ZIP anual não foi aberto. Não está confirmado que esses arquivos usem o rótulo `I105`. As normais climatológicas em [portal.inmet.gov.br/normais](https://portal.inmet.gov.br/normais) são normais, não a série bruta.

## Open-Meteo

Endpoint histórico: `GET https://archive-api.open-meteo.com/v1/archive` com `hourly=relative_humidity_2m`. O valor é instantâneo, em `%`, a 2 m acima do solo. A resolução horária da interface usa ERA5, ERA5-Land e ECMWF IFS (o ensemble ERA5 é de 3 horas). Fonte: [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api).

A chave (`apikey`) só é exigida para uso comercial. Uso não comercial é HTTP GET sem chave, até 10.000 chamadas por dia, sob CC BY 4.0, com atribuição. Fontes: a mesma página da API, [termos](https://open-meteo.com/en/terms) e a [página inicial](https://open-meteo.com/).

É reanálise em grade, não a leitura da estação do INMET. A [licença](https://open-meteo.com/en/licence) pede crédito e um link para Open-Meteo quando o dado é exibido. Os conjuntos de origem têm licenças próprias (várias CC-BY, Met Office em CC-BY-SA, reanálise do Copernicus).

Peça só `relative_humidity_2m`. Não use `soil_moisture_*` neste treino.

Controles diários com ids `relative_humidity_2m_mean_daily`, `relative_humidity_2m_max_daily` e `relative_humidity_2m_min_daily` aparecem na interface, mas a tabela “Daily Parameter Definition” não os lista. Não assuma que o sufixo `_daily` seja o token de `&daily=`.

## NASA POWER

`RH2M` é “Relative Humidity at 2 Meters”, unidade `%`. A unidade foi lida no cabeçalho de uma resposta horária com `community=AG`, sem chave: [exemplo de um dia em São Paulo](https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=RH2M&community=AG&longitude=-46.63&latitude=-23.55&start=20240101&end=20240101&format=JSON).

A API horária devolve média por hora. O padrão de endpoint é `/api/temporal/hourly/point`. O fuso padrão é LST; UTC pede `time-standard=UTC`. Fonte: [Hourly API](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/).

A comunidade de agroclimatologia é `AG`. A meteorologia dessa comunidade está disponível como média diária, e a série horária inclui os parâmetros meteorológicos básicos. Fonte: [communities](https://power.larc.nasa.gov/docs/methodology/communities/).

A umidade relativa é calculada a partir de pressão, temperatura de bulbo seco e razão de mistura do MERRA-2. É estimativa a 2 m, em porcentagem, não leitura de estação. Fonte: [metodologia de umidade relativa](https://power.larc.nasa.gov/docs/methodology/meteorology/relative-humidity/).

Não há autenticação: “All endpoints are publicly accessible with no authentication.” Fonte: [llms.txt do POWER](https://power.larc.nasa.gov/llms.txt).

Em publicação, citar a referência do serviço e a referência dos dados (nome do serviço, versão e data de acesso). Exemplo indicado pelo projeto: “The data was obtained from the POWER Project's Hourly 2.x.x version on YYYY/MM/DD.” Fonte: [referencing](https://power.larc.nasa.gov/docs/referencing/).

A grade é grosseira (cerca de 0,5° na meteorologia). Serve como terceira conferência da cidade, não como substituto do INMET nem do sensor local.

## O que não usar como treino deste ESP32

A série do 4º Autonomous Greenhouse Challenge foi coletada num compartimento de pesquisa de 96 m² nas instalações experimentais de Bleiswijk, com clima a cada 5 minutos e seis compartimentos controlados à distância por equipes do desafio. Não é uma estufa doméstica. Fonte: [dataset da Wageningen](https://research.wur.nl/en/datasets/4th-autonomous-greenhouse-challenge-dwarf-tomato-timeseries-and-i/).

Produto de satélite de umidade do solo também não entra no lugar da umidade relativa do ar. São variáveis diferentes.
