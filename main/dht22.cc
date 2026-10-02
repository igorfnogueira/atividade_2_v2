#include "dht22.h"

#include "driver/gpio.h"
#include "esp_rom_sys.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

namespace {
constexpr gpio_num_t kPino = GPIO_NUM_6;
portMUX_TYPE leitura = portMUX_INITIALIZER_UNLOCKED;

int espera_nivel(int nivel, int limite_us) {
  int decorrido = 0;
  while (gpio_get_level(kPino) != nivel) {
    if (decorrido >= limite_us) {
      return -1;
    }
    esp_rom_delay_us(1);
    decorrido += 1;
  }
  return decorrido;
}
}  // namespace

void dht22_iniciar(void) {
  gpio_config_t io = {};
  io.pin_bit_mask = 1ULL << kPino;
  io.mode = GPIO_MODE_INPUT_OUTPUT_OD;
  io.pull_up_en = GPIO_PULLUP_ENABLE;
  io.pull_down_en = GPIO_PULLDOWN_DISABLE;
  io.intr_type = GPIO_INTR_DISABLE;
  gpio_config(&io);
  gpio_set_level(kPino, 1);
  // O DHT22 precisa de cerca de 2 s depois de ligar antes da primeira leitura.
  vTaskDelay(pdMS_TO_TICKS(2000));
}

bool dht22_ler(float* umidade_pct, float* temperatura_c) {
  gpio_set_level(kPino, 0);
  esp_rom_delay_us(18000);
  gpio_set_level(kPino, 1);
  esp_rom_delay_us(40);

  uint8_t dados[5] = {};
  taskENTER_CRITICAL(&leitura);
  bool ok = espera_nivel(0, 200) >= 0 && espera_nivel(1, 200) >= 0 &&
            espera_nivel(0, 200) >= 0;
  for (int bit = 0; ok && bit < 40; ++bit) {
    if (espera_nivel(1, 100) < 0) {
      ok = false;
      break;
    }
    int alto = espera_nivel(0, 120);
    if (alto < 0) {
      ok = false;
      break;
    }
    dados[bit / 8] = (dados[bit / 8] << 1) | (alto > 40 ? 1 : 0);
  }
  taskEXIT_CRITICAL(&leitura);
  gpio_set_level(kPino, 1);

  if (!ok) {
    return false;
  }
  uint8_t soma = dados[0] + dados[1] + dados[2] + dados[3];
  if (soma != dados[4]) {
    return false;
  }

  *umidade_pct = ((dados[0] << 8) | dados[1]) / 10.0f;
  int temperatura = ((dados[2] & 0x7F) << 8) | dados[3];
  if (dados[2] & 0x80) {
    temperatura = -temperatura;
  }
  *temperatura_c = temperatura / 10.0f;
  return true;
}
