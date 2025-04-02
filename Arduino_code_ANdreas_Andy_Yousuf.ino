#include "DHT.h"
#include <Servo.h>
#include <Adafruit_NeoPixel.h>

// DHT22-setup
#define DHTPIN 7
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// Servo-setup
Servo myServo;
#define SERVO_PIN 9

// NeoPixel-setup
#define NEOPIXEL_PIN 10
#define NUMPIXELS 24
Adafruit_NeoPixel strip(NUMPIXELS, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

// LEDs för temperaturstatus
#define LED_COLD 4
#define LED_NORMAL 5
#define LED_HOT 6

// Ljussensor (fotomotstånd)
#define PHOTORESISTOR_PIN A0

// Variabler för sensordata och status
float latestTemperature = NAN;
float latestHumidity = NAN;
int latestLightValue = 0;
int brightness = 50;             // Standardljusstyrka (0–100)
uint32_t currentColor = 0xFFFFFF; // Standardfärg (vit)

// Konstanter för temperaturgränser
const float TEMP_HIGH_THRESHOLD = 26.0;
const float TEMP_LOW_THRESHOLD = 24.0;

// Funktioner
void updateSensorData();
void processSerialCommands();
void updateLEDStatus(float temperature);
void applyColor(uint32_t color);

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // Vänta tills Serial är redo
  }

  // Setup för hårdvara
  pinMode(LED_COLD, OUTPUT);
  pinMode(LED_NORMAL, OUTPUT);
  pinMode(LED_HOT, OUTPUT);

  dht.begin();
  myServo.attach(SERVO_PIN);
  myServo.write(90); // Startposition för servon

  strip.begin();
  strip.setBrightness(map(brightness, 0, 100, 0, 255)); // Sätt initial ljusstyrka
  applyColor(currentColor); // Sätt initial färg

  // Blink alla LEDs som startindikator
  blinkAll();
}

void loop() {
  // Uppdatera sensordata
  static unsigned long lastUpdate = 0;
  if (millis() - lastUpdate >= 2000) { // Uppdatera varannan sekund
    lastUpdate = millis();
    updateSensorData();
  }

  // Lyssna på inkommande kommandon via Serial
  processSerialCommands();
}

void updateSensorData() {
  // Läs sensordata
  latestTemperature = dht.readTemperature();
  latestHumidity = dht.readHumidity();
  latestLightValue = analogRead(PHOTORESISTOR_PIN);

  // Skicka sensordata via Serial i JSON-format
  if (!isnan(latestTemperature) && !isnan(latestHumidity)) {
    Serial.print("{\"temperature\": ");
    Serial.print(latestTemperature);
    Serial.print(", \"humidity\": ");
    Serial.print(latestHumidity);
    Serial.print(", \"lightSensor\": ");
    Serial.print(latestLightValue);
    Serial.print(", \"activeLED\": \"");
    Serial.print((latestTemperature < TEMP_LOW_THRESHOLD) ? "Cold LED" :
                 (latestTemperature <= TEMP_HIGH_THRESHOLD) ? "Normal LED" : "Hot LED");
    Serial.println("\"}");
  }

  // Uppdatera LEDs baserat på temperatur
  if (!isnan(latestTemperature)) {
    updateLEDStatus(latestTemperature);
  }
}

