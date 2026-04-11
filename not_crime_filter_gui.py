import os
import re
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import threading

# ── Crime keywords (Af-Soomaali) - We need them to identify what NOT to include.
CRIME_KEYWORDS_HIGH = [
    "dilka", "dilaan", "xasuuq", "kufsi", "kufsaday", "qarax", "qaraxay", "is-miidaamin", 
    "toogtay", "la toogtay", "xasuuqay", "la dilay", "gantaal", "madaafiic", "afduub", 
    "la afduubay", "qaraxa", "qaraxyo", "miino"
]
CRIME_KEYWORDS_MED = [
    "dhaawac", "xabsi", "la xidhay", "boob", "tuug", "tuugnimo", "colaad", "dagaal", 
    "weerar", "la weeraray", "booliska", "askari", "ciidanka", "hubka", "qori", 
    "maxkamad", "xukun", "dacwad", "dembi"
]
NEGATIVE_KEYWORDS = [
    "ciyaaraha", "kubadda", "football", "goal", "guul", "shirka", "mashaariic", 
    "horumar", "shirkad", "ganacsiga", "dhaqaalaha", "maalgashi", "isboortiga", 
    "hambalyo", "ducada", "tacsi", "geeriyooday", "geerida"
]

def is_not_crime(text):
    t = str(text or "").lower()
    score = 0
    for kw in CRIME_KEYWORDS_HIGH:
        if re.search(rf"\b{kw}", t):
            score += 10
    for kw in CRIME_KEYWORDS_MED:
        if re.search(rf"\b{kw}", t):
            score += 5
    for kw in NEGATIVE_KEYWORDS:
        if re.search(rf"\b{kw}", t):
            score -= 8
    
    # If the score is less than 10, it's NOT crime-related
    return score < 10

class NotCrimeFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Not Crime Filter Tool (Shaandheeyaha Aan Dembi Ahayn)")
        self.root.geometry("600x350")
        self.root.configure(padx=20, pady=20)
        
        self.input_file = None
        
        # Title
        tk.Label(root, text="Raadi Xogta 'Not Crime-Related' Oo Kaliya", font=("Helvetica", 14, "bold"), fg="#2196F3").pack(pady=(0, 15))
        
        # Step 1: Select file
        self.select_btn = tk.Button(root, text="1. Dooro CSV File-ka Guud (Select File)", command=self.select_file, width=40, height=2, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))
        self.select_btn.pack(pady=5)
        
        self.file_label = tk.Label(root, text="Fayl lama dooran...", fg="gray")
        self.file_label.pack(pady=5)
        
        # Step 2: Filter and Save
        self.filter_btn = tk.Button(root, text="2. Soo Saari Not Crime-Related", command=self.start_filter, width=40, height=2, bg="#FF9800", fg="white", font=("Helvetica", 10, "bold"), state="disabled")
        self.filter_btn.pack(pady=15)
        
        # Status Label
        self.status_label = tk.Label(root, text="Fadlan dooro file-ka ku jira xogta mixed-ka ah...", fg="black")
        self.status_label.pack(side=tk.BOTTOM, pady=5)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Soo dooro CSV file-ka weyn",
            filetypes=[("CSV files", "*.csv")]
        )
        if file_path:
            self.input_file = file_path
            self.file_label.config(text=f"Waa la doortay: {os.path.basename(file_path)}", fg="blue")
            self.filter_btn.config(state="normal")

    def start_filter(self):
        if not self.input_file:
            return
            
        self.filter_btn.config(state="disabled", text="MAREEYNAYA... ⏳")
        self.status_label.config(text="Waxaa socda shaandheynta (Filtering out crimes)...", fg="blue")
        threading.Thread(target=self.run_filter, daemon=True).start()
        
    def run_filter(self):
        try:
            df = pd.read_csv(self.input_file, encoding="utf-8-sig")
            
            if 'text' not in df.columns:
                self.root.after(0, lambda: messagebox.showerror("Error", "Faylkan kuma jiro tiirka 'text'!"))
                self.root.after(0, self.reset_ui)
                return
            
            # Filter
            mask = df['text'].apply(is_not_crime)
            df_not_crime = df[mask].copy()
            df_not_crime['category'] = 'not crime-related'
            
            if df_not_crime.empty:
                self.root.after(0, lambda: messagebox.showinfo("Macluumaad", "Lama helin wax xog ah oo 'not crime-related' ah!"))
                self.root.after(0, self.reset_ui)
                return
                
            # Create output path
            base_dir = os.path.dirname(self.input_file)
            base_name, ext = os.path.splitext(os.path.basename(self.input_file))
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_file = os.path.join(base_dir, f"{base_name}_ONLY_NON_CRIME_{ts}{ext}")
            
            # Save
            df_not_crime.to_csv(out_file, index=False, encoding="utf-8-sig")
            
            total_records = len(df)
            not_crime_num = len(df_not_crime)
            
            msg = (f"Waa la dhammeeyay!\n\n"
                   f"Dhammaan xogta file-ka: {total_records} \n"
                   f"Xogta Not Crime ee la helay: {not_crime_num}\n\n"
                   f"File-ka cusub waxaa laga heli karaa:\n{os.path.basename(out_file)}")
            
            self.root.after(0, lambda: self.status_label.config(text=f"Waa dhammaatay! {not_crime_num} Not Crime ayaa la helay.", fg="green"))
            self.root.after(0, lambda: messagebox.showinfo("Guul (Success)", msg))
            self.root.after(0, self.reset_ui)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Cillad", f"Cillad ayaa dhacday:\n{e}"))
            self.root.after(0, lambda: self.status_label.config(text="Cilad ayaa dhacday.", fg="red"))
            self.root.after(0, self.reset_ui)
            
    def reset_ui(self):
        self.filter_btn.config(state="normal", text="2. Soo Saari Not Crime-Related")

if __name__ == "__main__":
    root = tk.Tk()
    app = NotCrimeFilterApp(root)
    root.mainloop()
