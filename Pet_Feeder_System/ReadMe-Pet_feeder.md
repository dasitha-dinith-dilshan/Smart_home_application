📘 Smart Pet Feeder System (ESP32 + Firebase + Python GUI)

This project implements a Smart IoT Pet Feeding System using an ESP32, Firebase Realtime Database, RFID access control, scheduled feeding, ultrasonic food-level detection, soil moisture auto-watering, and a fully featured Python Tkinter desktop monitoring application.

🚀 Features
🐾 Pet Feeder (ESP32)

RFID-based access for authorized pets

Automatic feeding at 7 AM, 12 PM, 7 PM

Skips feeding if food is already present

Logs feeding time & RFID access to Firebase

Ultrasonic sensor monitors food level

Soil moisture sensor controls water pump automatically

IR sensor detects food presence

Servo motors:

Servo 1 → RFID access

Servo 2 → Food dispenser

Real-time Firebase data updates

🖥️ Python Desktop Monitor (pet_feeder_monitor.py)

Serial connection to ESP32

Live data stream window

Real-time dashboard showing:

Food distance

Food level alert

IR sensor

RFID logs

Access status

Feeding schedule (7AM/12PM/7PM)

Last access & last feeding

Soil & water pump status

Firebase & WiFi status

Color-coded visual alerts

Auto-refresh serial ports

Start/Stop monitoring

🛠️ Hardware Used
Component	Purpose
ESP32 DevKit V1	Main controller
MFRC522 RFID	Detect pet tags
Ultrasonic Sensor	Food level measurement
IR Sensor	Food presence detection
Soil Moisture Sensor	Auto-watering
Relay Module	Water pump control
SG90/MG90 Servo Motors	Access gate + Food dispenser
Firebase Realtime Database	Cloud logging
Python Tkinter App	Monitoring GUI
📁 Folder Structure
/PetFeeder/
│
├── esp32/
│   └── pet_feeder_esp32.ino          # Cleaned ESP32 firmware
│
├── monitor/
│   └── pet_feeder_monitor.py         # Python GUI for testing
│
├── README.md
└── requirements.txt (optional)

⚙️ Setting Up the ESP32
1. Install Required Arduino Libraries

FirebaseESP32 by Mobizt

MFRC522

ESP32Servo

WiFi

SPI

2. Update Credentials in .ino
#define WIFI_SSID "YOUR_WIFI"
#define WIFI_PASSWORD "YOUR_PASSWORD"
#define API_KEY "YOUR_FIREBASE_API_KEY"
#define DATABASE_URL "YOUR_FIREBASE_DB_URL"

3. Upload Code to ESP32

Select:

Board: ESP32 Dev Module
Baud: 115200
Partition Scheme: Default

🖥️ Running the Python Monitoring Program
Install Required Libraries:
pip install pyserial
pip install tkinter

Run:
python pet_feeder_monitor.py

Features:

Choose COM port

Select baud (default: 115200)

Press ➤ Start Monitoring

View all live events from ESP32

📡 Firebase Structure Example
petFeeder/
    foodDistance
    foodAlert
    soilMoisture
    pumpStatus
    irSensor
    accessStatus
    lastUID
    lastAccess
    lastFeed
    7am
    12pm
    7pm

📸 GUI Screenshot Example (Add Later)
[ Insert your screenshot here ]

📝 License

This project is open-source under the MIT License.