import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import re
from datetime import datetime

class SmartHomeMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🏠 Smart Home System Monitor")
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
            'temperature': '--',
            'humidity': '--',
            'light': '--',
            'motion': 'No Motion',
            'door': 'Closed',
            'gas': 'Normal',
            'flame': 'Normal',
            'wifi_status': 'Unknown',
            'firebase_status': 'Unknown',
            'last_update': 'Never'
        }

        self.create_widgets()
        self.populate_ports()

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title_label = ttk.Label(main_frame, text="🏠 Smart Home System Monitor", style='Title.TLabel')
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

        data_frame = ttk.LabelFrame(main_frame, text="📝 Live Data Stream", padding=10)
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
        env_frame = ttk.LabelFrame(parent, text="🌡️ Environmental", padding=10)
        env_frame.pack(fill=tk.X, pady=5)

        env_grid = ttk.Frame(env_frame)
        env_grid.pack(fill=tk.X)

        ttk.Label(env_grid, text="Temperature:", style='Status.TLabel').grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.temp_label = ttk.Label(env_grid, text="--°C", style='Status.TLabel')
        self.temp_label.grid(row=0, column=1, sticky='w', padx=(0, 20))

        ttk.Label(env_grid, text="Humidity:", style='Status.TLabel').grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.hum_label = ttk.Label(env_grid, text="--%", style='Status.TLabel')
        self.hum_label.grid(row=0, column=3, sticky='w', padx=(0, 20))

        ttk.Label(env_grid, text="Light Level:", style='Status.TLabel').grid(row=0, column=4, sticky='w', padx=(0, 10))
        self.light_label = ttk.Label(env_grid, text="--V", style='Status.TLabel')
        self.light_label.grid(row=0, column=5, sticky='w')

        sec_frame = ttk.LabelFrame(parent, text="🚨 Security", padding=10)
        sec_frame.pack(fill=tk.X, pady=5)

        sec_grid = ttk.Frame(sec_frame)
        sec_grid.pack(fill=tk.X)

        ttk.Label(sec_grid, text="Motion:", style='Status.TLabel').grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.motion_label = ttk.Label(sec_grid, text="No Motion", style='Status.TLabel')
        self.motion_label.grid(row=0, column=1, sticky='w', padx=(0, 20))

        ttk.Label(sec_grid, text="Door:", style='Status.TLabel').grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.door_label = ttk.Label(sec_grid, text="Closed", style='Status.TLabel')
        self.door_label.grid(row=0, column=3, sticky='w', padx=(0, 20))

        ttk.Label(sec_grid, text="Gas:", style='Status.TLabel').grid(row=0, column=4, sticky='w', padx=(0, 10))
        self.gas_label = ttk.Label(sec_grid, text="Normal", style='Status.TLabel')
        self.gas_label.grid(row=0, column=5, sticky='w', padx=(0, 20))

        ttk.Label(sec_grid, text="Fire:", style='Status.TLabel').grid(row=0, column=6, sticky='w', padx=(0, 10))
        self.flame_label = ttk.Label(sec_grid, text="Normal", style='Status.TLabel')
        self.flame_label.grid(row=0, column=7, sticky='w')

        sys_frame = ttk.LabelFrame(parent, text="⚙️ System", padding=10)
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
        self.temp_label.config(text=f"{self.current_data['temperature']}°C")
        self.hum_label.config(text=f"{self.current_data['humidity']}%")
        self.light_label.config(text=f"{self.current_data['light']}V")
        self.motion_label.config(text=self.current_data['motion'])
        self.door_label.config(text=self.current_data['door'])
        self.gas_label.config(text=self.current_data['gas'])
        self.flame_label.config(text=self.current_data['flame'])
        self.wifi_label.config(text=self.current_data['wifi_status'])
        self.firebase_label.config(text=self.current_data['firebase_status'])
        self.update_label.config(text=self.current_data['last_update'])

        # Color logic for temperature
        try:
            temp = float(self.current_data['temperature'])
            if temp > 35:
                self.temp_label.config(foreground='red')
            elif temp > 30:
                self.temp_label.config(foreground='orange')
            else:
                self.temp_label.config(foreground='#00ff00')
        except:
            self.temp_label.config(foreground='#ffffff')

        # Color logic for humidity
        try:
            hum = float(self.current_data['humidity'])
            if hum < 30:
                self.hum_label.config(foreground='red')
            elif hum < 40:
                self.hum_label.config(foreground='orange')
            else:
                self.hum_label.config(foreground='#00ff00')
        except:
            self.hum_label.config(foreground='#ffffff')

        # Color logic for light
        try:
            light = float(self.current_data['light'])
            if light < 1:
                self.light_label.config(foreground='red')
            elif light < 2:
                self.light_label.config(foreground='orange')
            else:
                self.light_label.config(foreground='#00ff00')
        except:
            self.light_label.config(foreground='#ffffff')

        # Security sensors colors
        self.motion_label.config(foreground='red' if "YES" in self.current_data['motion'] else '#00ff00')
        self.door_label.config(foreground='red' if "OPEN" in self.current_data['door'] else '#00ff00')
        self.gas_label.config(foreground='red' if "LEAK" in self.current_data['gas'] else '#00ff00')
        self.flame_label.config(foreground='red' if "FIRE" in self.current_data['flame'] or "Detected" in self.current_data['flame'] else '#00ff00')

        # System status colors
        self.wifi_label.config(foreground='#00ff00' if "Connected" in self.current_data['wifi_status'] else 'red')
        self.firebase_label.config(foreground='#00ff00' if "Ready" in self.current_data['firebase_status'] else 'red')

    def populate_ports(self):
        ports = serial.tools.list_ports.comports()
        port_names = [port.device for port in ports]
        if port_names:
            self.port_combo['values'] = port_names
            self.port_combo.set(port_names[0])
            self.start_btn.config(state=tk.NORMAL)
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
            if "Connected to WiFi" in line:
                self.current_data['wifi_status'] = "Connected"
            elif "Failed to connect to WiFi" in line:
                self.current_data['wifi_status'] = "Failed"

            # Firebase Status
            if "Firebase.ready(): true" in line:
                self.current_data['firebase_status'] = "Ready"
            elif "Firebase.ready(): false" in line:
                self.current_data['firebase_status'] = "Not Ready"
            elif "Firebase signup OK" in line:
                self.current_data['firebase_status'] = "Connected"

            # Environmental data - matches: "Environment -> Temp: 25.50°C  Humidity: 60.00%  Light: 3.25V"
            if "Environment ->" in line:
                temp_match = re.search(r"Temp:\s*([\d.]+)", line)
                hum_match = re.search(r"Humidity:\s*([\d.]+)", line)
                light_match = re.search(r"Light:\s*([\d.]+)", line)
                
                if temp_match:
                    self.current_data['temperature'] = temp_match.group(1)
                if hum_match:
                    self.current_data['humidity'] = hum_match.group(1)
                if light_match:
                    self.current_data['light'] = light_match.group(1)

            # Security data - NEW PARSING LOGIC
            # Matches: "Security -> Motion: YES | Door: OPEN | Gas: 450"
            if "Security ->" in line:
                # Motion - look for "Motion: YES" or "Motion: NO"
                if "Motion: YES" in line:
                    self.current_data['motion'] = "Motion YES"
                elif "Motion: NO" in line:
                    self.current_data['motion'] = "No Motion"

                # Door - look for "Door: OPEN" or "Door: CLOSED"
                if "Door: OPEN" in line:
                    self.current_data['door'] = "OPEN"
                elif "Door: CLOSED" in line:
                    self.current_data['door'] = "Closed"

                # Gas level - extract numeric value after "Gas: "
                gas_match = re.search(r"\|\s*Gas:\s*([\d.]+)", line)
                if gas_match:
                    gas_val = float(gas_match.group(1))
                    if gas_val > 500:
                        self.current_data['gas'] = "GAS LEAK!"
                    else:
                        self.current_data['gas'] = f"Normal ({gas_val:.0f})"

            # Flame sensor - separate lines
            # Matches: "| flame: 1234"
            if "| flame:" in line:
                flame_match = re.search(r"\|\s*flame:\s*([\d.]+)", line)
                if flame_match:
                    flame_val = float(flame_match.group(1))
                    if flame_val < 1000:
                        self.current_data['flame'] = "FIRE DETECTED!"
                    else:
                        self.current_data['flame'] = f"Normal ({flame_val:.0f})"

            # Flame status string
            # Matches: "| status: Detected" or "| status: norm"
            if "| status:" in line:
                if "Detected" in line:
                    self.current_data['flame'] = "FIRE DETECTED!"
                elif "norm" in line:
                    if "FIRE" not in self.current_data['flame']:  # Don't override if already detected
                        self.current_data['flame'] = "Normal"

            # Alarm triggers
            if "Door Opened - Alarm Triggered" in line:
                self.current_data['door'] = "OPEN - ALARM!"
            if "Fire Detected - Alarm Triggered" in line:
                self.current_data['flame'] = "FIRE DETECTED - ALARM!"

            # Update timestamp
            self.current_data['last_update'] = datetime.now().strftime("%H:%M:%S")
            self.after(0, self.update_status_display)

        except Exception as e:
            print(f"Error processing line '{line}': {e}")

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
    app = SmartHomeMonitorApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()