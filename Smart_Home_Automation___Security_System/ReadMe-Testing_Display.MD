🖥️ Smart Home System Serial Monitor (Python Tkinter)

A desktop-based Smart Home Monitoring Application built with Python Tkinter, designed to read and visualize real-time data from the ESP32 Smart Home System through a serial USB connection.

This program allows users to monitor environmental values, security alerts, and system status in a clean, organized GUI with color-coded alerts.

📌 Features
📡 Live Serial Monitoring

Automatically reads JSON-like or text-based logs from ESP32

Displays real-time system data

Scrollable live log window

🌡️ Environment Display

Temperature

Humidity

Light intensity

Color-coded indicators:

🔴 Red → Danger

🟠 Orange → Warning

🟢 Green → Safe

🚨 Security Monitoring

Motion detection (PIR)

Door status (Reed Switch)

Gas leak detection (MQ-6)

Flame detection

Color rules indicate safety or danger automatically.

🔌 Port Management

Auto-detects available COM ports

Choose baud rate

Start/Stop monitoring

Refresh port list

⚙️ System Status Indicators

WiFi connectivity (from ESP32 serial logs)

Firebase connectivity logs

Last update timestamp

📁 Project Structure
/Smart Home Application/Smart_Home_Automation___Security_System
│
├── Test-Display.py        # Main application
├── ReadMe-Testing_Display.md         # Documentation of Testing Program
├── ReadMe-Smart_Home_Automation___Security_System.md # Documentation of Arduino program
└── Smart_Home_Automation___Security_System.ino # Arduino Program

🛠️ Requirements
Python Version
Python 3.8 or higher

Required Libraries

Install dependencies with:

pip install pyserial
pip install tk


OR create a requirements.txt:

pyserial
tk

▶️ How to Run
1. Connect ESP32 to USB

Make sure the ESP32 is sending serial logs such as:

Environment -> Temp: 28.50°C  Humidity: 62.00%  Light: 2.50V
Security -> Motion: YES | Door: OPEN | Gas: 350

2. Run the program
python Display.py

3. Select the COM port

The program will show:

✔ Available serial ports
✔ Baud rate options
✔ Start & Stop buttons

🖼️ GUI Preview

Features included:

Title Bar

Connection Panel

Status Grid

Real-time log stream

Color-coded values

(Add screenshots here if you want—just upload them and I will embed)

🔍 How It Works (Parsing Logic)

The system listens to serial output and extracts values using:

Regex pattern matching

Keyword detection

Clean mapping into UI components

Examples:

Serial Text	GUI Interpretation
Motion: YES	Motion Detected (Red)
Door: OPEN	Door Open (Red)
FIRE DETECTED	Flame Alert (Red)
Connected to WiFi	WiFi Status → Connected
Firebase.ready(): true	Firebase Ready
💡 Color Logic (Visualization)
Environment

Green → Normal

Orange → Warning

Red → Danger

Security

Red for open / motion / leak / fire

Green for normal conditions

System

Green → Connected/Ready

Red → Failure

🧩 Extending the Program

You can easily add:

Charts (Matplotlib or Tkinter Canvas)

Logging to file

Custom Serial Commands

MQTT inputs

Automatic COM detection

Just ask if you want these features generated automatically!

📜 License

This tool is open-source under the MIT License.
Feel free to modify and use it in your projects.