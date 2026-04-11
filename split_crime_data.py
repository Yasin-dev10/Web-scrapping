import os
import re
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import threading

# ── Crime keywords (Af-Soomaali) ────────────────────────────────────────────────
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

def classify(text):
    t = str(text or "").lower()
    score = 0
    # 1. Hubi ereyada miisaanka culus (High Weight)
    for kw in CRIME_KEYWORDS_HIGH:
        if re.search(rf"\b{kw}", t):
            score += 10
    # 2. Hubi ereyada miisaanka dhexe (Medium Weight)
    for kw in CRIME_KEYWORDS_MED:
        if re.search(rf"\b{kw}", t):
            score += 5
    # 3. Ka sifee ereyada aan khuseyn (Negative Weight)
    for kw in NEGATIVE_KEYWORDS:
        if re.search(rf"\b{kw}", t):
            score -= 8
    
    if score >= 10:
        return "crime-related"
    return "not crime-related"

BG       = "#0f1117"
SURFACE  = "#1a1d27"
CARD     = "#22263a"
ACCENT   = "#3b82f6" # Buluug 
GREEN    = "#22c55e"
TEXT     = "#e2e8f0"
MUTED    = "#64748b"
BORDER   = "#2d3148"
FONT_FAMILY = "Segoe UI"

class SplitDataApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kala-saaraha Xogta (Crime vs Not Crime) - GUI")
        self.geometry("650x450")
        self.configure(bg=BG)
        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=SURFACE, height=60)
        hdr.pack(fill="x")
        tk.Label(hdr, text=" ⚖️ Crime Data Splitter Tool", font=(FONT_FAMILY, 14, "bold"),
                 bg=SURFACE, fg=ACCENT).pack(side="left", pady=15, padx=20)

        # Main Body
        body = tk.Frame(self, bg=BG, padx=30, pady=20)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="1. Dooro faylka CSV-ga ah ee ururintaada si loo kala saaro:",
                 bg=BG, fg=TEXT, font=(FONT_FAMILY, 11)).pack(anchor="w", pady=(0, 5))

        # Input File Selection
        self._input_path = tk.StringVar()
        row1 = tk.Frame(body, bg=BG)
        row1.pack(fill="x", pady=(0, 20))
        tk.Entry(row1, textvariable=self._input_path, bg=SURFACE, fg=TEXT,
                 relief="flat", font=(FONT_FAMILY, 10), highlightthickness=1,
                 highlightbackground=BORDER).pack(side="left", fill="x", expand=True, ipady=8)
        tk.Button(row1, text="Browse...", bg=CARD, fg=TEXT, relief="flat", font=(FONT_FAMILY, 10),
                  command=self._browse_input).pack(side="left", padx=(10, 0), ipady=5)

        # Instructions
        instr = tk.Frame(body, bg=CARD, padx=15, pady=15)
        instr.pack(fill="x", pady=(0, 20))
        tk.Label(instr, text="Sidee buu u shaqeeyaa?",
                 bg=CARD, fg=ACCENT, font=(FONT_FAMILY, 10, "bold")).pack(anchor="w", pady=(0, 5))
        tk.Label(instr, text="• Nidaamku wuxuu si sax ah u baari doonaa qoraal kasta.",
                 bg=CARD, fg=TEXT, font=(FONT_FAMILY, 10)).pack(anchor="w")
        tk.Label(instr, text="• Waxa uu soo saari doonaa 2 fayl oo si gooni ah uxareysan:",
                 bg=CARD, fg=TEXT, font=(FONT_FAMILY, 10)).pack(anchor="w")
        tk.Label(instr, text="    1. Fayl ay ku jiraan xogaha Crime-ka (Dembiyada) oo kaliya.",
                 bg=CARD, fg=GREEN, font=(FONT_FAMILY, 10)).pack(anchor="w")
        tk.Label(instr, text="    2. Fayl ay ku jiraan xogaha Non-Crime (Aan Dembi ahayn).",
                 bg=CARD, fg="#ef4444", font=(FONT_FAMILY, 10)).pack(anchor="w")

        # Action Button
        self._btn_run = tk.Button(body, text="🚀 KALA SAAR XOGTA", bg=ACCENT, fg="white",
                                  font=(FONT_FAMILY, 12, "bold"), relief="flat",
                                  command=self._start_split, state="disabled")
        self._btn_run.pack(fill="x", ipady=12, pady=(10, 10))

        # Status
        self._lbl_status = tk.Label(body, text="Fadlan dooro faylka (Browse)...", bg=BG, fg=MUTED, font=(FONT_FAMILY, 10, "bold"))
        self._lbl_status.pack(pady=5)

    def _browse_input(self):
        p = filedialog.askopenfilename(title="Select CSV file", filetypes=[("CSV files", "*.csv")])
        if p:
            self._input_path.set(p)
            self._btn_run.configure(state="normal", bg=ACCENT)
            self._lbl_status.configure(text=f"Diyaar: {os.path.basename(p)}")

    def _start_split(self):
        # Run process in a thread so UI doesn't freeze
        self._btn_run.configure(state="disabled", text="MAREEYNAYA... ⏳", bg=CARD)
        self._lbl_status.configure(text="Waxaa socda kala-shaandheynta (Classifying)...", fg="#eab308")
        threading.Thread(target=self._run_split, daemon=True).start()

    def _run_split(self):
        input_p = self._input_path.get()
        if not os.path.exists(input_p):
            self.after(0, lambda: messagebox.showerror("Error", "Faylka lama helin!"))
            self.after(0, self._reset_btn)
            return

        try:
            df = pd.read_csv(input_p, encoding="utf-8-sig")
            
            if 'text' not in df.columns:
                self.after(0, lambda: messagebox.showerror("Error", "Faylkan kuma jiro tiirka 'text' (Qoraalka)!"))
                self.after(0, self._reset_btn)
                return
            
            # Re-classify accurately
            df['calculated_category'] = df['text'].apply(classify)

            # Split logic
            df_crime = df[df['calculated_category'] == 'crime-related'].copy()
            df_not_crime = df[df['calculated_category'] == 'not crime-related'].copy()

            df_crime['category'] = 'crime-related'
            df_not_crime['category'] = 'not crime-related'
            
            df_crime.drop(columns=['calculated_category'], inplace=True)
            df_not_crime.drop(columns=['calculated_category'], inplace=True)

            # Create output paths
            base_dir = os.path.dirname(input_p)
            base_name, ext = os.path.splitext(os.path.basename(input_p))
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            out_crime = os.path.join(base_dir, f"{base_name}_CRIME_{ts}{ext}")
            out_not_crime = os.path.join(base_dir, f"{base_name}_NOT_CRIME_{ts}{ext}")

            # Save
            if not df_crime.empty:
                df_crime.to_csv(out_crime, index=False, encoding="utf-8-sig")
            if not df_not_crime.empty:
                df_not_crime.to_csv(out_not_crime, index=False, encoding="utf-8-sig")

            total_records = len(df)
            crime_num = len(df_crime)
            not_crime_num = len(df_not_crime)

            msg = (f"Shaqada waa la dhammeeyay si guul ah!\n\n"
                   f"Dhammaan xogta: {total_records} \n\n"
                   f"🚨 Crime-related: {crime_num} ayaa la helay\n"
                   f"✅ Not Crime: {not_crime_num} ayaa la helay\n\n"
                   f"Faylasah ayaa lagu sameeyay gudaha:\n{base_dir}")

            self.after(0, lambda: self._lbl_status.configure(text=f"Waa dhammaatay! {crime_num} Crime, {not_crime_num} Not Crime", fg=GREEN))
            self.after(0, lambda: messagebox.showinfo("Guul", msg))
            self.after(0, self._reset_btn)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Cillad", f"Cillad ayaa dhacday: {e}"))
            self.after(0, self._reset_btn)

    def _reset_btn(self):
        self._btn_run.configure(state="normal", text="🚀 KALA SAAR XOGTA", bg=ACCENT)

if __name__ == "__main__":
    app = SplitDataApp()
    app.mainloop()
