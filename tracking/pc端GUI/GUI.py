import queue
import socket
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

import serial
import serial.tools.list_ports


def clamp(value, limit):
    if value > limit:
        return limit
    if value < -limit:
        return -limit
    return value


class PID:
    def __init__(self):
        self.kp = 0.12
        self.ki = 0.0
        self.kd = 0.006
        self.integral = 0.0
        self.last_error = None
        self.integral_limit = 500.0

    def reset(self):
        self.integral = 0.0
        self.last_error = None

    def update(self, error, dt):
        if dt <= 0:
            dt = 0.001

        self.integral += error * dt
        self.integral = clamp(self.integral, self.integral_limit)

        if self.last_error is None:
            derivative = 0.0
        else:
            derivative = (error - self.last_error) / dt

        self.last_error = error
        return self.kp * error + self.ki * self.integral + self.kd * derivative


class SerialWorker:
    def __init__(self):
        self.ser = None
        self.commands = queue.Queue()
        self.running = False
        self.thread = None

    def connect(self, port, baud):
        self.disconnect()
        self.ser = serial.Serial(port, baudrate=baud, timeout=0.02)
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def disconnect(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.5)
        self.thread = None
        if self.ser:
            self.ser.close()
        self.ser = None

    def send(self, text):
        if self.ser and self.ser.is_open:
            self.commands.put(text)
            return True
        return False

    def _loop(self):
        while self.running:
            try:
                text = self.commands.get(timeout=0.05)
            except queue.Empty:
                continue

            try:
                self.ser.write(text.encode("ascii"))
            except serial.SerialException:
                self.running = False


class UdpReceiver:
    def __init__(self, host, port, callback):
        self.host = host
        self.port = port
        self.callback = callback
        self.running = False
        self.thread = None
        self.sock = None

    def start(self):
        self.stop()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(0.2)
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.5)
        self.thread = None
        if self.sock:
            self.sock.close()
        self.sock = None

    def _loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(256)
            except socket.timeout:
                continue
            except OSError:
                break

            text = data.decode("ascii", errors="ignore").strip()
            self.callback(text, addr)


class PidGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PKQ 视觉 PID 自动锁定")
        self.geometry("1040x720")
        self.minsize(920, 620)

        self.serial_worker = SerialWorker()
        self.udp_receiver = None

        self.pid_x = PID()
        self.pid_y = PID()

        self.last_control_time = None
        self.last_packet_time = 0.0
        self.filtered_dx = 0.0
        self.filtered_dy = 0.0
        self.step_accum_x = 0.0
        self.step_accum_y = 0.0

        self.auto_enabled = tk.BooleanVar(value=False)
        self.dry_run = tk.BooleanVar(value=True)

        self.listen_ip = tk.StringVar(value="0.0.0.0")
        self.listen_port = tk.IntVar(value=8899)
        self.esp_port = tk.StringVar(value="COM3")
        self.baud = tk.IntVar(value=115200)

        self.kp_x = tk.DoubleVar(value=0.12)
        self.ki_x = tk.DoubleVar(value=0.0)
        self.kd_x = tk.DoubleVar(value=0.006)
        self.kp_y = tk.DoubleVar(value=0.12)
        self.ki_y = tk.DoubleVar(value=0.0)
        self.kd_y = tk.DoubleVar(value=0.006)

        self.deadzone = tk.IntVar(value=4)
        self.max_steps = tk.IntVar(value=80)
        self.min_step = tk.IntVar(value=1)
        self.min_score = tk.DoubleVar(value=0.5)
        self.send_interval_ms = tk.IntVar(value=25)
        self.smooth_alpha = tk.DoubleVar(value=0.45)
        self.esp_pulse_us = tk.IntVar(value=250)
        self.invert_x = tk.BooleanVar(value=False)
        self.invert_y = tk.BooleanVar(value=False)

        self.status = tk.StringVar(value="未启动")
        self.vision_text = tk.StringVar(value="dx=0  dy=0  score=0")
        self.cmd_text = tk.StringVar(value="最近命令：无")
        self.target_state = tk.StringVar(value="目标：未知")

        self.event_queue = queue.Queue()

        self._build_ui()
        self._refresh_ports()
        self.after(30, self._process_events)
        self.after(200, self._watchdog)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        root = ttk.Frame(self, padding=10)
        root.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(root, width=340)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)

        right = ttk.Frame(root)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_connection(left)
        self._build_pid(left)
        self._build_limits(left)

        ttk.Label(right, text="视觉状态", font=("Microsoft YaHei UI", 14, "bold")).pack(anchor=tk.W)
        ttk.Label(right, textvariable=self.target_state, font=("Microsoft YaHei UI", 12)).pack(anchor=tk.W, pady=(8, 0))
        ttk.Label(right, textvariable=self.vision_text, font=("Consolas", 13)).pack(anchor=tk.W, pady=(4, 0))
        ttk.Label(right, textvariable=self.cmd_text, font=("Consolas", 11)).pack(anchor=tk.W, pady=(4, 10))

        self.canvas = tk.Canvas(right, bg="#101820", height=360, highlightthickness=1, highlightbackground="#8a96a3")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda _event: self._draw_canvas(self.filtered_dx, self.filtered_dy, False))

        ttk.Label(right, text="日志").pack(anchor=tk.W, pady=(10, 4))
        self.log_box = tk.Text(right, height=10, state=tk.DISABLED)
        self.log_box.pack(fill=tk.BOTH)

        self._draw_canvas(0, 0, False)

    def _build_connection(self, parent):
        frame = ttk.LabelFrame(parent, text="连接")
        frame.pack(fill=tk.X, pady=(0, 10))

        row = ttk.Frame(frame)
        row.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(row, text="UDP端口").pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=self.listen_port, width=8).pack(side=tk.RIGHT)

        row = ttk.Frame(frame)
        row.pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(row, text="启动UDP监听", command=self._start_udp).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="停止监听", command=self._stop_udp).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        row = ttk.Frame(frame)
        row.pack(fill=tk.X, padx=8, pady=6)
        self.port_combo = ttk.Combobox(row, textvariable=self.esp_port, width=10)
        self.port_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="刷新串口", command=self._refresh_ports).pack(side=tk.LEFT, padx=(6, 0))

        row = ttk.Frame(frame)
        row.pack(fill=tk.X, padx=8, pady=6)
        ttk.Checkbutton(row, text="dry-run 只看不动", variable=self.dry_run).pack(side=tk.LEFT)
        ttk.Button(row, text="连接ESP32", command=self._connect_esp).pack(side=tk.RIGHT)

        row = ttk.Frame(frame)
        row.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(row, text="ESP脉冲半周期us").pack(side=tk.LEFT)
        ttk.Spinbox(row, textvariable=self.esp_pulse_us, from_=80, to=2000, increment=10, width=8).pack(side=tk.RIGHT)

        ttk.Checkbutton(frame, text="启用自动锁定", variable=self.auto_enabled, command=self._reset_controller).pack(anchor=tk.W, padx=8, pady=(4, 8))

    def _build_pid(self, parent):
        frame = ttk.LabelFrame(parent, text="PID 参数")
        frame.pack(fill=tk.X, pady=(0, 10))

        self._spin(frame, "X Kp", self.kp_x, 0.0, 2.0, 0.005)
        self._spin(frame, "X Ki", self.ki_x, 0.0, 1.0, 0.001)
        self._spin(frame, "X Kd", self.kd_x, 0.0, 1.0, 0.001)
        self._spin(frame, "Y Kp", self.kp_y, 0.0, 2.0, 0.005)
        self._spin(frame, "Y Ki", self.ki_y, 0.0, 1.0, 0.001)
        self._spin(frame, "Y Kd", self.kd_y, 0.0, 1.0, 0.001)

        row = ttk.Frame(frame)
        row.pack(fill=tk.X, padx=8, pady=(4, 8))
        ttk.Checkbutton(row, text="X反向", variable=self.invert_x).pack(side=tk.LEFT)
        ttk.Checkbutton(row, text="Y反向", variable=self.invert_y).pack(side=tk.LEFT, padx=(18, 0))

    def _build_limits(self, parent):
        frame = ttk.LabelFrame(parent, text="平滑和安全限制")
        frame.pack(fill=tk.X, pady=(0, 10))

        self._spin(frame, "死区像素", self.deadzone, 0, 80, 1)
        self._spin(frame, "单次最大步数", self.max_steps, 1, 300, 1)
        self._spin(frame, "最小步进", self.min_step, 0, 20, 1)
        self._spin(frame, "最低置信度", self.min_score, 0.0, 1.0, 0.05)
        self._spin(frame, "发送间隔ms", self.send_interval_ms, 10, 500, 5)
        self._spin(frame, "误差平滑alpha", self.smooth_alpha, 0.0, 1.0, 0.05)

        ttk.Button(frame, text="急停 / 关闭自动", command=self._emergency_stop).pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(frame, textvariable=self.status, wraplength=300).pack(anchor=tk.W, padx=8, pady=(0, 8))

    def _spin(self, parent, label, var, from_, to, inc):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, padx=8, pady=3)
        ttk.Label(row, text=label).pack(side=tk.LEFT)
        ttk.Spinbox(row, textvariable=var, from_=from_, to=to, increment=inc, width=9).pack(side=tk.RIGHT)

    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if ports and self.esp_port.get() not in ports:
            self.esp_port.set(ports[0])

    def _start_udp(self):
        try:
            self.udp_receiver = UdpReceiver(self.listen_ip.get(), self.listen_port.get(), self._on_udp_packet)
            self.udp_receiver.start()
        except OSError as exc:
            messagebox.showerror("UDP错误", str(exc))
            return

        self.status.set(f"UDP监听中：{self.listen_port.get()}")
        self._log(f"UDP listening on {self.listen_port.get()}")

    def _stop_udp(self):
        if self.udp_receiver:
            self.udp_receiver.stop()
            self.udp_receiver = None
        self.status.set("UDP已停止")

    def _connect_esp(self):
        if self.dry_run.get():
            self.status.set("dry-run 模式，不连接 ESP32")
            self._log("dry-run enabled, ESP32 not opened")
            return

        try:
            self.serial_worker.connect(self.esp_port.get(), self.baud.get())
        except serial.SerialException as exc:
            messagebox.showerror("串口错误", str(exc))
            return

        self.status.set(f"ESP32已连接：{self.esp_port.get()}")
        self._log(f"ESP32 serial opened: {self.esp_port.get()}")
        self.serial_worker.send(f"P {self.esp_pulse_us.get()}\n")
        self._log(f"send speed: P {self.esp_pulse_us.get()}")

    def _on_udp_packet(self, text, addr):
        if text == "LOST":
            self.event_queue.put(("lost", None))
            return

        parts = text.split(",")
        if len(parts) != 4 or parts[0] != "TARGET":
            self._log(f"bad packet: {text}")
            return

        try:
            dx = int(parts[1])
            dy = int(parts[2])
            score = float(parts[3])
        except ValueError:
            self._log(f"bad value: {text}")
            return

        self.event_queue.put(("target", (dx, dy, score)))

    def _update_pid_values(self):
        self.pid_x.kp = self.kp_x.get()
        self.pid_x.ki = self.ki_x.get()
        self.pid_x.kd = self.kd_x.get()
        self.pid_y.kp = self.kp_y.get()
        self.pid_y.ki = self.ki_y.get()
        self.pid_y.kd = self.kd_y.get()

    def _handle_target(self, dx, dy, score):
        self.last_packet_time = time.time()

        alpha = self.smooth_alpha.get()
        self.filtered_dx = alpha * dx + (1.0 - alpha) * self.filtered_dx
        self.filtered_dy = alpha * dy + (1.0 - alpha) * self.filtered_dy

        display_dx = int(self.filtered_dx)
        display_dy = int(self.filtered_dy)

        self.target_state.set("目标：已锁定")
        self.vision_text.set(f"dx={dx}  dy={dy}  filtered=({display_dx},{display_dy})  score={score:.2f}")
        self._draw_canvas(self.filtered_dx, self.filtered_dy, True)

        if not self.auto_enabled.get():
            return
        if score < self.min_score.get():
            return

        now = time.time()
        interval = self.send_interval_ms.get() / 1000.0

        if self.last_control_time is None:
            dt = interval
        else:
            dt = now - self.last_control_time

        if dt < interval:
            return

        self._update_pid_values()

        x_error = self.filtered_dx
        y_error = -self.filtered_dy

        if abs(x_error) <= self.deadzone.get():
            x_out = 0.0
            self.pid_x.reset()
        else:
            x_out = self.pid_x.update(x_error, dt)

        if abs(self.filtered_dy) <= self.deadzone.get():
            y_out = 0.0
            self.pid_y.reset()
        else:
            y_out = self.pid_y.update(y_error, dt)

        if self.invert_x.get():
            x_out = -x_out
        if self.invert_y.get():
            y_out = -y_out

        self.step_accum_x += x_out
        self.step_accum_y += y_out

        x_steps = int(self.step_accum_x)
        y_steps = int(self.step_accum_y)

        min_step = self.min_step.get()
        if x_steps == 0 and abs(x_error) > self.deadzone.get() and abs(self.step_accum_x) >= 0.35 and min_step > 0:
            x_steps = min_step if self.step_accum_x > 0 else -min_step
        if y_steps == 0 and abs(self.filtered_dy) > self.deadzone.get() and abs(self.step_accum_y) >= 0.35 and min_step > 0:
            y_steps = min_step if self.step_accum_y > 0 else -min_step

        x_steps = int(clamp(x_steps, self.max_steps.get()))
        y_steps = int(clamp(y_steps, self.max_steps.get()))

        self.step_accum_x -= x_steps
        self.step_accum_y -= y_steps
        self.last_control_time = now

        if x_steps == 0 and y_steps == 0:
            self.cmd_text.set("最近命令：centered")
            return

        cmd = f"M {x_steps} {y_steps}\n"
        self.cmd_text.set(f"最近命令：{cmd.strip()}")

        if self.dry_run.get():
            self._log(f"dry {cmd.strip()}  dx={dx} dy={dy} f=({display_dx},{display_dy}) score={score:.2f}")
        else:
            ok = self.serial_worker.send(cmd)
            if not ok:
                self._log("ESP32未连接，命令未发送")

    def _handle_lost(self):
        self.target_state.set("目标：丢失")
        self._draw_canvas(0, 0, False)
        self._reset_controller()

    def _process_events(self):
        while True:
            try:
                kind, payload = self.event_queue.get_nowait()
            except queue.Empty:
                break

            if kind == "target":
                self._handle_target(*payload)
            elif kind == "lost":
                self._handle_lost()

        self.after(20, self._process_events)

    def _watchdog(self):
        if self.last_packet_time and time.time() - self.last_packet_time > 1.0:
            self.target_state.set("目标：超过1秒无数据")
            self._reset_controller()
        self.after(200, self._watchdog)

    def _draw_canvas(self, dx, dy, found):
        self.canvas.delete("all")
        w = max(self.canvas.winfo_width(), 1)
        h = max(self.canvas.winfo_height(), 1)
        cx = w // 2
        cy = h // 2

        self.canvas.create_line(cx, 0, cx, h, fill="#44515f", dash=(5, 5))
        self.canvas.create_line(0, cy, w, cy, fill="#44515f", dash=(5, 5))
        self.canvas.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, outline="#8ea0b5", width=2)

        if found:
            tx = int(cx + dx)
            ty = int(cy + dy)
            tx = max(8, min(w - 8, tx))
            ty = max(8, min(h - 8, ty))
            self.canvas.create_line(cx, cy, tx, ty, fill="#eab308", width=2)
            self.canvas.create_oval(tx - 7, ty - 7, tx + 7, ty + 7, fill="#22c55e", outline="")
            self.canvas.create_text(12, 12, anchor=tk.NW, text=f"dx={int(dx)}, dy={int(dy)}", fill="#d1fae5", font=("Consolas", 12))
        else:
            self.canvas.create_text(12, 12, anchor=tk.NW, text="target lost", fill="#fecaca", font=("Consolas", 12))

    def _reset_controller(self):
        self.pid_x.reset()
        self.pid_y.reset()
        self.last_control_time = None
        self.step_accum_x = 0.0
        self.step_accum_y = 0.0
        self.status.set("自动锁定已启用" if self.auto_enabled.get() else "自动锁定已关闭")

    def _emergency_stop(self):
        self.auto_enabled.set(False)
        self._reset_controller()
        self.status.set("已急停：自动锁定关闭")
        self._log("emergency stop")

    def _log(self, text):
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state=tk.DISABLED)

    def _on_close(self):
        self._stop_udp()
        self.serial_worker.disconnect()
        self.destroy()


if __name__ == "__main__":
    PidGui().mainloop()
