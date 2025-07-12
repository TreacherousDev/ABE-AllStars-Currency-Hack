import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import base64
import os

# Config
data_entries = [
    {
        "label": "Lucky Coins",
        "key": b"lucky_coin",
        "tag": 0x18,
        "max_value": 50_000
    },
    {
        "label": "Snoutlings",
        "key": b"gold",
        "tag": 0x18,
        "max_value": 1_000_000
    },
    {
        "label": "Friendship Essence",
        "key": b"friendship_essence",
        "tag": 0x18,
        "max_value": 50_000
    }
]

XOR_MASK = 0xBA2E8BA  # encryption mask used by game, credits to heroic

def encode_varint(value):
    value ^= XOR_MASK
    out = bytearray()
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return out

def decode_varint(data):
    result = 0
    shift = 0
    for i, b in enumerate(data):
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result ^ XOR_MASK, i + 1
        shift += 7
    return None, 0

# fixes corruption bug in 0.2
def find_exact_key_block(binary, key_bytes, tag):
    # Match pattern: 0A <len> <key_bytes> 10 01 18 <varint>
    pattern = b'\x0A' + bytes([len(key_bytes)]) + key_bytes + b'\x10\x01' + bytes([tag])
    return binary.find(pattern)

def patch_file(file_path, values):
    try:
        with open(file_path, "r") as f:
            b64_data = f.read().replace("\n", "").strip()

        while len(b64_data) % 4 != 0:
            b64_data = b64_data[:-1]

        binary = bytearray(base64.b64decode(b64_data))

        for entry in data_entries:
            key_bytes = entry["key"]
            varint_tag = entry["tag"]
            new_value = values.get(entry["label"])
            if new_value is None:
                continue

            tag_pos = find_exact_key_block(binary, key_bytes, varint_tag)
            if tag_pos == -1:
                messagebox.showerror("Error", f"{entry['label']}: Code 3 (exact key structure not found)")
                continue

            varint_start = tag_pos + len(b'\x0A') + 1 + len(key_bytes) + len(b'\x10\x01') + 1
            varint_bytes = binary[varint_start:varint_start + 10]
            current_value, length = decode_varint(varint_bytes)

            if current_value is None:
                messagebox.showerror("Error", f"{entry['label']}: Failed to decode current value")
                continue

            varint_end = varint_start + length
            binary[varint_start:varint_end] = encode_varint(new_value)

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

    try:
        with open(file_path, "r") as f:
            b64_data = f.read().replace("\n", "").strip()
        while len(b64_data) % 4 != 0:
            b64_data = b64_data[:-1]
        binary = bytearray(base64.b64decode(b64_data))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load file: {str(e)}")
        return

    values = {}
    for entry in data_entries:
        key_bytes = entry["key"]
        varint_tag = entry["tag"]

        tag_pos = find_exact_key_block(binary, key_bytes, varint_tag)
        if tag_pos == -1:
            messagebox.showerror("Error", f"{entry['label']}: Code 3 (exact key structure not found)")
            continue

        varint_start = tag_pos + len(b'\x0A') + 1 + len(key_bytes) + len(b'\x10\x01') + 1
        varint_bytes = binary[varint_start:varint_start + 10]
        current_value, length = decode_varint(varint_bytes)

        if current_value is None:
            messagebox.showerror("Error", f"{entry['label']}: Failed to decode current value")
            continue

        try:
            value = simpledialog.askinteger(
                title=" ",
                prompt=f"{entry['label']}\n\nCurrent value: {current_value}\nEnter new value:",
                minvalue=0,
                maxvalue=entry["max_value"],
                parent=root
            )
            if value is not None:
                values[entry['label']] = value
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input for {entry['label']}: {str(e)}")
            return

    patch_file(file_path, values)

root = tk.Tk()
root.title("ABE All Stars Currency Hack")
root.geometry("340x200")
root.resizable(False, False)

style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.configure("TLabel", font=("Segoe UI", 10))

frame = ttk.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

file_var = tk.StringVar()

title_label = ttk.Label(frame, text="ABE All Stars Currency Hack", font=("Segoe UI", 14, "bold"))
title_label.pack(pady=(0, 10))

select_btn = ttk.Button(frame, text="Select File", command=select_file)
select_btn.pack(pady=(0, 5))

file_label = ttk.Label(frame, text="No file selected", foreground="gray")
file_label.pack(pady=(0, 10))

patch_btn = ttk.Button(frame, text="Patch File", command=run_patch)
patch_btn.pack(pady=(0, 5))

root.mainloop()

# to build, run this command in terminal at the script folder's directory: pyinstaller --onefile --noconsole abe_allstars_currency_hack.py