void processSerialCommands() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // Läs inkommande kommando

    // Hantera SERVO-kommandon
    if (command.startsWith("SERVO:")) {
      int angle = command.substring(6).toInt();
      angle = constrain(angle, 0, 180); // Begränsa vinkel mellan 0 och 180
      myServo.write(angle);
      Serial.println("Servo moved to angle: " + String(angle));
    }
    // Hantera NEOPIXEL-ljusstyrka
    else if (command.startsWith("BRIGHTNESS:")) {
      brightness = constrain(command.substring(11).toInt(), 0, 100); // Begränsa till 0–100
      strip.setBrightness(map(brightness, 0, 100, 0, 255)); // Omvandla till 0–255
      strip.show();
      Serial.println("Brightness set to: " + String(brightness));
    }
    // Hantera NEOPIXEL-färg
    else if (command.startsWith("COLOR:")) {
      String colorHex = command.substring(6);
      currentColor = strtol(colorHex.c_str(), NULL, 16); // Konvertera hex-färg
      applyColor(currentColor);
      Serial.println("Color set to: #" + colorHex);
    }
    // Hantera regnbågseffekt
    else if (command.startsWith("RAINBOW:")) {
      int delayMs = constrain(command.substring(8).toInt(), 0, 100); // Fördröjning (0–100 ms)
      Serial.println("Starting rainbow effect with delay: " + String(delayMs) + " ms");
      rainbowEffect(delayMs);
    }
    // Hantera färgcykeleffekt
    else if (command.startsWith("CYCLE:")) {
      int delayMs = constrain(command.substring(6).toInt(), 0, 100); // Fördröjning (0–100 ms)
      Serial.println("Starting color cycle effect with delay: " + String(delayMs) + " ms");
      colorCycleEffect(delayMs);
    }
    // Okänt kommando
    else {
      Serial.println("Unknown command: " + command);
    }
  }
}

void applyColor(uint32_t color) {
  for (int i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, color);
  }
  strip.show();
}

void updateLEDStatus(float temperature) {
  if (temperature < TEMP_LOW_THRESHOLD) {
    digitalWrite(LED_COLD, HIGH);
    digitalWrite(LED_NORMAL, LOW);
    digitalWrite(LED_HOT, LOW);
  } else if (temperature >= TEMP_LOW_THRESHOLD && temperature <= TEMP_HIGH_THRESHOLD) {
    digitalWrite(LED_COLD, LOW);
    digitalWrite(LED_NORMAL, HIGH);
    digitalWrite(LED_HOT, LOW);
  } else if (temperature > TEMP_HIGH_THRESHOLD) {
    digitalWrite(LED_COLD, LOW);
    digitalWrite(LED_NORMAL, LOW);
    digitalWrite(LED_HOT, HIGH);
  }
}

void rainbowEffect(int delayMs) {
    int numPixels = strip.numPixels();
    for (int firstPixelHue = 0; firstPixelHue < 65536; firstPixelHue += 256) { // 65536 för full regnbåge
        for (int i = 0; i < numPixels; i++) {
            int pixelHue = firstPixelHue + (i * 65536 / numPixels); // Beräkna färg för varje pixel
            strip.setPixelColor(i, strip.ColorHSV(pixelHue));
        }
        strip.show();
        delay(delayMs);
    }
}


void colorCycleEffect(int delayMs) {
  for (int i = 0; i < 256; i++) { // 256 färger i färgcykeln
    uint32_t color = Wheel(i);
    applyColor(color);
    delay(delayMs);
  }
}

// Hjälpfunktion för att generera regnbågsfärger
uint32_t Wheel(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if (WheelPos < 85) {
    return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  } else if (WheelPos < 170) {
    WheelPos -= 85;
    return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  } else {
    WheelPos -= 170;
    return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
  }
}

void blinkAll() {
  // Tänd alla LEDs och NeoPixel som startindikator
  digitalWrite(LED_COLD, HIGH);
  digitalWrite(LED_NORMAL, HIGH);
  digitalWrite(LED_HOT, HIGH);

  for (int i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, strip.Color(255, 255, 255)); // Vit färg
  }
  strip.show();
  delay(500);

  // Släck alla LEDs och NeoPixel
  digitalWrite(LED_COLD, LOW);
  digitalWrite(LED_NORMAL, LOW);
  digitalWrite(LED_HOT, LOW);

  for (int i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, strip.Color(0, 0, 0));
  }
  strip.show();
  delay(500);
}