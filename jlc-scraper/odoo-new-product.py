import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Text, Scrollbar
from PIL import Image, ImageTk
import xmlrpc.client
import traceback
import string
import os

# Odoo connection details
url = "https://dev17.apps.bluerobotics.com/"
db = "20240809"
username = "engineering@bluerobotics.com"
password = "VqqpHGVZCh3yfj7"

# Establishing connection
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')


def show_error_window(error_message):
    """Display a new window with the error message."""
    error_window = Toplevel(root)
    error_window.title("Error Details")
    error_window.geometry("600x400")
    error_window.configure(bg="#2e2e2e")

    # Text widget for displaying the error message
    text_widget = Text(error_window, wrap='word', bg="#3e3e3e", fg="#f0f0f0", insertbackground="#f0f0f0")
    text_widget.insert('1.0', error_message)
    text_widget.config(state='disabled')  # Make it read-only
    text_widget.pack(expand=True, fill='both', padx=10, pady=10)

    # Scrollbar for the text widget
    scrollbar = Scrollbar(error_window, command=text_widget.yview)
    scrollbar.pack(side='right', fill='y')
    text_widget.config(yscrollcommand=scrollbar.set)


def submit_new_part():
    # Retrieve values from the fields
    bree_suffix = bree_suffix_entry.get()
    rev = rev_combobox.get()
    description = description_entry.get()
    part_type = type_var.get()  # Get the selected type from the dropdown
    category = category_entry.get()
    sales_price = lst_price_entry.get()
    cost_price = standard_price_entry.get()

    # Basic validation
    if not rev:
        messagebox.showerror("Input Error", "Rev is required and must be selected.")
        return

    # Construct the full BREE number
    bree_number = f"BREE- {bree_suffix}"

    # Attempt to create the new part in Odoo
    try:
        # Fetch category ID from name (or create a new category if not found)
        category_id = models.execute_kw(db, uid, password, 'product.category', 'search', [[['name', '=', category]]])
        if not category_id:
            category_id = models.execute_kw(db, uid, password, 'product.category', 'create', [{'name': category}])
        else:
            category_id = category_id[0]

        # Create the new product
        new_product_id = models.execute_kw(db, uid, password, 'product.product', 'create', [{
            'name': bree_number,
            'default_code': rev,
            'type': part_type,
            'categ_id': category_id,
            'description': description,
            'lst_price': float(sales_price) if sales_price else 0.0,
            'standard_price': float(cost_price) if cost_price else 0.0,
        }])

        messagebox.showinfo("Success", f"New part created with ID {new_product_id}")
    except Exception as e:
        # Capture the full traceback to show the detailed error
        error_message = traceback.format_exc()
        show_error_window(error_message)


# Setting up the Tkinter window with dark mode
root = tk.Tk()
root.title("Add New Part to Odoo")
root.configure(bg="#2e2e2e")

