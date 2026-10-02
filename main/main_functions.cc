/* Copyright 2020 The TensorFlow Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/


#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/system_setup.h"
#include "tensorflow/lite/schema/schema_generated.h"

#include "main_functions.h"
#include "model.h"
#include "output_handler.h"
#include "dht22.h"
#include "lcd1602.h"

// Globals, used for compatibility with Arduino-style sketches.
namespace {
const tflite::Model* model = nullptr;
tflite::MicroInterpreter* interpreter = nullptr;
TfLiteTensor* input = nullptr;
TfLiteTensor* output = nullptr;

constexpr int kTensorArenaSize = 4096;
uint8_t tensor_arena[kTensorArenaSize];
}  // namespace

// The name of this function is important for Arduino compatibility.
void setup() {
  // Map the model into a usable data structure. This doesn't involve any
  // copying or parsing, it's a very lightweight operation.
  model = tflite::GetModel(g_model);
  MicroPrintf("g_model_len=%d", g_model_len);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    MicroPrintf("Model provided is schema version %d not equal to supported "
                "version %d.", model->version(), TFLITE_SCHEMA_VERSION);
    return;
  }

  // Pull in only the operation implementations we need.
  static tflite::MicroMutableOpResolver<1> resolver;
  if (resolver.AddFullyConnected() != kTfLiteOk) {
    return;
  }

  // Build an interpreter to run the model with.
  static tflite::MicroInterpreter static_interpreter(
      model, resolver, tensor_arena, kTensorArenaSize);
  interpreter = &static_interpreter;

  // Allocate memory from the tensor_arena for the model's tensors.
  TfLiteStatus allocate_status = interpreter->AllocateTensors();
  if (allocate_status != kTfLiteOk) {
    MicroPrintf("AllocateTensors() failed");
    return;
  }

  // Obtain pointers to the model's input and output tensors.
  input = interpreter->input(0);
  output = interpreter->output(0);
  MicroPrintf("arena_used=%d / %d",
              static_cast<int>(interpreter->arena_used_bytes()),
              kTensorArenaSize);
  MicroPrintf("in scale=%f zp=%d  out scale=%f zp=%d",
              static_cast<double>(input->params.scale), input->params.zero_point,
              static_cast<double>(output->params.scale),
              output->params.zero_point);

  MicroPrintf("Hello World trocado por umidade_int8.tflite");
  MicroPrintf("Treino: estufa_treino.csv, rede 16-16-1, int8");
  MicroPrintf("Na prova, a rede erra 2.55 pontos. Repetir a leitura erra 2.61.");
  MicroPrintf("DHT22 no GPIO6. Borda da luz = 0");
  dht22_iniciar();
  lcd_iniciar();
}

// The name of this function is important for Arduino compatibility.
void loop() {
  // A umidade vem do DHT22. A borda fica em 0: o Wokwi não tem o relé da luz.
  float umidade = 0.f;
  float temperatura = 0.f;
  if (!dht22_ler(&umidade, &temperatura)) {
    MicroPrintf("dht22 sem leitura");
    lcd_avisar("Sensor sem", "leitura");
    return;
  }
  const float borda = 0.f;

  // Quantize the input from floating-point to integer. O cast corta em
  // direção a zero, a mesma conta da prova no computador.
  int8_t umidade_quantizada =
      umidade / input->params.scale + input->params.zero_point;
  int8_t borda_quantizada =
      borda / input->params.scale + input->params.zero_point;
  input->data.int8[0] = umidade_quantizada;
  input->data.int8[1] = borda_quantizada;

  TfLiteStatus invoke_status = interpreter->Invoke();
  if (invoke_status != kTfLiteOk) {
    MicroPrintf("Invoke failed on umidade: %f\n",
                         static_cast<double>(umidade));
    return;
  }

  int8_t previsto_quantizado = output->data.int8[0];
  float previsto = (previsto_quantizado - output->params.zero_point) *
                   output->params.scale;

  HandleOutput(umidade, umidade_quantizada, previsto);
  lcd_mostrar(umidade, previsto);
}
