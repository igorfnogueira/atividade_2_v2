# atividade_2_v2

Firmware TensorFlow Lite Micro no ESP32-S3 (Wokwi) usando o modelo `hello_world_int8.tflite`, embutido em `main/model_data.cc`.

## Modelo

- Fonte: `hello_world_int8.tflite`
- Array C: `main/model_data.cc` (`g_model` / `g_model_len`)
- O build em `main/CMakeLists.txt` compila `model_data.cc` (não o `model.cc` oficial)
- Para regenerar o array: `python convert.py`

## Wokwi / ESP-NN

O Wokwi não simula o ESP-NN. Depois do primeiro `idf.py build` (quando existir `managed_components/`), comente esta linha em `managed_components/espressif__esp-tflite-micro/CMakeLists.txt` e faça rebuild limpo:

```cmake
# target_compile_options(${COMPONENT_LIB} PRIVATE -DESP_NN)
```

Sem isso, o `y` fica só negativo. Com o kernel de referência, o `y` oscila (positivo e negativo).

## Placa

ESP32-S3 DevKitC-1 (`diagram.json`, `sdkconfig.defaults`).
