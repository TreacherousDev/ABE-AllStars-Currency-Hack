import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import base64
import os

# Config
target_string = b"gold" # find snoutlings
varint_tag = 0x18 # ignore protobuff header
replacement_bytes = bytes.fromhex("88 AF BB 5D") # set snoutling count to 802,610

def patch_file(file_path):
    try:
        with open(file_path, "r") as f:
            b64_data = f.read().replace("\n", "").strip()

        while len(b64_data) % 4 != 0:
            b64_data = b64_data[:-1]

        binary = bytearray(base64.b64decode(b64_data))

        pos = binary.find(target_string)
        if pos == -1:
            messagebox.showerror("Error", "Code: 1")
            return

        tag_pos = binary.find(bytes([varint_tag]), pos + len(target_string))
        if tag_pos == -1:
            messagebox.showerror("Error", "Code: 2")
            return

        varint_start = tag_pos + 1
        varint_end = varint_start
        for _ in range(10):
            if varint_end >= len(binary): break
            byte = binary[varint_end]
            varint_end += 1
            if byte & 0x80 == 0:
                break

        binary[varint_start:varint_end] = replacement_bytes

        with open(file_path, "w") as f:
            f.write(base64.b64encode(binary).decode())

        messagebox.showinfo("Success", f"File patched successfully:\n{os.path.basename(file_path)}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

# UI
def select_file():
    file_path = filedialog.askopenfilename(title="Select 'player' File")
    if file_path:
        file_var.set(file_path)
        file_label.configure(text=os.path.basename(file_path))

def run_patch():
    file_path = file_var.get()
    if not file_path:
        messagebox.showwarning("No File", "Please select a file first.")
        return
    patch_file(file_path)

root = tk.Tk()
root.title("ABE All Stars Snoutling Hack")
root.geometry("320x200")
root.resizable(False, False)

style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.configure("TLabel", font=("Segoe UI", 10))

frame = ttk.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

file_var = tk.StringVar()

title_label = ttk.Label(frame, text="ABE All Stars Snoutling Hack", font=("Segoe UI", 14, "bold"))
title_label.pack(pady=(0, 10))

select_btn = ttk.Button(frame, text="Select File", command=select_file)
select_btn.pack(pady=(0, 5))

file_label = ttk.Label(frame, text="No file selected", foreground="gray")
file_label.pack(pady=(0, 10))

patch_btn = ttk.Button(frame, text="Patch File", command=run_patch)
patch_btn.pack(pady=(0, 5))

root.mainloop()

# to build, run this command in terminal at the script folder's directory: pyinstaller --onefile --noconsole abe_allstars_snoutling_hack.py
