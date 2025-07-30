import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import serial
import serial.tools.list_ports
import threading
import datetime

class SerialMonitorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Arduino Battery Monitor")
        self.ser = None
        self.thread = None
        self.running = False
        self.log_file = None

        # Порт і швидкість
        self.port_var = tk.StringVar()
        self.baudrate = 9600

        # Елементи GUI
        frame = ttk.Frame(master)
        frame.pack(padx=10, pady=10, fill='x')

        ttk.Label(frame, text="COM порт:").pack(side='left')
        self.port_combo = ttk.Combobox(frame, textvariable=self.port_var, width=15, state='readonly')
        self.port_combo.pack(side='left', padx=5)
        self.refresh_ports()

        self.refresh_button = ttk.Button(frame, text="Оновити", command=self.refresh_ports)
        self.refresh_button.pack(side='left', padx=5)

        self.connect_button = ttk.Button(frame, text="Підключитись", command=self.toggle_connection)
        self.connect_button.pack(side='left', padx=5)

        # Текстове поле для логів
        self.text_area = ScrolledText(master, state='disabled', width=80, height=20)
        self.text_area.pack(padx=10, pady=10)

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [p.device for p in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)
        else:
            self.port_combo.set('')

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        port = self.port_var.get()
        if not port:
            messagebox.showwarning("Помилка", "Оберіть COM порт")
            return
        try:
            self.ser = serial.Serial(port, self.baudrate, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self.read_serial)
            self.thread.daemon = True
            self.thread.start()

            # Відкриваємо лог файл
            log_filename = datetime.datetime.now().strftime("battery_log_%Y%m%d_%H%M%S.txt")
            self.log_file = open(log_filename, "w", encoding="utf-8")

            self.append_text(f"Підключено до {port}\n")
            self.connect_button.config(text="Відключитись")
            self.port_combo.config(state='disabled')
            self.refresh_button.config(state='disabled')

        except serial.SerialException as e:
            messagebox.showerror("Помилка", f"Не вдалося відкрити порт {port}:\n{e}")

    def disconnect(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.append_text("Відключено\n")
        self.connect_button.config(text="Підключитись")
        self.port_combo.config(state='readonly')
        self.refresh_button.config(state='normal')

        if self.log_file:
            self.log_file.close()
            self.log_file = None

    def append_text(self, text):
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)
        self.text_area.configure(state='disabled')

        # Лог у файл
        if self.log_file:
            self.log_file.write(text)
            self.log_file.flush()

    def read_serial(self):
        while self.running:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8', errors='replace')
                    self.append_text(line)
            except Exception as e:
                self.append_text(f"Помилка читання: {e}\n")
                self.running = False

    def on_closing(self):
        if self.ser and self.ser.is_open:
            self.disconnect()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
