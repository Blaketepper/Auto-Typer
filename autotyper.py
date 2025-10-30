#!/usr/bin/env python3
"""
Auto Typer — Tkinter GUI (imported as tk)
Save as: auto_typer_tk.py
Requires: pyautogui (only if not running in Test Mode)
"""

import threading
import time
import random
import tkinter as tk
from tkinter import ttk, messagebox

# Try to import pyautogui but allow the app to run without it in Test Mode.
try:
    import pyautogui
    PY_AUTO_GUI_AVAILABLE = True
    # pyautogui safety: move mouse to top-left quickly to abort.
    pyautogui.FAILSAFE = True
except Exception:
    PY_AUTO_GUI_AVAILABLE = False

class AutoTyperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Typer — Tkinter")
        self.stop_event = threading.Event()
        self.worker_thread = None

        # Layout
        main = ttk.Frame(root, padding=12)
        main.grid(row=0, column=0, sticky="nsew")
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        # Message label + text
        ttk.Label(main, text="Message to type:").grid(row=0, column=0, sticky="w")
        self.text = tk.Text(main, width=60, height=8)
        self.text.grid(row=1, column=0, columnspan=4, pady=(0,10), sticky="nsew")
        self.text.insert("1.0", "Hello from AutoTyper!\n(Replace this with your own message.)")

        # Per-character speed
        ttk.Label(main, text="Char delay (sec):").grid(row=2, column=0, sticky="w")
        self.char_delay_var = tk.DoubleVar(value=0.03)
        self.char_spin = ttk.Spinbox(main, from_=0.0, to=2.0, increment=0.01, textvariable=self.char_delay_var, width=8)
        self.char_spin.grid(row=2, column=1, sticky="w")

        # Delay between messages
        ttk.Label(main, text="Delay between messages (sec):").grid(row=2, column=2, sticky="w")
        self.msg_delay_var = tk.DoubleVar(value=1.5)
        self.msg_spin = ttk.Spinbox(main, from_=0.0, to=600.0, increment=0.1, textvariable=self.msg_delay_var, width=8)
        self.msg_spin.grid(row=2, column=3, sticky="w")

        # Randomize delay
        self.randomize_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main, text="Randomize delay ± (sec)", variable=self.randomize_var).grid(row=3, column=0, sticky="w")
        self.random_range_var = tk.DoubleVar(value=0.25)
        self.random_range_spin = ttk.Spinbox(main, from_=0.0, to=10.0, increment=0.01, textvariable=self.random_range_var, width=8)
        self.random_range_spin.grid(row=3, column=1, sticky="w")

        # Press Enter after message
        self.enter_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main, text="Press Enter after message", variable=self.enter_var).grid(row=3, column=2, sticky="w")

        # Repeat count
        ttk.Label(main, text="Repeat (0 = infinite):").grid(row=4, column=0, sticky="w")
        self.repeat_var = tk.IntVar(value=10)
        self.repeat_spin = ttk.Spinbox(main, from_=0, to=1000000, increment=1, textvariable=self.repeat_var, width=10)
        self.repeat_spin.grid(row=4, column=1, sticky="w")

        # Countdown seconds
        ttk.Label(main, text="Countdown before start (sec):").grid(row=4, column=2, sticky="w")
        self.countdown_var = tk.IntVar(value=5)
        self.countdown_spin = ttk.Spinbox(main, from_=0, to=60, increment=1, textvariable=self.countdown_var, width=8)
        self.countdown_spin.grid(row=4, column=3, sticky="w")

        # Test mode (simulate)
        self.test_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main, text="Test mode (do NOT send keystrokes)", variable=self.test_mode_var).grid(row=5, column=0, sticky="w")

        # Buttons
        self.start_btn = ttk.Button(main, text="Start", command=self.start)
        self.start_btn.grid(row=6, column=0, pady=(10,0), sticky="w")

        self.stop_btn = ttk.Button(main, text="Stop", command=self.stop, state="disabled")
        self.stop_btn.grid(row=6, column=1, pady=(10,0), sticky="w")

        self.clear_btn = ttk.Button(main, text="Clear Text", command=lambda: self.text.delete("1.0", "end"))
        self.clear_btn.grid(row=6, column=2, pady=(10,0), sticky="w")

        self.help_btn = ttk.Button(main, text="Info", command=self.show_info)
        self.help_btn.grid(row=6, column=3, pady=(10,0), sticky="e")

        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main, textvariable=self.status_var).grid(row=7, column=0, columnspan=4, pady=(8,0), sticky="w")

        # Make UI expand nicely
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

    def show_info(self):
        info = (
            "Auto Typer (Tkinter)\n\n"
            "- Focus the target input window after pressing Start (use the countdown to switch windows).\n"
            "- Test Mode simulates typing without sending keystrokes (useful for verifying settings).\n"
            "- pyautogui must be installed for real typing. Move the mouse to the top-left corner to trigger pyautogui fail-safe.\n\n"
            "Use responsibly — do not spam or violate terms of service."
        )
        messagebox.showinfo("Info — Auto Typer", info)

    def start(self):
        # Validate pyautogui availability if not in test mode
        if not self.test_mode_var.get() and not PY_AUTO_GUI_AVAILABLE:
            messagebox.showerror("Missing dependency", "pyautogui is required for real typing. Install it with:\n\npip install pyautogui")
            return

        # Prevent multiple starts
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo("Already running", "Auto Typer is already running.")
            return

        self.stop_event.clear()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("Starting...")

        # Launch worker thread
        self.worker_thread = threading.Thread(target=self.worker, daemon=True)
        self.worker_thread.start()

    def stop(self):
        self.stop_event.set()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("Stopping...")

    def worker(self):
        try:
            # Read settings
            message = self.text.get("1.0", "end").rstrip("\n")
            if message.strip() == "":
                self.status_var.set("No message to type.")
                self.start_btn.config(state="normal")
                self.stop_btn.config(state="disabled")
                return

            char_delay = float(self.char_delay_var.get())
            base_msg_delay = float(self.msg_delay_var.get())
            randomize = self.randomize_var.get()
            random_range = float(self.random_range_var.get())
            press_enter = self.enter_var.get()
            repeat = int(self.repeat_var.get())
            countdown = int(self.countdown_var.get())
            test_mode = self.test_mode_var.get()

            # Countdown so user can focus target window
            for i in range(countdown, 0, -1):
                if self.stop_event.is_set():
                    self.status_var.set("Stopped.")
                    self.start_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    return
                self.status_var.set(f"Starting in {i}...")
                time.sleep(1)

            # Main loop
            self.status_var.set("Typing...")
            i = 0
            while (repeat == 0) or (i < repeat):
                if self.stop_event.is_set():
                    break
                i += 1
                self.status_var.set(f"Typing message {i}{' (test mode)' if test_mode else ''}...")

                # If test mode, print to console; else send keystrokes
                if test_mode:
                    # Show each character simulation with delay
                    for ch in message:
                        if self.stop_event.is_set():
                            break
                        print(ch, end="", flush=True)
                        time.sleep(char_delay)
                    print()  # newline after message
                    if press_enter:
                        print("<ENTER>")
                else:
                    # Use pyautogui to type
                    try:
                        pyautogui.typewrite(message, interval=char_delay)
                        if press_enter:
                            pyautogui.press("enter")
                    except Exception as e:
                        # If typing fails, stop and show error
                        self.status_var.set(f"Typing failed: {e}")
                        break

                # After typing message
                if self.stop_event.is_set():
                    break

                # Compute next delay (with optional randomization)
                delay = base_msg_delay
                if randomize and random_range > 0:
                    delta = random.uniform(-random_range, random_range)
                    delay = max(0.0, base_msg_delay + delta)
                # Sleep in chunks so Stop can be responsive
                slept = 0.0
                while slept < delay:
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)
                    slept += 0.1

            # Done
            if self.stop_event.is_set():
                self.status_var.set("Stopped.")
            else:
                self.status_var.set("Completed.")
        finally:
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")

def main():
    root = tk.Tk()
    style = ttk.Style(root)
    # Optionally set a platform-friendly theme
    try:
        style.theme_use('clam')
    except Exception:
        pass
    app = AutoTyperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
