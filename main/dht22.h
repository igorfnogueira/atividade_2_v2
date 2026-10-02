#ifndef DHT22_H_
#define DHT22_H_

#include <stdbool.h>

// GPIO6. O Wokwi entrega a umidade que está no DHT22, não o CSV.
void dht22_iniciar(void);
bool dht22_ler(float* umidade_pct, float* temperatura_c);

#endif