# Configure the window grid to center all widgets vertically and horizontally
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(11, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# Applying a dark style with Consolas font
font_settings = ("Consolas", 10)
bree_prefix_font = ("Consolas", 12)  # Slightly larger font for BREE-
style = ttk.Style()
style.theme_use("clam")

style.configure("TLabel", background="#2e2e2e", foreground="#f0f0f0", font=font_settings)
style.configure("TEntry", fieldbackground="#3e3e3e", foreground="#f0f0f0", insertcolor="#f0f0f0", font=font_settings)
style.configure("TButton", background="#3e3e3e", foreground="#f0f0f0", font=font_settings)
style.map("TButton",
          background=[("active", "#5e5e5e"), ("pressed", "#4e4e4e")])

# Adding the BR logo
try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Current working directory:", os.getcwd())
    br_logo_image = Image.open("br_logo.png")
    desired_width = 200
    aspect_ratio = br_logo_image.width / br_logo_image.height
    new_height = int(desired_width / aspect_ratio)
    br_logo_image = br_logo_image.resize((desired_width, new_height), Image.LANCZOS)
    br_logo_photo = ImageTk.PhotoImage(br_logo_image)
    br_logo_label = tk.Label(root, image=br_logo_photo, bg="#2e2e2e")
    br_logo_label.grid(row=1, column=0, columnspan=2, pady=5)
except Exception as e:
    messagebox.showerror("Error", f"Failed to load BR logo image: {e}")

# Adding the Odoo logo
try:
    logo_image = Image.open("odoo_logo.png")
    desired_width = 120  # Smaller width for the Odoo logo
    aspect_ratio = logo_image.width / logo_image.height
    new_height = int(desired_width / aspect_ratio)
    logo_image = logo_image.resize((desired_width, new_height), Image.LANCZOS)
    logo_photo = ImageTk.PhotoImage(logo_image)
    logo_label = tk.Label(root, image=logo_photo, bg="#2e2e2e")
    logo_label.grid(row=2, column=0, columnspan=2, pady=(5, 15))  # Added padding below the image
except Exception as e:
    messagebox.showerror("Error", f"Failed to load Odoo logo image: {e}")

# Creating labels and entry fields with consistent padding
padx, pady = 10, 5

# Frame for BREE Number
bree_frame = ttk.Frame(root, style="TFrame")
bree_frame.grid(row=3, column=1, padx=padx, pady=pady, sticky="w")

# BREE Number
ttk.Label(root, text="BREE Number:").grid(row=3, column=0, padx=padx, pady=pady, sticky="e")
bree_prefix_label = ttk.Label(bree_frame, text="BREE- ", background="#2e2e2e", foreground="#f0f0f0",
                              font=bree_prefix_font)
bree_prefix_label.pack(side="left")
bree_suffix_entry = ttk.Entry(bree_frame, width=25, font=font_settings)
bree_suffix_entry.pack(side="left")

# Rev (Dropdown A-Z)
ttk.Label(root, text="Rev:").grid(row=4, column=0, padx=padx, pady=pady, sticky="e")
rev_combobox = ttk.Combobox(root, values=list(string.ascii_uppercase), state="readonly", width=28, font=font_settings)
rev_combobox.grid(row=4, column=1, padx=padx, pady=pady, sticky="w")

# Description
ttk.Label(root, text="Description:").grid(row=5, column=0, padx=padx, pady=pady, sticky="e")
description_entry = ttk.Entry(root, width=30, font=font_settings)
description_entry.grid(row=5, column=1, padx=padx, pady=pady, sticky="w")

# Type
ttk.Label(root, text="Type:").grid(row=6, column=0, padx=padx, pady=pady, sticky="e")
type_var = tk.StringVar()
type_options = ['product', 'consumable', 'service']
type_var.set(type_options[0])  # Set default value
type_menu = ttk.Combobox(root, textvariable=type_var, values=type_options, state="readonly", width=28,
                         font=font_settings)
type_menu.grid(row=6, column=1, padx=padx, pady=pady, sticky="w")

# Category
ttk.Label(root, text="Category:").grid(row=7, column=0, padx=padx, pady=pady, sticky="e")
category_entry = ttk.Entry(root, width=30, font=font_settings)
category_entry.grid(row=7, column=1, padx=padx, pady=pady, sticky="w")

# Sales Price
ttk.Label(root, text="Sales Price:").grid(row=8, column=0, padx=padx, pady=pady, sticky="e")
lst_price_entry = ttk.Entry(root, width=30, font=font_settings)
lst_price_entry.grid(row=8, column=1, padx=padx, pady=pady, sticky="w")

# Cost Price
ttk.Label(root, text="Cost Price:").grid(row=9, column=0, padx=padx, pady=pady, sticky="e")
standard_price_entry = ttk.Entry(root, width=30, font=font_settings)
standard_price_entry.grid(row=9, column=1, padx=padx, pady=pady, sticky="w")

# Create New Item button centered across both columns
create_button = ttk.Button(root, text="Create New Item", command=submit_new_part)
create_button.grid(row=10, column=0, columnspan=2, pady=20)

# Center the window on the screen
root.update_idletasks()
window_width = root.winfo_width()
window_height = root.winfo_height()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

position_top = int((screen_height - window_height) / 2)
position_left = int((screen_width - window_width) / 2)

root.geometry(f"{window_width}x{window_height}+{position_left}+{position_top}")

# Keep the references to the images
root.br_logo_photo = br_logo_photo
root.logo_photo = logo_photo

# Running the Tkinter event loop
root.mainloop()
