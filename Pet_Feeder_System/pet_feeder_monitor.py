import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import re
from datetime import datetime

class PetFeederMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🐾 Pet Feeder System Monitor")
        self.geometry("1200x800")
        self.configure(bg='#2b2b2b')

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2b2b2b', background='#ffffff')
        self.style.configure('Status.TLabel', font=('Arial', 10), foreground='#ffffff', background='#2b2b2b')
        self.style.configure('Custom.TButton', font=('Arial', 10, 'bold'))

        self.serial_port = None
        self.running = False
        self.thread = None

        self.current_data = {
            'food_distance': '--',
            'food_alert': 'Unknown',
            'food_present': 'Unknown',
            'ir_sensor': '--',
            'relay_status': 'OFF',
            'last_access': 'Never',
            'last_feed': 'Never',
            'last_uid': '--',
            'access_status': '--',
            'unauthorized_uid': '--',
            'feeding_7am': '--',
            'feeding_12pm': '--',
            'feeding_7pm': '--',
            'wifi_status': 'Unknown',
            'firebase_status': 'Unknown',
            'last_update': 'Never'
        }

        self.create_widgets()
        self.populate_ports()

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title_label = ttk.Label(main_frame, text="🐾 Pet Feeder System Monitor", style='Title.TLabel')
        title_label.pack(pady=(0, 20))

        conn_frame = ttk.LabelFrame(main_frame, text="🔌 Connection Settings", padding=10)
        conn_frame.pack(fill=tk.X, pady=(0, 20))

        port_frame = ttk.Frame(conn_frame)
        port_frame.pack(fill=tk.X, pady=5)

        ttk.Label(port_frame, text="Serial Port:", style='Status.TLabel').pack(side=tk.LEFT)
        self.port_combo = ttk.Combobox(port_frame, state="readonly", width=20)
        self.port_combo.pack(side=tk.LEFT, padx=(10, 20))

        ttk.Label(port_frame, text="Baud Rate:", style='Status.TLabel').pack(side=tk.LEFT)
        self.baud_combo = ttk.Combobox(port_frame, state="readonly", values=[9600, 115200, 4800, 19200, 38400, 57600], width=10)
        self.baud_combo.set(115200)
        self.baud_combo.pack(side=tk.LEFT, padx=(10, 20))

        btn_frame = ttk.Frame(conn_frame)
        btn_frame.pack(pady=10)

        self.start_btn = ttk.Button(btn_frame, text="▶️ Start Monitoring", command=self.start_reading, style='Custom.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="⏹️ Stop Monitoring", command=self.stop_reading, state=tk.DISABLED, style='Custom.TButton')
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_btn = ttk.Button(btn_frame, text="🔄 Refresh Ports", command=self.populate_ports, style='Custom.TButton')
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        status_frame = ttk.LabelFrame(main_frame, text="📊 System Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        self.create_status_grid(status_frame)

        data_frame = ttk.LabelFrame(main_frame, text="📜 Live Data Stream", padding=10)
        data_frame.pack(fill=tk.BOTH, expand=True)

        self.text_area = scrolledtext.ScrolledText(
            data_frame, 
            width=100, 
            height=20, 
            state=tk.DISABLED, 
            font=("Consolas", 9),
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='#ffffff'
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)

        clear_btn = ttk.Button(data_frame, text="🗑️ Clear Display", command=self.clear_display, style='Custom.TButton')
        clear_btn.pack(pady=(10, 0))

    def create_status_grid(self, parent):
        # Food Status Frame
        food_frame = ttk.LabelFrame(parent, text="🍽️ Food Monitoring", padding=10)
        food_frame.pack(fill=tk.X, pady=5)

        food_grid = ttk.Frame(food_frame)
        food_grid.pack(fill=tk.X)

        ttk.Label(food_grid, text="Food Distance:", style='Status.TLabel').grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.food_distance_label = ttk.Label(food_grid, text="-- cm", style='Status.TLabel')
        self.food_distance_label.grid(row=0, column=1, sticky='w', padx=(0, 20))

        ttk.Label(food_grid, text="Food Alert:", style='Status.TLabel').grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.food_alert_label = ttk.Label(food_grid, text="Unknown", style='Status.TLabel')
        self.food_alert_label.grid(row=0, column=3, sticky='w', padx=(0, 20))

        ttk.Label(food_grid, text="Food Present:", style='Status.TLabel').grid(row=0, column=4, sticky='w', padx=(0, 10))
        self.food_present_label = ttk.Label(food_grid, text="Unknown", style='Status.TLabel')
        self.food_present_label.grid(row=0, column=5, sticky='w', padx=(0, 20))

        ttk.Label(food_grid, text="IR Sensor:", style='Status.TLabel').grid(row=0, column=6, sticky='w', padx=(0, 10))
        self.ir_sensor_label = ttk.Label(food_grid, text="--", style='Status.TLabel')
        self.ir_sensor_label.grid(row=0, column=7, sticky='w')

        # RFID Access Frame
        rfid_frame = ttk.LabelFrame(parent, text="🔐 RFID Access Control", padding=10)
        rfid_frame.pack(fill=tk.X, pady=5)

        rfid_grid = ttk.Frame(rfid_frame)
        rfid_grid.pack(fill=tk.X)

        ttk.Label(rfid_grid, text="Last UID:", style='Status.TLabel').grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.last_uid_label = ttk.Label(rfid_grid, text="--", style='Status.TLabel')
        self.last_uid_label.grid(row=0, column=1, sticky='w', padx=(0, 20))

        ttk.Label(rfid_grid, text="Access Status:", style='Status.TLabel').grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.access_status_label = ttk.Label(rfid_grid, text="--", style='Status.TLabel')
        self.access_status_label.grid(row=0, column=3, sticky='w', padx=(0, 20))

        ttk.Label(rfid_grid, text="Unauthorized UID:", style='Status.TLabel').grid(row=0, column=4, sticky='w', padx=(0, 10))
        self.unauthorized_uid_label = ttk.Label(rfid_grid, text="--", style='Status.TLabel')
        self.unauthorized_uid_label.grid(row=0, column=5, sticky='w')

        # Feeding Schedule Frame
        schedule_frame = ttk.LabelFrame(parent, text="⏰ Feeding Schedule", padding=10)
        schedule_frame.pack(fill=tk.X, pady=5)

        schedule_grid = ttk.Frame(schedule_frame)
        schedule_grid.pack(fill=tk.X)

        ttk.Label(schedule_grid, text="7 AM:", style='Status.TLabel').grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.feeding_7am_label = ttk.Label(schedule_grid, text="--", style='Status.TLabel')
        self.feeding_7am_label.grid(row=0, column=1, sticky='w', padx=(0, 20))

        ttk.Label(schedule_grid, text="12 PM:", style='Status.TLabel').grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.feeding_12pm_label = ttk.Label(schedule_grid, text="--", style='Status.TLabel')
        self.feeding_12pm_label.grid(row=0, column=3, sticky='w', padx=(0, 20))

        ttk.Label(schedule_grid, text="7 PM:", style='Status.TLabel').grid(row=0, column=4, sticky='w', padx=(0, 10))
        self.feeding_7pm_label = ttk.Label(schedule_grid, text="--", style='Status.TLabel')
        self.feeding_7pm_label.grid(row=0, column=5, sticky='w')

        # Activity Log Frame
        activity_frame = ttk.LabelFrame(parent, text="📝 Activity Log", padding=10)
        activity_frame.pack(fill=tk.X, pady=5)

        activity_grid = ttk.Frame(activity_frame)
        activity_grid.pack(fill=tk.X)

        ttk.Label(activity_grid, text="Last Access:", style='Status.TLabel').grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.last_access_label = ttk.Label(activity_grid, text="Never", style='Status.TLabel')
        self.last_access_label.grid(row=0, column=1, sticky='w', padx=(0, 20))

        ttk.Label(activity_grid, text="Last Feed:", style='Status.TLabel').grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.last_feed_label = ttk.Label(activity_grid, text="Never", style='Status.TLabel')
        self.last_feed_label.grid(row=0, column=3, sticky='w', padx=(0, 20))

        ttk.Label(activity_grid, text="Relay:", style='Status.TLabel').grid(row=0, column=4, sticky='w', padx=(0, 10))
        self.relay_label = ttk.Label(activity_grid, text="OFF", style='Status.TLabel')
        self.relay_label.grid(row=0, column=5, sticky='w')

        # System Status Frame
        sys_frame = ttk.LabelFrame(parent, text="⚙️ System Status", padding=10)
        sys_frame.pack(fill=tk.X, pady=5)

        sys_grid = ttk.Frame(sys_frame)
        sys_grid.pack(fill=tk.X)

        ttk.Label(sys_grid, text="WiFi:", style='Status.TLabel').grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.wifi_label = ttk.Label(sys_grid, text="Unknown", style='Status.TLabel')
        self.wifi_label.grid(row=0, column=1, sticky='w', padx=(0, 20))

        ttk.Label(sys_grid, text="Firebase:", style='Status.TLabel').grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.firebase_label = ttk.Label(sys_grid, text="Unknown", style='Status.TLabel')
        self.firebase_label.grid(row=0, column=3, sticky='w', padx=(0, 20))

        ttk.Label(sys_grid, text="Last Update:", style='Status.TLabel').grid(row=0, column=4, sticky='w', padx=(0, 10))
        self.update_label = ttk.Label(sys_grid, text="Never", style='Status.TLabel')
        self.update_label.grid(row=0, column=5, sticky='w')

    def update_status_display(self):
        # Food Monitoring
        self.food_distance_label.config(text=f"{self.current_data['food_distance']} cm")
        self.food_alert_label.config(text=self.current_data['food_alert'])
        self.food_present_label.config(text=self.current_data['food_present'])
        self.ir_sensor_label.config(text=self.current_data['ir_sensor'])

        # RFID Access
        self.last_uid_label.config(text=self.current_data['last_uid'])
        self.access_status_label.config(text=self.current_data['access_status'])
        self.unauthorized_uid_label.config(text=self.current_data['unauthorized_uid'])

        # Feeding Schedule
        self.feeding_7am_label.config(text=self.current_data['feeding_7am'])
        self.feeding_12pm_label.config(text=self.current_data['feeding_12pm'])
        self.feeding_7pm_label.config(text=self.current_data['feeding_7pm'])

        # Activity Log
        self.last_access_label.config(text=self.current_data['last_access'])
        self.last_feed_label.config(text=self.current_data['last_feed'])
        self.relay_label.config(text=self.current_data['relay_status'])

        # System Status
        self.wifi_label.config(text=self.current_data['wifi_status'])
        self.firebase_label.config(text=self.current_data['firebase_status'])
        self.update_label.config(text=self.current_data['last_update'])

        # Color coding
        # Food Alert
        if "low" in self.current_data['food_alert'].lower():
            self.food_alert_label.config(foreground='red')
        elif "OK" in self.current_data['food_alert']:
            self.food_alert_label.config(foreground='#00ff00')
        else:
            self.food_alert_label.config(foreground='orange')

        # Food Distance
        try:
            distance = int(self.current_data['food_distance'].replace('--', '0'))
            if distance > 15:
                self.food_distance_label.config(foreground='red')
            elif distance > 10:
                self.food_distance_label.config(foreground='orange')
            else:
                self.food_distance_label.config(foreground='#00ff00')
        except:
            self.food_distance_label.config(foreground='white')

        # Food Present
        if "Yes" in self.current_data['food_present']:
            self.food_present_label.config(foreground='#00ff00')
        elif "No" in self.current_data['food_present']:
            self.food_present_label.config(foreground='orange')
        else:
            self.food_present_label.config(foreground='white')

        # Access Status
        if "Authorized" in self.current_data['access_status']:
            self.access_status_label.config(foreground='#00ff00')
        elif "Unauthorized" in self.current_data['access_status']:
            self.access_status_label.config(foreground='red')
        else:
            self.access_status_label.config(foreground='white')

        # Relay Status
        if self.current_data['relay_status'] == "ON":
            self.relay_label.config(foreground='#00ff00')
        else:
            self.relay_label.config(foreground='orange')

        # WiFi and Firebase
        if "Connected" in self.current_data['wifi_status']:
            self.wifi_label.config(foreground='#00ff00')
        else:
            self.wifi_label.config(foreground='red')

        if "true" in self.current_data['firebase_status'].lower():
            self.firebase_label.config(foreground='#00ff00')
        else:
            self.firebase_label.config(foreground='red')

    def populate_ports(self):
        ports = serial.tools.list_ports.comports()
        port_names = [port.device for port in ports]
        if port_names:
            self.port_combo['values'] = port_names
            self.port_combo.set(port_names[0])
        else:
            self.port_combo['values'] = ['No Ports Found']
            self.port_combo.set('No Ports Found')
            self.start_btn.config(state=tk.DISABLED)

    def start_reading(self):
        port = self.port_combo.get()
        if port == 'No Ports Found':
            messagebox.showerror("Error", "No serial ports available")
            return

        try:
            baud = int(self.baud_combo.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid baud rate")
            return

        try:
            self.serial_port = serial.Serial(port, baud, timeout=1)
            time.sleep(2)
        except serial.SerialException as e:
            messagebox.showerror("Error", f"Could not open serial port:\n{e}")
            return

        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.config(state=tk.DISABLED)

        self.thread = threading.Thread(target=self.read_serial_data, daemon=True)
        self.thread.start()

    def stop_reading(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

    def read_serial_data(self):
        while self.running:
            if self.serial_port.in_waiting > 0:
                try:
                    line = self.serial_port.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        self.process_data_line(line)
                        self.append_text(line)
                except Exception as e:
                    self.append_text(f"Error decoding data: {e}")
            else:
                time.sleep(0.1)

    def process_data_line(self, line):
        try:
            # WiFi Status
            if "Connected to WiFi" in line or "Connected to Wi-Fi" in line:
                self.current_data['wifi_status'] = "Connected"
            elif "Failed to connect" in line:
                self.current_data['wifi_status'] = "Failed"

            # Firebase Status
            if "Firebase.ready():" in line:
                if "true" in line.lower():
                    self.current_data['firebase_status'] = "Ready (true)"
                else:
                    self.current_data['firebase_status'] = "Not Ready (false)"

            # RFID Detection
            if "RFID Detected:" in line:
                match = re.search(r"RFID Detected:\s*([A-F0-9:]+)", line)
                if match:
                    self.current_data['last_uid'] = match.group(1)

            if "Authorized ID detected" in line or "✅ Authorized" in line:
                self.current_data['access_status'] = "Authorized"

            if "Unauthorized UID" in line or "❌ Unauthorized" in line:
                self.current_data['access_status'] = "Unauthorized"
                match = re.search(r"([A-F0-9:]+)", line)
                if match:
                    self.current_data['unauthorized_uid'] = match.group(1)

            # Servo Actions
            if "Opening Servo 1" in line:
                self.current_data['last_access'] = datetime.now().strftime("%H:%M:%S")

            if "Scheduled feeding time" in line or "Opening Servo 2" in line:
                self.current_data['last_feed'] = datetime.now().strftime("%H:%M:%S")

            # Relay Status
            if "Relay:" in line:
                if "ON" in line:
                    self.current_data['relay_status'] = "ON"
                else:
                    self.current_data['relay_status'] = "OFF"

            # Food Distance
            if "Food container distance:" in line or "food container distance:" in line:
                match = re.search(r"distance:\s*(\d+)\s*cm", line)
                if match:
                    self.current_data['food_distance'] = match.group(1)

            # Food Alert
            if "Food level low" in line or "Food level Low" in line:
                self.current_data['food_alert'] = "Food level low"
            elif "Food level OK" in line or "Food Status: Normal" in line:
                self.current_data['food_alert'] = "OK"

            # IR Sensor
            if "IR Sensor:" in line:
                match = re.search(r"IR Sensor:\s*(\d+)", line)
                if match:
                    self.current_data['ir_sensor'] = match.group(1)

            if "Food Present:" in line:
                if "Yes" in line:
                    self.current_data['food_present'] = "Yes"
                else:
                    self.current_data['food_present'] = "No"

            # Feeding Schedule
            if "7 AM:" in line or "7am" in line:
                if "Fed" in line:
                    self.current_data['feeding_7am'] = "✅ Fed"
                elif "Skipped" in line:
                    self.current_data['feeding_7am'] = "⏭️ Skipped"

            if "12 PM:" in line or "12pm" in line:
                if "Fed" in line:
                    self.current_data['feeding_12pm'] = "✅ Fed"
                elif "Skipped" in line:
                    self.current_data['feeding_12pm'] = "⏭️ Skipped"

            if "7 PM:" in line or "7pm" in line:
                if "Fed" in line:
                    self.current_data['feeding_7pm'] = "✅ Fed"
                elif "Skipped" in line:
                    self.current_data['feeding_7pm'] = "⏭️ Skipped"

            # Firebase Debug Messages
            if "[OK]" in line:
                # Extract path and value for better tracking
                if "/petFeeder/lastAccess" in line:
                    match = re.search(r"=\s*(.+)$", line)
                    if match:
                        self.current_data['last_access'] = match.group(1).strip()
                elif "/petFeeder/lastFeed" in line:
                    match = re.search(r"=\s*(.+)$", line)
                    if match:
                        self.current_data['last_feed'] = match.group(1).strip()

            self.current_data['last_update'] = datetime.now().strftime("%H:%M:%S")
            self.after(0, self.update_status_display)

        except Exception as e:
            print(f"Error processing line: {e}")

    def append_text(self, text):
        def task():
            self.text_area.config(state=tk.NORMAL)
            self.text_area.insert(tk.END, text + '\n')
            self.text_area.see(tk.END)
            self.text_area.config(state=tk.DISABLED)
        self.after(0, task)

    def clear_display(self):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.config(state=tk.DISABLED)

    def on_closing(self):
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.destroy()

if __name__ == "__main__":
    app = PetFeederMonitorApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
