#ifndef LCD1602_H_
#define LCD1602_H_

// LCD 16x2 no I2C, GPIO4 (SDA) e GPIO5 (SCL), endereço 0x27.
bool lcd_iniciar(void);
void lcd_mostrar(float umidade_agora, float umidade_em_1h);
void lcd_avisar(const char* linha1, const char* linha2);

#endif
