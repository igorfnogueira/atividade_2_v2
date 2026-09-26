import os

tflite_file = "hello_world_int8.tflite"
output_file = "main/model_data.cc"

with open(tflite_file, "rb") as f:
    data = f.read()

hex_array = ", ".join(f"0x{b:02x}" for b in data)

content = f"""#include "model.h"

alignas(8) const unsigned char g_model[] = {{
    {hex_array}
}};

const int g_model_len = sizeof(g_model);
"""

os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(output_file, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Sucesso! Arquivo gerado em {output_file} com {len(data)} bytes.")