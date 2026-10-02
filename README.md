# atividade_2_v2

Firmware TensorFlow Lite Micro no ESP32-S3 (Wokwi) usando o modelo `umidade_int8.tflite`, embutido em `main/model_data.cc`. O DHT22 no GPIO6 é a umidade de agora. A borda da luz fica em 0, porque o simulador não tem o relé. A saída é a umidade prevista para uma hora, no serial e no LCD. O CSV da estufa treinou o modelo; o slider do DHT22 só muda a leitura ao vivo. O valor inicial do sensor é 63% e 24 °C.

## Modelo

- Fonte: `umidade_int8.tflite`
- Array C: `main/model_data.cc` (`g_model` / `g_model_len`)
- O build em `main/CMakeLists.txt` compila `model_data.cc` (não o `model.cc` oficial)
- Para regenerar o array: `python convert.py`

## Wokwi / ESP-NN

O Wokwi não simula o ESP-NN. Depois do primeiro `idf.py build` (quando existir `managed_components/`), comente esta linha em `managed_components/espressif__esp-tflite-micro/CMakeLists.txt` e faça rebuild limpo:

```cmake
# target_compile_options(${COMPONENT_LIB} PRIVATE -DESP_NN)
```

Sem isso, a saída fica só negativa. Com o kernel de referência, a umidade prevista fica na faixa da estufa.

## Placa

ESP32-S3 DevKitC-1 (`diagram.json`, `sdkconfig.defaults`).
