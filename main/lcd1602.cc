#include "lcd1602.h"

#include <stdio.h>

#include "driver/i2c_master.h"
#include "esp_rom_sys.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

namespace {
constexpr i2c_port_num_t kPorta = 0;
constexpr gpio_num_t kSda = GPIO_NUM_4;
constexpr gpio_num_t kScl = GPIO_NUM_5;
constexpr uint8_t kEndereco = 0x27;
constexpr uint8_t kLuz = 0x08;
constexpr uint8_t kEnable = 0x04;
constexpr uint8_t kRs = 0x01;

i2c_master_dev_handle_t dispositivo = nullptr;

void escrever(uint8_t valor) {
  if (dispositivo == nullptr) {
    return;
  }
  uint8_t byte = valor | kLuz;
  i2c_master_transmit(dispositivo, &byte, 1, 50);
}

void pulso(uint8_t valor) {
  escrever(valor | kEnable);
  esp_rom_delay_us(1);
  escrever(valor & ~kEnable);
  esp_rom_delay_us(50);
}

void nibble(uint8_t nib, bool dado) {
  pulso((nib << 4) | (dado ? kRs : 0));
}

void byte_lcd(uint8_t valor, bool dado) {
  nibble(valor >> 4, dado);
  nibble(valor & 0x0F, dado);
}

void linha(int fileira, const char* texto) {
  byte_lcd(fileira == 0 ? 0x80 : 0xC0, false);
  char buf[17];
  snprintf(buf, sizeof(buf), "%-16.16s", texto);
  for (int i = 0; buf[i] != '\0'; ++i) {
    byte_lcd(static_cast<uint8_t>(buf[i]), true);
  }
}
}  // namespace

bool lcd_iniciar(void) {
  i2c_master_bus_config_t barramento = {};
  barramento.i2c_port = kPorta;
  barramento.sda_io_num = kSda;
  barramento.scl_io_num = kScl;
  barramento.clk_source = I2C_CLK_SRC_DEFAULT;
  barramento.glitch_ignore_cnt = 7;
  barramento.flags.enable_internal_pullup = true;

  i2c_master_bus_handle_t bus = nullptr;
  if (i2c_new_master_bus(&barramento, &bus) != ESP_OK) {
    return false;
  }

  i2c_device_config_t cfg = {};
  cfg.dev_addr_length = I2C_ADDR_BIT_LEN_7;
  cfg.device_address = kEndereco;
  cfg.scl_speed_hz = 100000;
  if (i2c_master_bus_add_device(bus, &cfg, &dispositivo) != ESP_OK) {
    return false;
  }

  vTaskDelay(pdMS_TO_TICKS(50));
  nibble(0x03, false);
  vTaskDelay(pdMS_TO_TICKS(5));
  nibble(0x03, false);
  esp_rom_delay_us(150);
  nibble(0x03, false);
  nibble(0x02, false);
  byte_lcd(0x28, false);
  byte_lcd(0x0C, false);
  byte_lcd(0x01, false);
  vTaskDelay(pdMS_TO_TICKS(2));
  byte_lcd(0x06, false);
  linha(0, "Lendo DHT22");
  linha(1, "");
  return true;
}

void lcd_mostrar(float umidade_agora, float umidade_em_1h) {
  char agora[17];
  char depois[17];
  snprintf(agora, sizeof(agora), "Agora %4.1f%%", umidade_agora);
  snprintf(depois, sizeof(depois), "Em 1h %4.1f%%", umidade_em_1h);
  linha(0, agora);
  linha(1, depois);
}

void lcd_avisar(const char* linha1, const char* linha2) {
  linha(0, linha1);
  linha(1, linha2);
}
