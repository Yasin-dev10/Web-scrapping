import tkinter as tk
from tkinter import ttk
import subprocess
import os

FONT_FAMILY = "Helvetica"

class MainDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Aaladda Xog-Uruurinta & Kala-Saarista (Main Dashboard)")
        self.root.geometry("600x500")
        self.root.configure(bg="#f0f0f0")

        # Header
        header_frame = tk.Frame(root, bg="#2c3e50", pady=20)
        header_frame.pack(fill=tk.X)
        header_label = tk.Label(header_frame, text="Mideeyaha Barnaamijyada (All-in-One GUI)", font=("Helvetica", 16, "bold"), fg="white", bg="#2c3e50")
        header_label.pack()

        # Instructions
        instruction_label = tk.Label(root, text="Fadlan dooro barnaamijka aad rabto inaad isticmaasho:", font=("Helvetica", 11), bg="#f0f0f0", pady=10)
        instruction_label.pack()

        # Buttons Frame
        btn_frame = tk.Frame(root, bg="#f0f0f0")
        btn_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # Dictionary of tools: Button Text -> Python Script
        self.tools = {
            "1. News & Social Scraper": "news_scraper_gui.py",
            "2. Facebook Crime Scraper": "facebook_scraper_gui.py",
            "3. Crime Filter Tool (Nadiifinta Crime)": "CrimeFilterTool.py",
            "4. Not Crime Filter": "not_crime_filter_gui.py",
            "5. Split Crime Data (Kala Saar)": "split_crime_data.py",
            "6. CSV Merger (Isku darka CSV)": "csv_merger_gui.py",
            "7. Data Validator (Hubinta Xogta)": "data_validator_gui.py",
            "8. Data Separator": "data_separator.py",
            "──────── DATABASE ────────────": None,
            "🗄️  Database Dashboard (Xogta & CSV Download)": "db_dashboard.py",
        }

        # Create Buttons dynamically
        for text, script in self.tools.items():
            if script is None:
                # Separator / divider label
                tk.Label(btn_frame, text=text, font=(FONT_FAMILY, 9),
                         bg="#f0f0f0", fg="#999999").pack(pady=(8, 2))
                continue
            btn = ttk.Button(btn_frame, text=text, command=lambda s=script: self.launch_script(s), width=50)
            btn.pack(pady=5, ipady=5)

    def launch_script(self, script_name):
        try:
            # Check if file exists
            if os.path.exists(script_name):
                # Run the script in a separate process
                subprocess.Popen(["python", script_name])
            else:
                tk.messagebox.showerror("Error", f"Faylka '{script_name}' lama helin!")
        except Exception as e:
            tk.messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = MainDashboard(root)
    root.mainloop()
