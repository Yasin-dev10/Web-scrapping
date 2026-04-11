# -*- coding: utf-8 -*-
"""
CrimeFilterTool.py  —  Nadiifinta iyo Kala-shaandheynta Xogta
============================================================
Barnaamijkan wuxuu ka dhex saaraa CSV-gaaga oo keliya xogta
la xiriirta dembiyada (crime-related), isagoo tirtiraya inta kale.
"""
import os, sys, json, time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from datetime import datetime
import re
import shared_db

# ── fix Windows console encoding ──────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
# Ereyadaan hadday ku jiraan, waxay yareynayaan suurtogalnimada in qoraalku yahay dembi (False Positives)
NEGATIVE_KEYWORDS = [
    "ciyaaraha", "kubadda", "football", "goal", "guul", "shirka", "mashaariic", 
    "horumar", "shirkad", "ganacsiga", "dhaqaalaha", "maalgashi", "isboortiga", 
    "hambalyo", "ducada", "tacsi", "geeriyooday", "geerida"
]

def classify(text):
    t = (text or "").lower()
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
ACCENT   = "#ef4444" 
GREEN    = "#22c55e"
TEXT     = "#e2e8f0"
MUTED    = "#64748b"
BORDER   = "#2d3148"
FONT_FAMILY = "Segoe UI"

class CrimeFilterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Crime Data Filter Tool - v2.0")
        self.geometry("900x700") # Larger window for the table
        self.configure(bg=BG)
        self._df_filtered = None
        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=SURFACE, height=60)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  🧹 Crime Filter Tool", font=(FONT_FAMILY, 14, "bold"),
                 bg=SURFACE, fg=ACCENT).pack(side="left", pady=15)

        # Main Body
        body = tk.Frame(self, bg=BG, padx=20, pady=20)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Dooro faylka CSV-ga ah ee aad rabto inaad nadiifiso:",
                 bg=BG, fg=TEXT, font=(FONT_FAMILY, 10)).pack(anchor="w", pady=(0, 5))

        # Input File Selection
        self._input_path = tk.StringVar()
        row1 = tk.Frame(body, bg=BG)
        row1.pack(fill="x", pady=(0, 20))
        tk.Entry(row1, textvariable=self._input_path, bg=SURFACE, fg=TEXT,
                 relief="flat", font=(FONT_FAMILY, 9), highlightthickness=1,
                 highlightbackground=BORDER).pack(side="left", fill="x", expand=True, ipady=6)
        tk.Button(row1, text="Browse...", bg=CARD, fg=TEXT, relief="flat",
                  command=self._browse_input).pack(side="left", padx=(10, 0))

        # Instructions
        instr = tk.Frame(body, bg=CARD, padx=15, pady=15)
        instr.pack(fill="x", pady=(0, 20))
        tk.Label(instr, text="Barnaamijku wuxuu si toos ah u soo saari doonaa xogta:",
                 bg=CARD, fg=MUTED, font=(FONT_FAMILY, 9, "italic")).pack(anchor="w")
        tk.Label(instr, text="• Kaliya xogta 'category' keedu yahay 'crime-related'.",
                 bg=CARD, fg=TEXT, font=(FONT_FAMILY, 9)).pack(anchor="w")
        tk.Label(instr, text="• Natiijada waxaa lagu keydin doonaa fayl cusub.",
                 bg=CARD, fg=TEXT, font=(FONT_FAMILY, 9)).pack(anchor="w")

        # Action Button
        self._btn_run = tk.Button(body, text="🚀 BILOOW NADIIFINTA (RE-SCAN)", bg=ACCENT, fg="white",
                                  font=(FONT_FAMILY, 11, "bold"), relief="flat",
                                  command=self._run_filter, state="disabled")
        self._btn_run.pack(fill="x", ipady=10, pady=(0, 10))

        # Table Preview
        tk.Label(body, text="Muraayadda Xogta Nadiifka ah (Preview):",
                 bg=BG, fg=MUTED, font=(FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
        
        table_frame = tk.Frame(body, bg=BORDER, pady=1)
        table_frame.pack(fill="both", expand=True)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=SURFACE, foreground=TEXT, fieldbackground=SURFACE, borderwidth=0, font=(FONT_FAMILY, 9))
        style.map("Treeview", background=[('selected', ACCENT)])
        style.configure("Treeview.Heading", background=CARD, foreground=TEXT, borderwidth=0, font=(FONT_FAMILY, 9, "bold"))

        self._tree = ttk.Treeview(table_frame, columns=("category", "text", "url"), show="headings", height=10)
        self._tree.heading("category", text="Category")
        self._tree.heading("text", text="Qoraalka (Text)")
        self._tree.heading("url", text="Link-ga")
        
        self._tree.column("category", width=100, anchor="center")
        self._tree.column("text", width=500)
        self._tree.column("url", width=150)
        
        self._tree.pack(side="left", fill="both", expand=True)

        scb = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        scb.pack(side="right", fill="y")
        self._tree.configure(yscrollcommand=scb.set)

        # Status
        self._lbl_status = tk.Label(body, text="Dooro fayl si aad u bilowdo.", bg=BG, fg=MUTED, font=(FONT_FAMILY, 10, "bold"))
        self._lbl_status.pack(pady=10)

    def _browse_input(self):
        p = filedialog.askopenfilename(title="Select CSV file", filetypes=[("CSV files", "*.csv")])
        if p:
            self._input_path.set(p)
            self._btn_run.configure(state="normal")
            self._lbl_status.configure(text=f"Faylka la doortay: {os.path.basename(p)}")

    def _run_filter(self):
        input_p = self._input_path.get()
        if not os.path.exists(input_p):
            messagebox.showerror("Error", "Faylka lama helin!")
            return

        try:
            input_p = self._input_path.get()
            self._lbl_status.configure(text="Sidee looga aqrinayaa xogta... fadlan sug ⏳", fg=ACCENT)
            self.update()

            # 1. Read CSV
            df = pd.read_csv(input_p, encoding="utf-8-sig")
            
            if 'text' not in df.columns:
                messagebox.showerror("Error", "Faylkan kuma jiro tiirka 'text' (Qoraalka)!")
                return
            
            total_before = len(df)
            
            # 2. Re-classify
            df['category'] = df['text'].apply(classify)
            df_filtered = df[df['category'] == 'crime-related']
            
            total_after = len(df_filtered)
            removed = total_before - total_after
            
            # 3. Update Table
            for item in self._tree.get_children():
                self._tree.delete(item)
            
            # Show first 100 in preview to keep it fast
            for _, row in df_filtered.head(100).iterrows():
                self._tree.insert("", "end", values=(row['category'], row['text'][:150], row['url']))
            
            # 4. Save to new file
            base, ext = os.path.splitext(input_p)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_p = f"{base}_CRIME_ONLY_{ts}{ext}"
            df_filtered.to_csv(output_p, index=False, encoding="utf-8-sig")
            
            # ── Keydi Database-ka
            try:
                rows = df_filtered[['url','text','category']].to_dict('records')
                shared_db.insert_many(rows, source="CrimeFilter")
                db_msg = f" | Database: {len(rows)} la keydiyey"
            except Exception as db_err:
                db_msg = f" | DB khatar: {db_err}"
            
            # 5. Result message
            self._lbl_status.configure(text=f"✅ Nadiifintu waa dhammaatay! ({total_after} rows / {total_before} total){db_msg}", fg=GREEN)
            
            msg = f"Nadiifintii waa dhammaatay!\n\n" \
                  f"Filter-ka waxaa soo maray: {total_after} posts\n" \
                  f"Waxaa la tirtiray: {removed} posts\n\n" \
                  f"Faylka waa la keydiyey!\n{db_msg}"
            messagebox.showinfo("Success", msg)
            
        except Exception as e:
            messagebox.showerror("Error", f"Khalad ayaa dhacay: {e}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Khalad ayaa dhacay: {e}")

if __name__ == "__main__":
    app = CrimeFilterApp()
    app.mainloop()
