// Arduino Nano код для скидання PF-флагу Renesas 045A20 (SMBus)
#include <Wire.h>

#define MAX_ADDRESS 0x7F

void setup() {
  Wire.begin();
  Serial.begin(9600);
  delay(1000);

  Serial.println("?? Сканування I2C/SMBus пристроїв...");
  byte addr = detectBatteryChip();

  if (addr == 0xFF) {
    Serial.println("? Чип батареї не знайдено.");
    return;
  }

  Serial.print("? Знайдено пристрій на адресі 0x");
  Serial.println(addr, HEX);

  readBatteryInfo(addr);
  checkAndResetPF(addr);
}

void loop() {}

// Виявлення батареї
byte detectBatteryChip() {
  byte knownAddresses[] = {0x0B, 0x0A, 0x16, 0x0C};
  for (byte i = 0; i < sizeof(knownAddresses); i++) {
    Wire.beginTransmission(knownAddresses[i]);
    if (Wire.endTransmission() == 0) return knownAddresses[i];
  }
  return 0xFF;
}

// Зчитування текстових SMBus полів
String readString(byte addr, byte reg) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  if (Wire.endTransmission() != 0) return "ERR";

  Wire.requestFrom(addr, 8);
  String result = "";
  while (Wire.available()) {
    char c = Wire.read();
    if (isPrintable(c)) result += c;
  }
  return result;
}

// Основна інформація
void readBatteryInfo(byte addr) {
  Serial.println("?? Інформація про батарею:");

  Serial.print("Виробник: "); Serial.println(readString(addr, 0x20));
  Serial.print("Модель: "); Serial.println(readString(addr, 0x21));
  Serial.print("Серійний №: "); Serial.println(readString(addr, 0x1C));

  uint16_t voltage = readWord(addr, 0x09);
  uint16_t current = readWord(addr, 0x0A);
  uint16_t temp = readWord(addr, 0x08);

  Serial.print("Напруга: "); Serial.print(voltage / 1000.0); Serial.println(" В");
  Serial.print("Струм: "); Serial.print(current); Serial.println(" мА");
  Serial.print("Температура: "); Serial.print(temp * 0.1); Serial.println(" °C");
}

// Скидання PF-флагу
void checkAndResetPF(byte addr) {
  uint16_t status = readWord(addr, 0x0F); // BatteryStatus

  if (status == 0xFFFF) {
    Serial.println("?? Неможливо зчитати статус батареї.");
    return;
  }

  Serial.print("BatteryStatus: 0x"); Serial.println(status, HEX);

  if (status & (1 << 15)) {
    Serial.println("? Виявлено PF-флаг. Спроба скидання...");

    bool success = tryResetCommand(addr, 0x0041) || tryResetCommand(addr, 0x0012);

    if (success) Serial.println("? Команда скидання відправлена.");
    else Serial.println("? Скидання не вдалося.");
  } else {
    Serial.println("? PF-флаг не встановлений.");
  }
}

// Надсилання скидаючої команди
bool tryResetCommand(byte addr, uint16_t command) {
  Wire.beginTransmission(addr);
  Wire.write(0x00); // ManufacturerAccess або Control
  Wire.write(lowByte(command));
  Wire.write(highByte(command));
  return Wire.endTransmission() == 0;
}

// Зчитування 16-бітного значення
uint16_t readWord(byte addr, byte reg) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  if (Wire.endTransmission() != 0) return 0xFFFF;

  Wire.requestFrom(addr, 2);
  if (Wire.available() < 2) return 0xFFFF;

  byte low = Wire.read();
  byte high = Wire.read();
  return (high << 8) | low;
}
