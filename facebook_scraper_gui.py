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
import shared_db

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
    if len(text) < 15:
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

# ─ Hubinta dambiyada (Crime Filtering) ──────────────────────────────────────────
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
    t = (text or "").lower()
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
    
    if score >= 10:
        return "crime-related"
    return "not crime-related"

# ─ GUI Colors ────────────────────────────────────────────────────────────────
BG       = "#0f1117"
SURFACE  = "#1a1d27"
CARD     = "#22263a"
ACCENT   = "#3b82f6"  # Blue theme for Facebook
ACCENT2  = "#2563eb"
GREEN    = "#22c55e"
RED      = "#ef4444"
TEXT     = "#e2e8f0"
MUTED    = "#64748b"
BORDER   = "#2d3148"
FONT_FAMILY = "Segoe UI"


class FacebookScraperGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FB Crime Scraper (Qoraalada Dembiyada)")
        self.geometry("900x700")
        self.minsize(800, 600)
        self.configure(bg=BG)

        self._scraping = False
        self._stop_flag = False
        self._items = []
        self._driver = None
        
        self._build_ui()
        if not DEPS_OK:
            self._log_msg(f"Missing dependency: {DEPS_ERROR}", "err")
            self._log_msg("Fadlan run: pip install selenium webdriver-manager beautifulsoup4 pandas", "err")

    def _build_ui(self):
        # --- Header ---
        hdr = tk.Frame(self, bg=SURFACE, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        
        tk.Frame(hdr, bg=ACCENT, width=4).pack(side="left", fill="y")
        tk.Label(hdr, text=" Facebook Crime Scraper", font=(FONT_FAMILY, 15, "bold"), bg=SURFACE, fg=TEXT).pack(side="left", padx=10, pady=10)
        
        self._lbl_status_badge = tk.Label(hdr, text="● IDLE", font=(FONT_FAMILY, 9, "bold"), bg=SURFACE, fg=MUTED)
        self._lbl_status_badge.pack(side="right", padx=20)
        
        # --- Main Layout ---
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
        self._url_var = tk.StringVar(value="https://www.facebook.com/MunasarMohamedAbd")
        ent_url = tk.Entry(card, textvariable=self._url_var, bg=SURFACE, fg=TEXT, insertbackground=TEXT, relief="flat", font=(FONT_FAMILY, 10), highlightthickness=1, highlightbackground=BORDER)
        ent_url.pack(fill="x", ipady=5, pady=(2, 10))
        
        self._lbl(card, "Posts Count (Tirada la rabo)")
        self._target_var = tk.IntVar(value=50)
        spin = tk.Spinbox(card, from_=1, to=10000, textvariable=self._target_var, bg=SURFACE, fg=TEXT, insertbackground=TEXT, buttonbackground=SURFACE, relief="flat", font=(FONT_FAMILY, 10))
        spin.pack(fill="x", ipady=5, pady=(2, 10))
        
        self._lbl(card, "Cookies JSON Path (Login-ka)")
        self._cookies_var = tk.StringVar(value="fb_cookies.json")
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
        self._stat_total = tk.Label(card, text="0", font=(FONT_FAMILY, 24, "bold"), bg=CARD, fg=ACCENT)
        self._stat_total.pack(pady=5)
        tk.Label(card, text="Total Crime Posts", bg=CARD, fg=MUTED, font=(FONT_FAMILY, 9)).pack()

    def _build_log(self, parent):
        card = self._card(parent, "📋 Live Log", expand=True)
        self._log = tk.Text(card, bg=SURFACE, fg=TEXT, font=("Consolas", 9), relief="flat", state="disabled", wrap="word", highlightthickness=0)
        self._log.pack(fill="both", expand=True)
        
        self._log.tag_configure("info", foreground=ACCENT)
        self._log.tag_configure("ok", foreground=GREEN)
        self._log.tag_configure("err", foreground=RED)
        self._log.tag_configure("muted", foreground=MUTED)
        
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
        count = len(self._items)
        self.after(0, lambda: self._stat_total.configure(text=str(count)))

    def _set_running(self, running):
        self._scraping = running
        self._btn_start.configure(state="disabled" if running else "normal")
        self._btn_stop.configure(state="normal" if running else "disabled")
        self._lbl_status_badge.configure(text="● RUNNING" if running else "● IDLE", fg=GREEN if running else MUTED)

    def _start(self):
        if not DEPS_OK: return
        self._items = []
        self._stop_flag = False
        self._update_stats()
        self._set_running(True)
        t = threading.Thread(target=self._scrape_thread, daemon=True)
        t.start()

    def _stop(self):
        self._stop_flag = True
        self._log_msg("Stopping requested...", "err")

    def _scrape_thread(self):
        target_count = self._target_var.get()
        url = self._url_var.get().strip()
        cookie_path = self._cookies_var.get().strip()
        
        self._log_msg("🌐 Furayaa browser-ka...", "info")
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
            
            # Cookies
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
                self._log_msg("⚠️ Faylka cookies-ka lama helin. Log-in u baahan garee.", "err")

            self._log_msg(f"🚀 Tagayaa URL: {url}", "info")
            driver.get(url)
            
            if not has_cookies:
                self._log_msg("Fadlan Browserka ka login garee kadibna faraha ka qaad.", "err")
            
            time.sleep(5)
            self._log_msg("Bilaabayaa scraping...", "info")
            
            seen_texts = set()
            no_new_posts = 0
            
            while len(self._items) < target_count and not self._stop_flag:
                # Fur dhammaan 'See more' (Sii aqri) si qoraalka oo dhan u soo baxo inta aan la baarin
                try:
                    btns = driver.find_elements(By.XPATH, "//div[@role='button' and (contains(., 'See more') or contains(., 'See More'))]")
                    for b in btns:
                        try:
                            driver.execute_script("arguments[0].click();", b)
                        except:
                            pass
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
                    
                    # Hubi inay crime tahay
                    cat = classify(cleaned)
                    if cat != "crime-related": continue
                    
                    sig = cleaned[:100].lower()
                    if sig in seen_texts: continue
                    seen_texts.add(sig)
                    
                    self._items.append({
                        "url": driver.current_url,
                        "text": cleaned,
                        "category": cat
                    })
                    new_found += 1
                    self._log_msg(f"✅ [{len(self._items)}/{target_count}] {cleaned[:60]}...", "ok")
                    self._update_stats()
                    
                    if len(self._items) >= target_count: break
                
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
        if not self._items: return
        try:
            df = pd.DataFrame(self._items, columns=["url", "text", "category"])
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"fb_crime_GUI_{ts}.csv")
            df.to_csv(fname, index=False, encoding="utf-8-sig")
            self._log_msg(f"🎉 Saved to: {fname}", "ok")
        except Exception as e:
            self._log_msg(f"Failure to save CSV: {e}", "err")

        # ── Keydi Database-ka ──────────────────────────────────────────
        try:
            shared_db.insert_many(self._items, source="Facebook-Scraper")
            self._log_msg(f"🗄️  Database: {len(self._items)} xog ayaa lagu keydiiyey", "ok")
        except Exception as e:
            self._log_msg(f"⚠️  Database error: {e}", "err")

if __name__ == "__main__":
    app = FacebookScraperGUI()
    app.mainloop()
