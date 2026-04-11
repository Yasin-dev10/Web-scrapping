import os
import sys
import time
import json
import re
import threading
from datetime import datetime
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
    DEPS_OK = True
except ImportError as e:
    DEPS_OK = False
    DEPS_ERROR = str(e)


# ─ Nadiifi Qoraalka ─────────────────────────────────────────────────────────────
def is_junk_text(text):
    text = text.strip()
    if len(text) < 10:
        return True
    
    lower_text = text.lower()
    junk_patterns = [
        r"^like\b", r"\d+\s*likes?\b", 
        r"^comment\b", r"\d+\s*comments?\b",
        r"^share\b", r"\d+\s*shares?\b",
        r"^see more$", r"^see translation$",
        r"^write a comment\.\.\.$",
        r"^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$",
        r"^\d+\s*(h|m|d)\b"
    ]
    
    for pattern in junk_patterns:
        if re.match(pattern, lower_text):
            return True
            
    words = text.split()
    if all(w.startswith('http') or w.startswith('#') or w.startswith('@') for w in words):
        return True
        
    return False

def clean_post_text(text):
    text = re.sub(r'See more\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'See translation\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

# ─ Hubinta Cabashada Isgaarsiinta (Telecom Complaints) ─────────────────────────
NETWORK_KEYWORDS = ["shabakad", "khadka", "go'ay", "go'an", "daciif", "maqan", "internetka", "data", "adeega"]
BILLING_KEYWORDS = ["lacag", "iiga goosatay", "jaray", "haraaga", "qaali", "balance", "evc", "edahab"]
SERVICE_KEYWORDS = ["adeeg", "xun", "macaamiil", "dhib", "la'aan", "cabasho"]

def classify_telecom_complaint(text):
    t = (text or "").lower()
    
    score = 0
    is_complaint = False
    comp_type = "none"
    
    # Check Network
    for kw in NETWORK_KEYWORDS:
        if kw in t:
            score += 5
            comp_type = "Network Issue"
            break
            
    # Check Billing
    for kw in BILLING_KEYWORDS:
        if kw in t:
            score += 5
            comp_type = "Billing Issue"
            break
            
    # Check Service/General
    for kw in SERVICE_KEYWORDS:
        if kw in t:
            score += 3
            if comp_type == "none":
                comp_type = "Customer Service"
            break
            
    if score >= 3:
        return True, comp_type
    else:
        return False, "none"

# ─ GUI Colors ────────────────────────────────────────────────────────────────
BG       = "#0f1117"
SURFACE  = "#1a1d27"
CARD     = "#22263a"
ACCENT   = "#eb6e34"  # Orange theme for Telecom
ACCENT2  = "#d95f27"
GREEN    = "#22c55e"
RED      = "#ef4444"
TEXT     = "#e2e8f0"
MUTED    = "#64748b"
BORDER   = "#2d3148"
FONT_FAMILY = "Segoe UI"


class TelecomScraperGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Telecom Complaints Scraper (Cabashooyinka Isgaarsiinta)")
        self.geometry("900x750")
        self.minsize(800, 650)
        self.configure(bg=BG)

        self._scraping = False
        self._stop_flag = False
        self._complaints = []
        self._non_complaints = []
        self._driver = None
        
        self._build_ui()
        if not DEPS_OK:
            self._log_msg(f"Missing dependency: {DEPS_ERROR}", "err")

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=SURFACE, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=ACCENT, width=4).pack(side="left", fill="y")
        tk.Label(hdr, text=" Telecom Complaints Scraper", font=(FONT_FAMILY, 15, "bold"), bg=SURFACE, fg=TEXT).pack(side="left", padx=10, pady=10)
        self._lbl_status_badge = tk.Label(hdr, text="● IDLE", font=(FONT_FAMILY, 9, "bold"), bg=SURFACE, fg=MUTED)
        self._lbl_status_badge.pack(side="right", padx=20)
        
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=15, pady=15)
        
        left_panel = tk.Frame(main, bg=BG, width=320)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        right_panel = tk.Frame(main, bg=BG)
        right_panel.pack(side="left", fill="both", expand=True)
        
        self._build_settings(left_panel)
        self._build_stats(left_panel)
        self._build_log(right_panel)

    def _build_settings(self, parent):
        card = self._card(parent, "⚙ Settings")
        
        self._lbl(card, "Facebook Page / Profile URL")
        self._url_var = tk.StringVar(value="https://www.facebook.com/SomaliTelecomIssues")
        ent_url = tk.Entry(card, textvariable=self._url_var, bg=SURFACE, fg=TEXT, insertbackground=TEXT, relief="flat", font=(FONT_FAMILY, 10), highlightthickness=1, highlightbackground=BORDER)
        ent_url.pack(fill="x", ipady=5, pady=(2, 10))
        
        self._lbl(card, "Total Posts (Tusaale 200 = 100 Comp + 100 Non-comp)")
        self._target_var = tk.IntVar(value=100)
        spin = tk.Spinbox(card, from_=2, to=10000, textvariable=self._target_var, bg=SURFACE, fg=TEXT, insertbackground=TEXT, buttonbackground=SURFACE, relief="flat", font=(FONT_FAMILY, 10))
        spin.pack(fill="x", ipady=5, pady=(2, 10))
        
        self._lbl(card, "Cookies JSON Path")
        # Default cookies path based on your requirement
        self._cookies_var = tk.StringVar(value="c:/Users/ymaxa/Downloads/complaint_scrapp/fb_cookies.json")
        cookie_frame = tk.Frame(card, bg=CARD)
        cookie_frame.pack(fill="x", pady=(2, 10))
        tk.Entry(cookie_frame, textvariable=self._cookies_var, bg=SURFACE, fg=TEXT, insertbackground=TEXT, relief="flat", font=(FONT_FAMILY, 9), highlightthickness=1, highlightbackground=BORDER).pack(side="left", fill="x", expand=True, ipady=4)
        tk.Button(cookie_frame, text="...", command=self._browse_cookies, bg=SURFACE, fg=TEXT, relief="flat").pack(side="left", padx=(4,0))
        
        btn_frame = tk.Frame(card, bg=CARD)
        btn_frame.pack(fill="x", pady=(10, 0))
        self._btn_start = tk.Button(btn_frame, text="▶ Start Scraping", bg=ACCENT, fg="white", font=(FONT_FAMILY, 9, "bold"), relief="flat", command=self._start)
        self._btn_start.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 2))
        self._btn_stop = tk.Button(btn_frame, text="■ Stop", bg=RED, fg="white", font=(FONT_FAMILY, 9, "bold"), relief="flat", command=self._stop, state="disabled")
        self._btn_stop.pack(side="left", fill="x", expand=True, ipady=4, padx=(2, 0))

    def _build_stats(self, parent):
        card = self._card(parent, "📊 Stats")
        
        stat_frame = tk.Frame(card, bg=CARD)
        stat_frame.pack(fill="x", pady=5)
        
        f1 = tk.Frame(stat_frame, bg=CARD)
        f1.pack(side="left", expand=True)
        self._stat_comp = tk.Label(f1, text="0", font=(FONT_FAMILY, 18, "bold"), bg=CARD, fg=ACCENT)
        self._stat_comp.pack()
        tk.Label(f1, text="Complaints", bg=CARD, fg=MUTED, font=(FONT_FAMILY, 8)).pack()
        
        f2 = tk.Frame(stat_frame, bg=CARD)
        f2.pack(side="right", expand=True)
        self._stat_nocomp = tk.Label(f2, text="0", font=(FONT_FAMILY, 18, "bold"), bg=CARD, fg=GREEN)
        self._stat_nocomp.pack()
        tk.Label(f2, text="Non-complaints", bg=CARD, fg=MUTED, font=(FONT_FAMILY, 8)).pack()

    def _build_log(self, parent):
        card = self._card(parent, "📋 Live Log", expand=True)
        self._log = tk.Text(card, bg=SURFACE, fg=TEXT, font=("Consolas", 9), relief="flat", state="disabled", wrap="word", highlightthickness=0)
        self._log.pack(fill="both", expand=True)
        
        self._log.tag_configure("info", foreground="#60a5fa")
        self._log.tag_configure("comp", foreground=ACCENT)
        self._log.tag_configure("nocomp", foreground=GREEN)
        self._log.tag_configure("err", foreground=RED)
        self._log.tag_configure("muted", foreground=MUTED)
        self._log.tag_configure("ok", foreground="#34d399")
        
        sb = ttk.Scrollbar(self._log, command=self._log.yview)
        sb.pack(side="right", fill="y")
        self._log.configure(yscrollcommand=sb.set)

    def _card(self, parent, title, expand=False):
        outer = tk.Frame(parent, bg=BORDER, pady=1)
        outer.pack(fill="x" if not expand else "both", expand=expand, pady=(0, 10))
        inner = tk.Frame(outer, bg=CARD, padx=12, pady=10)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=title, font=(FONT_FAMILY, 10, "bold"), bg=CARD, fg=TEXT).pack(anchor="w", pady=(0, 10))
        return inner

    def _lbl(self, parent, text):
        tk.Label(parent, text=text, bg=CARD, fg=MUTED, font=(FONT_FAMILY, 9)).pack(anchor="w")

    def _browse_cookies(self):
        p = filedialog.askopenfilename(title="Select Cookies JSON", filetypes=[("JSON files", "*.json")])
        if p: self._cookies_var.set(p)

    def _log_msg(self, msg, tag=""):
        def _ins():
            self._log.configure(state="normal")
            ts = datetime.now().strftime("%H:%M:%S")
            self._log.insert("end", f"[{ts}] ", "muted")
            self._log.insert("end", msg + "\n", tag)
            self._log.see("end")
            self._log.configure(state="disabled")
        self.after(0, _ins)

    def _update_stats(self):
        c_count = len(self._complaints)
        n_count = len(self._non_complaints)
        self.after(0, lambda: self._stat_comp.configure(text=str(c_count)))
        self.after(0, lambda: self._stat_nocomp.configure(text=str(n_count)))

    def _set_running(self, running):
        self._scraping = running
        self._btn_start.configure(state="disabled" if running else "normal")
        self._btn_stop.configure(state="normal" if running else "disabled")
        self._lbl_status_badge.configure(text="● RUNNING" if running else "● IDLE", fg=GREEN if running else MUTED)

    def _start(self):
        if not DEPS_OK: return
        self._complaints = []
        self._non_complaints = []
        self._stop_flag = False
        self._update_stats()
        self._set_running(True)
        t = threading.Thread(target=self._scrape_thread, daemon=True)
        t.start()

    def _stop(self):
        self._stop_flag = True
        self._log_msg("Stopping requested...", "err")

    def _scrape_thread(self):
        total_target = self._target_var.get()
        target_each = max(1, total_target // 2)
        url = self._url_var.get().strip()
        cookie_path = self._cookies_var.get().strip()
        
        self._log_msg(f"Wadarta guud: {total_target} -> {target_each} Complaint + {target_each} Non-complaint", "info")
        
        driver = None
        try:
            opts = Options()
            opts.add_argument("--disable-gpu")
            opts.add_argument("--disable-notifications")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            opts.add_experimental_option("useAutomationExtension", False)
            
            svc = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=svc, options=opts)
            driver.set_window_size(1280, 900)
            self._driver = driver
            
            # Login
            has_cookies = False
            if os.path.exists(cookie_path):
                self._log_msg("🍪 Gelinayaa cookies-ka...", "info")
                driver.get("https://www.facebook.com/")
                time.sleep(2)
                try:
                    with open(cookie_path, "r", encoding="utf-8") as f:
                        cookies = json.load(f)
                    for c in cookies:
                        driver.add_cookie({"name": c.get("name",""), "value": c.get("value",""), "domain": ".facebook.com", "path": "/"})
                    has_cookies = True
                except Exception as e:
                    self._log_msg(f"Cilad cookies: {e}", "err")
            else:
                self._log_msg("⚠️ Faylka cookies-ka lama helin. Gacanta ku gal.", "err")

            self._log_msg(f"🚀 Tagayaa URL: {url}", "info")
            driver.get(url)
            time.sleep(5)
            self._log_msg("Bilaabayaa scraping...", "info")
            
            seen_texts = set()
            no_new_posts = 0
            
            while not self._stop_flag:
                # Fur dhammaan 'See more'
                try:
                    btns = driver.find_elements(By.XPATH, "//div[@role='button' and (contains(., 'See more') or contains(., 'See More'))]")
                    for b in btns:
                        try: driver.execute_script("arguments[0].click();", b)
                        except: pass
                    time.sleep(0.5)
                except: pass
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                fb_posts = soup.find_all("div", attrs={"data-ad-preview": "message"})
                if not fb_posts:
                    fb_posts = soup.find_all("div", dir="auto")
                    
                new_found = 0
                for post in fb_posts:
                    if self._stop_flag: break
                    raw_text = post.get_text(" ", strip=True)
                    cleaned = clean_post_text(raw_text)
                    
                    if is_junk_text(cleaned): continue
                    
                    sig = cleaned[:100].lower()
                    if sig in seen_texts: continue
                    
                    is_comp, comp_type = classify_telecom_complaint(cleaned)
                    
                    if is_comp:
                        if len(self._complaints) < target_each:
                            seen_texts.add(sig)
                            self._complaints.append({
                                "text": cleaned,
                                "is_complaint": "Complaint",
                                "complaint_type": comp_type,
                                "url": driver.current_url
                            })
                            new_found += 1
                            self._log_msg(f"🔴 Complaint: {cleaned[:40]}... [{comp_type}]", "comp")
                    else:
                        if len(self._non_complaints) < target_each:
                            seen_texts.add(sig)
                            self._non_complaints.append({
                                "text": cleaned,
                                "is_complaint": "Non-complaint",
                                "complaint_type": "none",
                                "url": driver.current_url
                            })
                            new_found += 1
                            self._log_msg(f"🟢 Non-Comp: {cleaned[:40]}...", "nocomp")
                            
                    self._update_stats()
                    
                    if len(self._complaints) >= target_each and len(self._non_complaints) >= target_each:
                        self._log_msg("Dhamaystiray tiradii la rabay!", "ok")
                        self._stop_flag = True
                        break
                
                if self._stop_flag: break
                
                if new_found == 0:
                    no_new_posts += 1
                    if no_new_posts > 10:
                        self._log_msg("Waa la waayay posts cusub.", "err")
                        break
                else:
                    no_new_posts = 0
                    
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(3)

            self._save_csv()

        except Exception as ex:
            self._log_msg(f"CILAD: {ex}", "err")
        finally:
            if driver:
                try: driver.quit()
                except: pass
            self._driver = None
            self.after(0, lambda: self._set_running(False))
            self._log_msg("Done!", "info")

    def _save_csv(self):
        all_data = self._complaints + self._non_complaints
        if not all_data: return
        try:
            df = pd.DataFrame(all_data)
            df = df[["text", "is_complaint", "complaint_type", "url"]] # Make sure columns match somali_complaints.csv
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"telecom_complaints_GUI_{ts}.csv")
            df.to_csv(fname, index=False, encoding="utf-8-sig")
            self._log_msg(f"🎉 Saved to: {fname}", "ok")
        except Exception as e:
            self._log_msg(f"Failure to save CSV: {e}", "err")

if __name__ == "__main__":
    app = TelecomScraperGUI()
    app.mainloop()
