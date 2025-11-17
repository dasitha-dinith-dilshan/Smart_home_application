# Smart_Home_Application
This project is a complete IoT-based Smart Home System built using an ESP32 Dev Kit, Firebase Realtime Database, and a fully responsive Web Dashboard. The system allows real-time monitoring, security alerts, and manual/automatic control of home appliances. It integrates three major modules—Home Security, Home Automation, and Smart Pet Feeding—to provide a unified, intelligent, and user-friendly smart home experience.

🔒 1. Home Security System

A multi-sensor security module designed to keep the home protected at all times.
Key features include:

* PIR motion detection

* Magnetic reed switch for door status

* Smoke/gas detection using MQ-6

* Flame detection

* Buzzer alert when the system is armed

* Real-time notifications and logs stored in Firebase

* Status viewable on the web dashboard

🏠 2. Home Automation & Monitoring

Enables intelligent control and live monitoring of household conditions and appliances.
Features include:

* DHT11 sensor for temperature & humidity

* LDR/light sensor for automatic lighting

* Automatic fan control based on temperature

* Manual/automatic mode switch for appliances

* Control of lights, fans, and other loads through the dashboard

* Real-time sensor data streaming to Firebase

* Fully interactive web interface with authentication

🐾 3. Smart Pet Feeding System

A fully automated pet care module built for convenience and reliability.
Core functionalities include:

* RFID-based access for pets

* Automatic feeding at scheduled times (7 AM, 12 PM, 7 PM)

* Skips feeding if food is already present (IR-based detection)

* Ultrasonic sensor to monitor food level

* Servo-controlled food dispenser

Soil moisture sensor and relay-based water pump control

All logs (feeding time, access, food levels) synced to Firebase

Optional Python desktop app for advanced real-time monitoring
