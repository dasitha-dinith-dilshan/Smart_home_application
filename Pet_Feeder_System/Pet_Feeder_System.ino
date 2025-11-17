#include <WiFi.h>
#include <FirebaseESP32.h>
#include <SPI.h>
#include <MFRC522.h>
#include <time.h>
#include <ESP32Servo.h>

// -----------------------------------------------------------------------------
// WiFi & Firebase Credentials  (Replace with your own values before uploading)
// -----------------------------------------------------------------------------
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define API_KEY "YOUR_FIREBASE_API_KEY"
#define DATABASE_URL "YOUR_DATABASE_URL"

// -----------------------------------------------------------------------------
// Pin Definitions (ESP32 DevKit V1)
// -----------------------------------------------------------------------------
#define SS_PIN 5              // RFID SS
#define RST_PIN 22            // RFID RST

// Servos
#define SERVO1_PIN 13         // Servo for RFID access
#define SERVO2_PIN 12         // Servo for scheduled feeding

// Relay & sensors
#define RELAY_PIN 27          // Water pump relay
#define SOIL_MOISTURE_PIN 34  // Soil moisture sensor
#define TRIG_PIN 32           // Ultrasonic trigger
#define ECHO_PIN 33           // Ultrasonic echo
#define IR_PIN 4              // IR sensor

// -----------------------------------------------------------------------------
// Objects
// -----------------------------------------------------------------------------
MFRC522 mfrc522(SS_PIN, RST_PIN);
Servo servo1;
Servo servo2;

FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

// -----------------------------------------------------------------------------
// Feeding Schedule
// -----------------------------------------------------------------------------
bool feedingSchedule[3] = {false, false, false};  // 7AM, 12PM, 7PM
int lastHour = -1;

#define FOOD_LOW_THRESHOLD 15     // Ultrasonic threshold (cm)

// Time (GMT +5:30)
const long gmtOffset_sec = 19800;
const int daylightOffset_sec = 0;

// -----------------------------------------------------------------------------
// Firebase Debug Helpers
// -----------------------------------------------------------------------------
void debugSetFloat(const char* path, float val) {
  Firebase.setFloat(fbdo, path, val);
}

void debugSetInt(const char* path, int val) {
  Firebase.setInt(fbdo, path, val);
}

void debugSetString(const char* path, const String &val) {
  Firebase.setString(fbdo, path, val);
}

// -----------------------------------------------------------------------------
// Setup
// -----------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== ESP32 Pet Feeder System ===");

  // Pin setup
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(IR_PIN, INPUT);

  digitalWrite(RELAY_PIN, LOW);

  // Servos
  servo1.attach(SERVO1_PIN);
  servo2.attach(SERVO2_PIN);
  servo1.write(0);
  servo2.write(0);

  // WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    Serial.print(".");
    delay(300);
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected to WiFi");
  } else {
    Serial.println("\nWiFi connection failed");
  }

  // Firebase
  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;
  Firebase.signUp(&config, &auth, "", "");
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  debugSetInt("/petFeeder/status", 1);

  // NTP Time
  configTime(gmtOffset_sec, daylightOffset_sec, "pool.ntp.org");

  // RFID
  SPI.begin();
  mfrc522.PCD_Init();

  Serial.println("Setup complete.\n");
}

// -----------------------------------------------------------------------------
// Utility: Get Current Timestamp
// -----------------------------------------------------------------------------
String getTimeNow() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) return "00:00:00";
  char buf[20];
  strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", &timeinfo);
  return String(buf);
}

// -----------------------------------------------------------------------------
// Ultrasonic Distance Measurement
// -----------------------------------------------------------------------------
long measureDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(5);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return -1;
  return duration * 0.034 / 2;
}

// -----------------------------------------------------------------------------
// Servo Control (RFID)
// -----------------------------------------------------------------------------
void openServo1() {
  Serial.println("Authorized: Opening Servo 1");
  servo1.write(120);
  delay(20000);
  servo1.write(0);

  debugSetString("/petFeeder/lastAccess", getTimeNow());
}

// -----------------------------------------------------------------------------
// Servo Control (Scheduled Feeding)
// -----------------------------------------------------------------------------
void feedPet() {
  Serial.println("Scheduled Feeding: Opening Servo 2");
  servo2.write(90);
  delay(3000);
  servo2.write(0);

  debugSetString("/petFeeder/lastFeed", getTimeNow());
}

