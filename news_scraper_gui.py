# -*- coding: utf-8 -*-
"""
news_scraper_gui.py  —  Universal News & Social Media Scraper
============================================================
Run:  python -X utf8 news_scraper_gui.py
"""
import os, sys, time, re, threading, json, random
from urllib.parse import urljoin, urlparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# ── fix Windows console encoding ──────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── lazy imports ─────────────────────────────────────────────────────────────
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
    import pandas as pd
    import requests
    DEPS_OK = True
except ImportError as e:
    DEPS_OK = False
    DEPS_ERROR = str(e)

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

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def is_junk(text):
    if not text: return True
    words = text.split()
    if len(words) >= 8 and all(len(w) <= 2 for w in words[:8]): return True
    if len(words) == 1 and len(text) > 40: return True
    return False

def is_valid_article_link(base_url, link_href):
    if not link_href or link_href.startswith("javascript") or link_href.startswith("#"):
        return False
    full_url = urljoin(base_url, link_href)
    parsed_base = urlparse(base_url)
    parsed_link = urlparse(full_url)
    if parsed_base.netloc not in parsed_link.netloc and parsed_link.netloc not in parsed_base.netloc:
        return False
    ignore_paths = ["/contact", "/about", "/privacy", "/terms", "/search", "/login", "/register"]
    lower_path = parsed_link.path.lower()
    for ip in ignore_paths:
        if ip in lower_path:
            return False
    if len(lower_path.split('/')) < 3 and "bbc.com" in parsed_link.netloc:
        return False 
    return True

# ══════════════════════════════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════════════════════════════
BG       = "#0f1117"
SURFACE  = "#1a1d27"
CARD     = "#22263a"
ACCENT   = "#f74f4f"  # Red theme
ACCENT2  = "#ed3a3a"
GREEN    = "#22c55e"
RED      = "#ef4444"
YELLOW   = "#f59e0b"
TEXT     = "#e2e8f0"
MUTED    = "#64748b"
BORDER   = "#2d3148"

FONT_FAMILY = "Segoe UI"

class ScraperGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Universal News & Social Media Scraper")
        self.geometry("1050x780")
        self.minsize(900, 650)
        self.configure(bg=BG)
        self.resizable(True, True)

        self._scraping   = False
        self._stop_flag  = False
        self._items      = []
        self._driver     = None
        self._save_path  = tk.StringVar(value=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "scraped_data.csv"))

        self._build_ui()
        self._check_deps()

    def _build_ui(self):
        self._header()
        self._main_panel()
        self._statusbar()

    def _header(self):
        hdr = tk.Frame(self, bg=SURFACE, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        accent_bar = tk.Frame(hdr, bg=ACCENT, width=4)
        accent_bar.pack(side="left", fill="y")

        tk.Label(hdr, text="  🌐  ", font=(FONT_FAMILY, 20),
                 bg=SURFACE, fg=ACCENT).pack(side="left", pady=10)
        tk.Label(hdr, text="Universal News & Social Media Scraper",
                 font=(FONT_FAMILY, 15, "bold"),
                 bg=SURFACE, fg=TEXT).pack(side="left", pady=10)
        tk.Label(hdr, text="  —  Dhamaan xogaha meel ka baadh",
                 font=(FONT_FAMILY, 10), bg=SURFACE, fg=MUTED).pack(side="left")

        self._lbl_status_badge = tk.Label(
            hdr, text="● IDLE", font=(FONT_FAMILY, 9, "bold"),
            bg=SURFACE, fg=MUTED)
        self._lbl_status_badge.pack(side="right", padx=20)

    def _main_panel(self):
        pane = tk.Frame(self, bg=BG)
        pane.pack(fill="both", expand=True, padx=18, pady=14)

        left = tk.Frame(pane, bg=BG, width=340)
        left.pack(side="left", fill="y", padx=(0,12))
        left.pack_propagate(False)

        self._card_settings(left)
        self._card_cookies(left)
        self._card_output(left)
        self._card_stats(left)

        right = tk.Frame(pane, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self._card_log(right)
        self._card_progress(right)

    def _card_settings(self, parent):
        card = self._card(parent, "⚙  Scraper Settings")

        self._lbl(card, "Select Platform Type")
        self._platform_var = tk.StringVar(value="News Websites")
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=SURFACE, background=CARD, foreground=TEXT, bordercolor=BORDER, arrowcolor=TEXT)
        
        platforms = ["News Websites", "Facebook", "Twitter / X", "Instagram", "All Social Media"]
        cb = ttk.Combobox(card, textvariable=self._platform_var, values=platforms, state="readonly", font=(FONT_FAMILY, 10))
        cb.pack(fill="x", pady=(2, 8))
        cb.bind("<<ComboboxSelected>>", self._on_platform_change)

        self._lbl(card, "Target URL or Username/Topic")
        self._url_var = tk.StringVar(value="https://www.bbc.com/somali")
        url_frame = tk.Frame(card, bg=CARD)
        url_frame.pack(fill="x", pady=(2,8))
        tk.Label(url_frame, text="🔗", bg=CARD, fg=ACCENT,
                 font=(FONT_FAMILY, 11)).pack(side="left", padx=(0,4))
        self._ent_url = tk.Entry(url_frame, textvariable=self._url_var,
                                  bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                                  relief="flat", font=(FONT_FAMILY, 10),
                                  highlightthickness=1, highlightbackground=BORDER)
        self._ent_url.pack(fill="x", expand=True, ipady=6)

        self._lbl(card, "Target Number of Items")
        self._target_var = tk.IntVar(value=30)
        spin_frame = tk.Frame(card, bg=CARD)
        spin_frame.pack(fill="x", pady=(2,8))
        self._spin = tk.Spinbox(spin_frame, from_=5, to=500000,
                                  textvariable=self._target_var,
                                  bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                                  buttonbackground=SURFACE,
                                  relief="flat", font=(FONT_FAMILY, 10), width=10)
        self._spin.pack(side="left", ipady=5)

        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(fill="x", pady=(6,2))

        self._btn_start = self._btn(btn_row, "▶  Start Scraping",
                                     ACCENT, self._start_scraping, side="left")
        self._btn_stop  = self._btn(btn_row, "■  Stop",
                                     RED, self._stop_scraping,
                                     side="left", padx=(6,0), state="disabled")

    def _card_cookies(self, parent):
        self._cookies_card = self._card(parent, "🍪  Cookies (Social Media Only)")
        
        cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb_cookies.json")
        self._cookies_var = tk.StringVar(value=cookies_path)

        self._lbl(self._cookies_card, "Path to cookies.json")
        row = tk.Frame(self._cookies_card, bg=CARD)
        row.pack(fill="x", pady=(2,6))
        tk.Entry(row, textvariable=self._cookies_var,
                 bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=(FONT_FAMILY, 9), highlightthickness=1, highlightbackground=BORDER).pack(
                 side="left", fill="x", expand=True, ipady=5)
        self._btn(row, "…", SURFACE, self._browse_cookies, side="left", padx=(4,0), fg=TEXT)

        # Hide initially since default is News Websites
        self._cookies_card.pack_forget()

    def _on_platform_change(self, event=None):
        plat = self._platform_var.get()
        if plat == "News Websites":
            self._cookies_card.pack_forget()
            self._ent_url.delete(0, 'end')
            self._ent_url.insert(0, "https://www.bbc.com/somali")
        else:
            self._cookies_card.pack(fill="x", pady=(0, 10), after=self._cookies_card.master.winfo_children()[0])
            self._ent_url.delete(0, 'end')
            if plat == "Facebook": self._ent_url.insert(0, "MunasarMohamedAbd")
            elif plat == "Twitter / X": self._ent_url.insert(0, "https://twitter.com/search?q=somalia")
            else: self._ent_url.insert(0, "somali")

    def _browse_cookies(self):
        p = filedialog.askopenfilename(title="Select cookies JSON", filetypes=[("JSON files", "*.json")])
        if p: self._cookies_var.set(p)

    def _card_output(self, parent):
        card = self._card(parent, "💾  Output CSV")
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=(2,6))
        tk.Entry(row, textvariable=self._save_path,
                 bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=(FONT_FAMILY, 9), highlightthickness=1, highlightbackground=BORDER).pack(
                 side="left", fill="x", expand=True, ipady=5)
        self._btn(row, "…", SURFACE, self._browse_save, side="left", padx=(4,0), fg=TEXT)
        self._btn(card, "📂  Open CSV in Folder", "#1e293b", self._open_folder, fill="x")

    def _card_stats(self, parent):
        card = self._card(parent, "📊  Statistics")
        grid = tk.Frame(card, bg=CARD)
        grid.pack(fill="x")
        self._stat_total  = self._stat_box(grid, "Total",  "0",  TEXT,   0)
        self._stat_crime  = self._stat_box(grid, "Crime",  "0",  RED,    1)
        self._stat_ok     = self._stat_box(grid, "Clean",  "0",  GREEN,  2)

    def _stat_box(self, parent, label, val, color, col):
        f = tk.Frame(parent, bg=SURFACE, padx=8, pady=6)
        f.grid(row=0, column=col, padx=3, pady=4, sticky="ew")
        parent.columnconfigure(col, weight=1)
        num = tk.Label(f, text=val, font=(FONT_FAMILY, 18, "bold"),
                       bg=SURFACE, fg=color)
        num.pack()
        tk.Label(f, text=label, font=(FONT_FAMILY, 8),
                 bg=SURFACE, fg=MUTED).pack()
        return num

    def _card_log(self, parent):
        card = self._card(parent, "📋  Live Log", expand=True)
        self._log = tk.Text(
            card, bg=SURFACE, fg=TEXT, font=("Consolas", 9),
            relief="flat", state="disabled", wrap="word", highlightthickness=0)
        self._log.pack(fill="both", expand=True)

        self._log.tag_configure("crime",  foreground=RED)
        self._log.tag_configure("ok",     foreground=GREEN)
        self._log.tag_configure("info",   foreground=ACCENT)
        self._log.tag_configure("warn",   foreground=YELLOW)
        self._log.tag_configure("err",    foreground="#ff6b6b")
        self._log.tag_configure("muted",  foreground=MUTED)
        self._log.tag_configure("bold",   font=("Consolas", 9, "bold"))

        sb = ttk.Scrollbar(self._log, command=self._log.yview)
        sb.pack(side="right", fill="y")
        self._log.configure(yscrollcommand=sb.set)

        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(fill="x", pady=(4,0))
        self._btn(btn_row, "🗑  Clear Log", "#1e293b", self._clear_log, side="left")

    def _card_progress(self, parent):
        card = self._card(parent, "⏳  Progress")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("news.Horizontal.TProgressbar",
                        troughcolor=SURFACE, background=ACCENT,
                        bordercolor=SURFACE, lightcolor=ACCENT, darkcolor=ACCENT2)

        self._progress_var = tk.DoubleVar(value=0)
        self._progress_bar = ttk.Progressbar(
            card, variable=self._progress_var,
            style="news.Horizontal.TProgressbar",
            mode="determinate", maximum=100)
        self._progress_bar.pack(fill="x", pady=(0,4))

        self._lbl_progress = tk.Label(
            card, text="Waiting to start…",
            bg=CARD, fg=MUTED, font=(FONT_FAMILY, 9))
        self._lbl_progress.pack(anchor="w")

    def _statusbar(self):
        bar = tk.Frame(self, bg=SURFACE, height=26)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Frame(bar, bg=ACCENT, width=4).pack(side="left", fill="y")
        self._lbl_status = tk.Label(
            bar, text="  Ready", bg=SURFACE, fg=MUTED,
            font=(FONT_FAMILY, 8), anchor="w")
        self._lbl_status.pack(side="left", fill="x", expand=True)

    def _card(self, parent, title, expand=False):
        outer = tk.Frame(parent, bg=BORDER, pady=1)
        outer.pack(fill="x" if not expand else "both", expand=expand, pady=(0, 10))
        inner = tk.Frame(outer, bg=CARD, padx=14, pady=10)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=title, font=(FONT_FAMILY, 9, "bold"),
                 bg=CARD, fg=ACCENT).pack(anchor="w", pady=(0,6))
        return inner

    def _lbl(self, parent, text):
        tk.Label(parent, text=text, bg=CARD, fg=MUTED,
                 font=(FONT_FAMILY, 8)).pack(anchor="w")

    def _btn(self, parent, text, color, cmd, side=None, padx=0, fill=None, state="normal", fg="white"):
        btn = tk.Button(parent, text=text, bg=color, fg=fg, font=(FONT_FAMILY, 9, "bold"),
                        relief="flat", cursor="hand2", padx=10, pady=6, command=cmd, state=state)
        if side: btn.pack(side=side, padx=padx)
        elif fill: btn.pack(fill=fill, pady=(3,0))
        else: btn.pack(pady=(3,0))
        return btn

    def _log_msg(self, msg, tag=""):
        def _insert():
            self._log.configure(state="normal")
            ts = datetime.now().strftime("%H:%M:%S")
            self._log.insert("end", f"[{ts}] ", "muted")
            self._log.insert("end", msg + "\n", tag)
            self._log.see("end")
            self._log.configure(state="disabled")
        self.after(0, _insert)

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _check_deps(self):
        if not DEPS_OK:
            self._log_msg(f"Missing dependency: {DEPS_ERROR}", "err")

    def _browse_save(self):
        p = filedialog.asksaveasfilename(title="Save CSV as…", defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if p: self._save_path.set(p)

    def _open_folder(self):
        p = self._save_path.get()
        folder = os.path.dirname(p) if p else os.getcwd()
        os.startfile(folder)

    def _set_running(self, running: bool):
        self._scraping = running
        state_on  = "normal" if running  else "disabled"
        state_off = "disabled" if running else "normal"
        self._btn_start.configure(state=state_off)
        self._btn_stop.configure(state=state_on)
        self._ent_url.configure(state=state_off)
        badge_text  = "● RUNNING" if running else "● IDLE"
        badge_color = GREEN if running else MUTED
        self._lbl_status_badge.configure(text=badge_text, fg=badge_color)

    def _update_stats(self):
        total  = len(self._items)
        crime  = sum(1 for p in self._items if p["category"] == "crime-related")
        clean  = total - crime
        self.after(0, lambda: self._stat_total.configure(text=str(total)))
        self.after(0, lambda: self._stat_crime.configure(text=str(crime)))
        self.after(0, lambda: self._stat_ok.configure(text=str(clean)))

    def _set_progress(self, done, total, msg=""):
        pct = (done / total * 100) if total else 0
        self.after(0, lambda: self._progress_var.set(pct))
        label = msg or f"{done} / {total} items  ({pct:.0f}%)"
        self.after(0, lambda: self._lbl_progress.configure(text=label))
        self.after(0, lambda: self._lbl_status.configure(text=f"  {label}"))

    def _start_scraping(self):
        if not DEPS_OK:
            messagebox.showerror("Error", "Missing dependencies!")
            return
        url_raw = self._url_var.get().strip()
        if not url_raw:
            messagebox.showwarning("Error", "Please enter a Target!")
            return

        self._items  = []
        self._stop_flag = False
        self._set_running(True)
        self._update_stats()
        self._clear_log()

        plat = self._platform_var.get()
        target = self._target_var.get()
        
        self._log_msg(f"Target logic : {plat}", "info")
        self._log_msg(f"Target URL   : {url_raw}", "info")
        self._log_msg(f"Target limit : {target} items", "info")
        self._set_progress(0, target, "Starting…")

        thread = threading.Thread(target=self._scrape_thread, args=(plat, url_raw, target), daemon=True)
        thread.start()

    def _stop_scraping(self):
        self._stop_flag = True
        self._log_msg("Stop requested...", "warn")

    def _scrape_thread(self, plat, target_url, target_count):
        driver = None
        try:
            self._log_msg("Starting Chrome Driver...", "info")
            opts = Options()
            if plat == "News Websites":
                opts.add_argument("--headless=new")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            opts.add_experimental_option("useAutomationExtension", False)
            opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
            
            svc = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=svc, options=opts)
            self._driver = driver
            driver.set_window_size(1280, 900)

            # Handle Cookies for Social Media
            if plat != "News Websites" and os.path.exists(self._cookies_var.get()):
                self._log_msg("Injecting cookies...", "info")
                try:
                    with open(self._cookies_var.get(), encoding="utf-8") as f:
                        cookies = json.load(f)
                    
                    if "Facebook" in plat or "All" in plat:
                        driver.get("https://www.facebook.com")
                        driver.delete_all_cookies()
                        for c in cookies:
                            if "facebook.com" in c.get("domain", ""):
                                driver.add_cookie({"name": c.get("name",""), "value": c.get("value",""), "domain": ".facebook.com", "path": "/"})
                    
                    if "Twitter" in plat or "All" in plat:
                        driver.get("https://twitter.com")
                        for c in cookies:
                            if "twitter.com" in c.get("domain", "") or "x.com" in c.get("domain", ""):
                                driver.add_cookie({"name": c.get("name",""), "value": c.get("value",""), "domain": ".twitter.com", "path": "/"})
                except Exception as e:
                    self._log_msg(f"Failed to inject cookies: {e}", "warn")

            if plat == "News Websites":
                self._scrape_news(driver, target_url, target_count)
            elif plat == "Facebook":
                self._scrape_facebook(driver, target_url, target_count)
            elif plat == "Twitter / X":
                self._scrape_twitter(driver, target_url, target_count)
            elif plat == "Instagram":
                self._scrape_generic_social(driver, target_url, target_count, "Instagram")
            elif "All Social Media" in plat:
                self._log_msg("Scraping Facebook...", "info")
                self._scrape_facebook(driver, "https://www.facebook.com/search/posts/?q=" + target_url, target_count // 3)
                if not self._stop_flag:
                    self._log_msg("Scraping Twitter...", "info")
                    self._scrape_twitter(driver, "https://twitter.com/search?q=" + target_url, target_count // 3)
                if not self._stop_flag:
                    self._log_msg("Scraping Instagram...", "info")
                    self._scrape_generic_social(driver, "https://www.instagram.com/explore/tags/" + target_url, target_count // 3, "Instagram")

            if self._items:
                self._save_csv()

        except Exception as ex:
            self._log_msg(f"ERROR: {ex}", "err")
        finally:
            if driver:
                try: driver.quit()
                except: pass
            self._driver = None
            self.after(0, self._on_done)

    def _scrape_news(self, driver, base_url, target):
        if not base_url.startswith("http"): base_url = "https://" + base_url
        self._log_msg("Starting recursive crawl from News homepage...", "info")
        
        visited_urls = set()
        pending_urls = [base_url]
        
        while pending_urls and len(self._items) < target and not self._stop_flag:
            current_url = pending_urls.pop(0)
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)
            
            try:
                self._log_msg(f"Reading: {current_url[:60]}...", "muted")
                driver.get(current_url)
                time.sleep(2)
                
                # Scroll slightly to trigger lazy-loaded images/links if any
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/1.5);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)

                page_soup = BeautifulSoup(driver.page_source, "html.parser")
                
                # 1) Search for new links (Breadth-First Search)
                for a in page_soup.find_all("a", href=True):
                    href = a["href"]
                    if is_valid_article_link(base_url, href):
                        full_link = urljoin(base_url, href)
                        # Remove fragment/hash from URLs
                        full_link = full_link.split("#")[0]
                        if full_link not in visited_urls and full_link not in pending_urls:
                            pending_urls.append(full_link)
                            
                # 2) Extract content and treat as article if enough text is found
                title = page_soup.find("h1")
                title_text = clean_text(title.get_text()) if title else ""
                
                paras = [clean_text(p.get_text()) for p in page_soup.find_all("p")]
                full_text = "\n".join([p for p in paras if len(p) > 30])
                
                # Skip saving if text is too short (likely page is not an article or is the homepage)
                if len(full_text) >= 100:
                    cat = classify(full_text + " " + title_text)
                    self._items.append({
                        "url": current_url, "text": title_text + "\n" + full_text,
                        "category": cat
                    })
                    tag = "crime" if cat == "crime-related" else "ok"
                    self._log_msg(f"✅ [{len(self._items)}/{target}] {title_text[:50]}", tag)
                    self._update_stats()
                    self._set_progress(len(self._items), target)
                
            except Exception as e:
                self._log_msg(f"Error on {current_url}: {e}", "err")

    def _scrape_facebook(self, driver, url, target):
        if not url.startswith("http"): url = "https://www.facebook.com/" + url.strip("/")
        driver.get(url)
        time.sleep(6)
        self._scroll_and_extract_social(driver, target, "Facebook", [ 
            "//div[@role='article']", 
            "//div[@data-pagelet='ProfileTimeline']"
        ])

    def _scrape_twitter(self, driver, url, target):
        if not url.startswith("http"): url = "https://twitter.com/" + url.strip("/")
        driver.get(url)
        time.sleep(6)
        self._scroll_and_extract_social(driver, target, "Twitter", ["//article"])

    def _scrape_generic_social(self, driver, url, target, plat_name):
        if not url.startswith("http"): url = f"https://www.{plat_name.lower()}.com/" + url.strip("/")
        driver.get(url)
        time.sleep(6)
        self._scroll_and_extract_social(driver, target, plat_name, ["//article", "//div[contains(@class, 'post')]"])

    def _scroll_and_extract_social(self, driver, target, platform, xpaths):
        seen = set()
        no_new = 0
        scroll_count = 0
        
        while len(self._items) < target and no_new < 10 and not self._stop_flag:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Click See More on FB randomly if any
            if platform == "Facebook":
                try:
                    btns = driver.find_elements(By.XPATH, "//div[@role='button' and contains(.,'See more')]")
                    for b in btns[:2]: 
                        driver.execute_script("arguments[0].click();", b)
                        time.sleep(0.5)
                except: pass

            gained = 0
            if platform == "Facebook":
                blocks = soup.find_all(attrs={"role": "article"}) + soup.find_all(attrs={"dir": "auto"})
            elif platform == "Twitter":
                blocks = soup.find_all("article")
            else:
                blocks = soup.find_all("article") + soup.find_all("div", dir="auto")

            for block in blocks:
                text = re.sub(r"\s+", " ", block.get_text(" ", strip=True)).strip()
                if len(text) < 30 or is_junk(text): continue
                key = text[:150]
                if key in seen: continue
                seen.add(key)
                
                url = driver.current_url
                for a in block.find_all("a", href=True):
                    if "status" in a["href"] or "posts" in a["href"] or "p" in a["href"]:
                        if a["href"].startswith("/"):
                            url = urljoin(driver.current_url, a["href"])
                        else:
                            url = a["href"]
                        break
                
                cat = classify(text)
                self._items.append({
                    "url": url, "text": text,
                    "category": cat
                })
                gained += 1
                tag = "crime" if cat == "crime-related" else "ok"
                self._log_msg(f"[{len(self._items)}/{target}] {platform}: {text[:60]}...", tag)
                self._update_stats()
                self._set_progress(len(self._items), target)
                if len(self._items) >= target: break

            if gained == 0: no_new += 1
            else: no_new = 0

            driver.execute_script(f"window.scrollBy(0, {random.randint(500, 900)});")
            time.sleep(random.uniform(2.5, 4.5))
            scroll_count += 1

    def _save_csv(self):
        base_dir = os.path.dirname(self._save_path.get()) if self._save_path.get() else os.getcwd()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"universal_scraped_{ts}.csv"
        path = os.path.join(base_dir, filename)

        try:
            df = pd.DataFrame(self._items, columns=["url", "text", "category"])
            df.to_csv(path, index=False, encoding="utf-8-sig")
            self._save_path.set(path)
            self._log_msg(f"✅  Saved {len(self._items)} items → {path}", "info")
        except Exception as ex:
            self._log_msg(f"❌  Save error: {ex}", "err")

    def _on_done(self):
        self._set_running(False)
        total = len(self._items)
        self._set_progress(total, self._target_var.get(), f"Done — {total} items extracted")
        self._log_msg("─" * 55, "muted")
        self._log_msg(f"FINISHED  —  Total: {total}", "bold")


if __name__ == "__main__":
    app = ScraperGUI()
    app.mainloop()
