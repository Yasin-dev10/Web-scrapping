import tkinter as tk
from tkinter import ttk
import subprocess
import os

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
            "1. Facebook Scraper (General)": "facebook_scraper_gui.py",
            "2. Scraping Data (New Scraper)": "new_scrapper.py",
            "3. Telecom Complaints Scraper": "telecom_complaints_scraper_gui.py",
            "4. CSV Merger (Isku darka CSV)": "csv_merger_gui.py",
            "5. Data Validator (Hubinta Xogta)": "data_validator_gui.py",
            "6. Data Separator (Kala saarista Crime/Not Crime)": "data_separator.py",
            "7. Split Crime Data (Isku miisaanid)": "split_crime_data.py",
            "8. Crime Only Filter": "scrape_crime_only_gui.py",
            "9. Not Crime Only Filter": "scrape_not_crime_only_gui.py"
        }

        # Create Buttons dynamically
        for text, script in self.tools.items():
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