// -----------------------------------------------------------------------------
// Feeding Schedule Logic (7AM/12PM/7PM)
// -----------------------------------------------------------------------------
void checkScheduledFeeding() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) return;

  int hour = timeinfo.tm_hour;

  // Reset schedule at midnight
  if (hour == 0 && lastHour != 0) {
    feedingSchedule[0] = feedingSchedule[1] = feedingSchedule[2] = false;
    Serial.println("Daily feeding schedule reset.");
  }

  int irVal = digitalRead(IR_PIN);
  bool foodPresent = (irVal == 0);

  debugSetInt("/petFeeder/irSensor", irVal);
  debugSetInt("/petFeeder/foodPresent", foodPresent ? 1 : 0);

  if (hour == 7 && !feedingSchedule[0] && lastHour != 7) {
    feedingSchedule[0] = true;
    foodPresent ? debugSetString("/petFeeder/7am", "Skipped - Food present")
                : (feedPet(), debugSetString("/petFeeder/7am", "Fed"));
  }

  if (hour == 12 && !feedingSchedule[1] && lastHour != 12) {
    feedingSchedule[1] = true;
    foodPresent ? debugSetString("/petFeeder/12pm", "Skipped - Food present")
                : (feedPet(), debugSetString("/petFeeder/12pm", "Fed"));
  }

  if (hour == 19 && !feedingSchedule[2] && lastHour != 19) {
    feedingSchedule[2] = true;
    foodPresent ? debugSetString("/petFeeder/7pm", "Skipped - Food present")
                : (feedPet(), debugSetString("/petFeeder/7pm", "Fed"));
  }

  lastHour = hour;
}

// -----------------------------------------------------------------------------
// Main Loop
// -----------------------------------------------------------------------------
void loop() {
  static unsigned long lastCheck = 0;

  if (!Firebase.ready()) {
    delay(1000);
    return;
  }

  // ---------------------------------------------------------------------------
  // RFID Card Reading
  // ---------------------------------------------------------------------------
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {

    char uidStr[20];
    for (byte i = 0; i < mfrc522.uid.size; i++) {
      sprintf(uidStr + (i * 3), "%02X:", mfrc522.uid.uidByte[i]);
    }
    uidStr[(mfrc522.uid.size * 3) - 1] = '\0';
    String uid = uidStr;

    Serial.println("RFID Detected: " + uid);

    // Authorized IDs
    if (uid.equals("5B:2B:3A:03") || uid.equals("93:29:C1:01")) {
      openServo1();
      debugSetString("/petFeeder/accessStatus", "Authorized");
      debugSetString("/petFeeder/lastUID", uid);
    } else {
      Serial.println("Unauthorized UID");
      debugSetString("/petFeeder/accessStatus", "Unauthorized");
      debugSetString("/petFeeder/unauthorizedUID", uid);
    }

    mfrc522.PICC_HaltA();
  }

  // ---------------------------------------------------------------------------
  // Main 2-second Routine
  // ---------------------------------------------------------------------------
  if (millis() - lastCheck >= 2000) {
    lastCheck = millis();

    // Soil moisture
    int soilValue = digitalRead(SOIL_MOISTURE_PIN);
    bool soilDry = (soilValue == LOW);

    debugSetInt("/petFeeder/soilMoisture", soilValue);

    if (soilDry) {
      digitalWrite(RELAY_PIN, HIGH);
      debugSetString("/petFeeder/soilStatus", "Dry - Watering");
      debugSetInt("/petFeeder/pumpStatus", 1);
    } else {
      digitalWrite(RELAY_PIN, LOW);
      debugSetString("/petFeeder/soilStatus", "Wet - Pump Off");
      debugSetInt("/petFeeder/pumpStatus", 0);
    }

    // Food level (ultrasonic)
    long dist = measureDistance();
    if (dist > 0) {
      debugSetInt("/petFeeder/foodDistance", dist);
      (dist > FOOD_LOW_THRESHOLD)
          ? debugSetString("/petFeeder/foodAlert", "Food level low")
          : debugSetString("/petFeeder/foodAlert", "OK");
    } else {
      debugSetString("/petFeeder/foodAlert", "Sensor Error");
    }

    checkScheduledFeeding();
  }

  delay(80);
}
