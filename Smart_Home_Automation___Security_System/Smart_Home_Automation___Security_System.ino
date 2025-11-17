#include <WiFi.h>
#include <FirebaseESP32.h>
#include <DHT.h>
#include <time.h>

// -----------------------------------------------------------------------------
// WiFi & Firebase Credentials  (Replace with your own values)
// -----------------------------------------------------------------------------
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

#define API_KEY "YOUR_FIREBASE_API_KEY"
#define DATABASE_URL "YOUR_FIREBASE_DATABASE_URL"

// -----------------------------------------------------------------------------
// Sensor & Actuator Pins
// -----------------------------------------------------------------------------
#define PIR_PIN 15             // Motion sensor (PIR)
#define REED_PIN 13            // Magnetic door sensor
#define MQ6_PIN 35             // Gas sensor (MQ-6)
#define FLAME_PIN 34           // Flame sensor (analog)

#define DHT_PIN 4              // DHT11 sensor pin
#define LDR_PIN 32             // Light sensor (LDR)

#define BUZZER_PIN 12          // Alarm buzzer
#define FAN_RELAY 18           // Fan relay
#define LIGHT_KITCHEN 21       // Kitchen light relay
#define LIGHT_GARAGE 22        // Garage light relay

// -----------------------------------------------------------------------------
// Objects
// -----------------------------------------------------------------------------
DHT dht(DHT_PIN, DHT11);
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

// Time config (GMT +5:30)
const long gmtOffset_sec = 19800;
const int daylightOffset_sec = 0;

// -----------------------------------------------------------------------------
// Utility: Get Current Timestamp
// -----------------------------------------------------------------------------
String getTimeNow() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) return "00:00";
  char buf[20];
  strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &timeinfo);
  return String(buf);
}

// -----------------------------------------------------------------------------
// Firebase Helper Functions (For Debug Logging)
// -----------------------------------------------------------------------------
void debugSetFloat(const char* path, float val) {
  if (Firebase.setFloat(fbdo, path, val)) {
    Serial.printf("[OK] %s = %.2f\n", path, val);
  } else {
    Serial.printf("[ERR] %s: %s\n", path, fbdo.errorReason().c_str());
  }
}

void debugSetInt(const char* path, int val) {
  if (Firebase.setInt(fbdo, path, val)) {
    Serial.printf("[OK] %s = %d\n", path, val);
  } else {
    Serial.printf("[ERR] %s: %s\n", path, fbdo.errorReason().c_str());
  }
}

void debugSetString(const char* path, const String &val) {
  if (Firebase.setString(fbdo, path, val)) {
    Serial.printf("[OK] %s = %s\n", path, val.c_str());
  } else {
    Serial.printf("[ERR] %s: %s\n", path, fbdo.errorReason().c_str());
  }
}

// -----------------------------------------------------------------------------
// Setup
// -----------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(10);

  Serial.println("\n=== ESP32 Smart Home System ===");

  // Connect WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(300);
    if (millis() - start > 20000) {
      Serial.println("\nWiFi connection failed.");
      break;
    }
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected.");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  }

  // Firebase Setup
  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;

  if (Firebase.signUp(&config, &auth, "", "")) {
    Serial.println("Firebase signup successful.");
  } else {
    Serial.printf("Firebase signup failed: %s\n",
                  config.signer.signupError.message.c_str());
  }

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  delay(1000);

  // Initialize sensors
  dht.begin();
  configTime(gmtOffset_sec, daylightOffset_sec, "pool.ntp.org");

  // Pin modes
  pinMode(PIR_PIN, INPUT);
  pinMode(REED_PIN, INPUT);
  pinMode(MQ6_PIN, INPUT);
  pinMode(FLAME_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);

  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(FAN_RELAY, OUTPUT);
  pinMode(LIGHT_KITCHEN, OUTPUT);
  pinMode(LIGHT_GARAGE, OUTPUT);

  // Default OFF state
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(FAN_RELAY, LOW);
  digitalWrite(LIGHT_KITCHEN, LOW);
  digitalWrite(LIGHT_GARAGE, LOW);

  Serial.println("Setup completed.\n");
}

// -----------------------------------------------------------------------------
// Main Loop
// -----------------------------------------------------------------------------
void loop() {

  // Log Firebase readiness every 5 seconds
  static unsigned long lastStatus = 0;
  if (millis() - lastStatus > 5000) {
    Serial.printf("Firebase.ready(): %s\n", Firebase.ready() ? "true" : "false");
    lastStatus = millis();
  }

  if (!Firebase.ready()) {
    delay(1000);
    return;
  }

  // ---------------------------------------------------------------------------
  // Read Environmental Values
  // ---------------------------------------------------------------------------
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  float lightV = analogRead(LDR_PIN) * (5.0 / 4095.0);

  Serial.printf("Temp: %.2f°C | Hum: %.2f%% | Light: %.2fV\n",
                temp, hum, lightV);

  debugSetFloat("environment/temperature", temp);
  debugSetFloat("environment/humidity", hum);
  debugSetFloat("environment/lightLevel", lightV);

  // Auto light control (Garage)
  digitalWrite(LIGHT_GARAGE, lightV < 2.0 ? HIGH : LOW);

  // Auto fan control
  if (temp > 32.0) {
    digitalWrite(FAN_RELAY, HIGH);
    delay(5000);
  }

  // ---------------------------------------------------------------------------
  // Security Sensors
  // ---------------------------------------------------------------------------
  int motion = digitalRead(PIR_PIN);
  int door = digitalRead(REED_PIN);
  float gasValue = analogRead(MQ6_PIN);
  float flameValue = analogRead(FLAME_PIN);

  int gasLeak = gasValue > 500 ? 1 : 0;
  int fireDetected = flameValue < 1000 ? 1 : 0;

  debugSetInt("security/motion", motion);
  debugSetInt("security/doorStatus", door);
  debugSetInt("security/gasLeak", gasLeak);
  debugSetInt("security/fire", fireDetected);

  // Door alarm
  if (door == HIGH) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(2000);
    digitalWrite(BUZZER_PIN, LOW);
    debugSetString("security/doorEvent", "Door Opened");
  }

  // Fire alarm
  if (fireDetected) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(3000);
    digitalWrite(BUZZER_PIN, LOW);
    debugSetString("security/fireEvent", "Fire Detected");
  }

  // ---------------------------------------------------------------------------
  // Manual Appliance Control from Firebase
  // ---------------------------------------------------------------------------
  if (Firebase.getInt(fbdo, "devices/kitchenLight")) {
    digitalWrite(LIGHT_KITCHEN, fbdo.intData() ? HIGH : LOW);
  }

  if (Firebase.getInt(fbdo, "devices/fan")) {
    digitalWrite(FAN_RELAY, fbdo.intData() ? HIGH : LOW);
  }

  delay(500);
}
