# -*- coding: utf-8 -*-
"""
scraper_gui.py  —  Facebook Page Scraper  (GUI)
================================================
Run:  python -X utf8 scraper_gui.py
"""
import os, sys, json, time, re, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# ── fix Windows console encoding ──────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── lazy imports (selenium / bs4 / pandas) ────────────────────────────────────
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
    import pandas as pd
    DEPS_OK = True
except ImportError as e:
    DEPS_OK = False
    DEPS_ERROR = str(e)

# ── Crime keywords ─────────────────────────────────────────────────────────────
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
    import re
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
            score -= 8  # Waxay hoos u dhigaysaa score-ka haddii uu yahay war Isboorti ama Ganacsi
            
    # Haddii score-ku uu ka sarreeyo 5, markaas waa crime-related
    if score >= 10:
        return "crime-related"
    return "not crime-related"

def is_junk(text):
    if not text: return True
    words = text.split()
    if len(words) >= 8 and all(len(w) <= 2 for w in words[:8]): return True
    if len(words) == 1 and len(text) > 40: return True
    return False

def normalise_url(raw):
    """Accept  facebook.com/page  or  MunasarMohamedAbd  → full URL."""
    raw = raw.strip().rstrip("/")
    if raw.startswith("http"):
        return raw
    if "facebook.com" in raw:
        return "https://" + raw if not raw.startswith("http") else raw
    return f"https://www.facebook.com/{raw}"

# ══════════════════════════════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════════════════════════════
BG       = "#0f1117"
SURFACE  = "#1a1d27"
CARD     = "#22263a"
ACCENT   = "#4f8ef7"
ACCENT2  = "#7c3aed"
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
        self.title("Facebook Post Scraper")
        self.geometry("980x720")
        self.minsize(820, 600)
        self.configure(bg=BG)
        self.resizable(True, True)

        self._scraping   = False
        self._stop_flag  = False
        self._posts      = []
        self._driver     = None
        self._save_path  = tk.StringVar(value=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "scraped_posts.csv"))

        self._build_ui()
        self._check_deps()

    # ── UI build ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._header()
        self._main_panel()
        self._statusbar()

    def _header(self):
        hdr = tk.Frame(self, bg=SURFACE, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # gradient-ish left bar
        accent_bar = tk.Frame(hdr, bg=ACCENT, width=4)
        accent_bar.pack(side="left", fill="y")

        tk.Label(hdr, text="  🌐", font=(FONT_FAMILY, 20),
                 bg=SURFACE, fg=ACCENT).pack(side="left", padx=(12,4), pady=10)
        tk.Label(hdr, text="Facebook Post Scraper",
                 font=(FONT_FAMILY, 16, "bold"),
                 bg=SURFACE, fg=TEXT).pack(side="left", pady=10)
        tk.Label(hdr, text="  —  crime detection powered",
                 font=(FONT_FAMILY, 10), bg=SURFACE, fg=MUTED).pack(side="left")

        # top-right badge
        self._lbl_status_badge = tk.Label(
            hdr, text="● IDLE", font=(FONT_FAMILY, 9, "bold"),
            bg=SURFACE, fg=MUTED)
        self._lbl_status_badge.pack(side="right", padx=20)

    def _main_panel(self):
        pane = tk.Frame(self, bg=BG)
        pane.pack(fill="both", expand=True, padx=18, pady=14)

        # left column  ──────────────────────────────────────────────────────
        left = tk.Frame(pane, bg=BG, width=320)
        left.pack(side="left", fill="y", padx=(0,12))
        left.pack_propagate(False)

        self._card_settings(left)
        self._card_cookies(left)
        self._card_output(left)
        self._card_stats(left)

        # right column ──────────────────────────────────────────────────────
        right = tk.Frame(pane, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self._card_log(right)
        self._card_progress(right)

    # ── Settings card ─────────────────────────────────────────────────────────
    def _card_settings(self, parent):
        card = self._card(parent, "⚙  Scraper Settings")

        # URL
        self._lbl(card, "Facebook Page URL or Username")
        self._url_var = tk.StringVar(value="MunasarMohamedAbd")
        url_frame = tk.Frame(card, bg=CARD)
        url_frame.pack(fill="x", pady=(2,8))
        tk.Label(url_frame, text="🔗", bg=CARD, fg=ACCENT,
                 font=(FONT_FAMILY, 11)).pack(side="left", padx=(0,4))
        self._ent_url = tk.Entry(url_frame, textvariable=self._url_var,
                                  bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                                  relief="flat", font=(FONT_FAMILY, 10),
                                  highlightthickness=1,
                                  highlightbackground=BORDER,
                                  highlightcolor=ACCENT)
        self._ent_url.pack(fill="x", expand=True, ipady=6)

        # Target count
        self._lbl(card, "Target Number of Posts")
        self._target_var = tk.IntVar(value=200)
        spin_frame = tk.Frame(card, bg=CARD)
        spin_frame.pack(fill="x", pady=(2,8))
        self._spin = tk.Spinbox(spin_frame, from_=10, to=1000,
                                  textvariable=self._target_var,
                                  bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                                  buttonbackground=SURFACE,
                                  relief="flat", font=(FONT_FAMILY, 10),
                                  highlightthickness=1,
                                  highlightbackground=BORDER,
                                  highlightcolor=ACCENT, width=10)
        self._spin.pack(side="left", ipady=5)

        # Buttons row
        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(fill="x", pady=(6,2))

        self._btn_start = self._btn(btn_row, "▶  Start Scraping",
                                     ACCENT, self._start_scraping, side="left")
        self._btn_stop  = self._btn(btn_row, "■  Stop",
                                     RED, self._stop_scraping,
                                     side="left", padx=(6,0), state="disabled")

    # ── Cookies card ──────────────────────────────────────────────────────────
    def _card_cookies(self, parent):
        card = self._card(parent, "🍪  Cookies")

        cookies_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fb_cookies.json")
        self._cookies_var = tk.StringVar(value=cookies_path)

        self._lbl(card, "fb_cookies.json path")
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=(2,6))
        tk.Entry(row, textvariable=self._cookies_var,
                 bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=(FONT_FAMILY, 9),
                 highlightthickness=1, highlightbackground=BORDER).pack(
                 side="left", fill="x", expand=True, ipady=5)
        self._btn(row, "…", SURFACE, self._browse_cookies,
                  side="left", padx=(4,0), fg=TEXT)

        self._btn(card, "🔐  Refresh Cookies (get_cookies.py)",
                  "#1e293b", self._refresh_cookies, fill="x")

        self._lbl_cookies_info = tk.Label(
            card, text="", bg=CARD, fg=MUTED, font=(FONT_FAMILY, 8),
            anchor="w")
        self._lbl_cookies_info.pack(fill="x")
        self._check_cookie_file()

    # ── Output card ───────────────────────────────────────────────────────────
    def _card_output(self, parent):
        card = self._card(parent, "💾  Output CSV")

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", pady=(2,6))
        tk.Entry(row, textvariable=self._save_path,
                 bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=(FONT_FAMILY, 9),
                 highlightthickness=1, highlightbackground=BORDER).pack(
                 side="left", fill="x", expand=True, ipady=5)
        self._btn(row, "…", SURFACE, self._browse_save,
                  side="left", padx=(4,0), fg=TEXT)

        self._btn(card, "📂  Open CSV in Folder",
                  "#1e293b", self._open_folder, fill="x")

    # ── Stats card ────────────────────────────────────────────────────────────
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

    # ── Log card ──────────────────────────────────────────────────────────────
    def _card_log(self, parent):
        card = self._card(parent, "📋  Live Log", expand=True)

        self._log = tk.Text(
            card, bg=SURFACE, fg=TEXT, font=("Consolas", 9),
            relief="flat", state="disabled", wrap="word",
            selectbackground=ACCENT, selectforeground=TEXT,
            highlightthickness=0)
        self._log.pack(fill="both", expand=True)

        # colour tags
        self._log.tag_configure("crime",  foreground=RED)
        self._log.tag_configure("ok",     foreground=GREEN)
        self._log.tag_configure("info",   foreground=ACCENT)
        self._log.tag_configure("warn",   foreground=YELLOW)
        self._log.tag_configure("err",    foreground="#ff6b6b")
        self._log.tag_configure("muted",  foreground=MUTED)
        self._log.tag_configure("bold",   font=("Consolas", 9, "bold"))

        # scrollbar
        sb = ttk.Scrollbar(self._log, command=self._log.yview)
        sb.pack(side="right", fill="y")
        self._log.configure(yscrollcommand=sb.set)

        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(fill="x", pady=(4,0))
        self._btn(btn_row, "🗑  Clear Log", "#1e293b", self._clear_log,
                  side="left")

    # ── Progress card ─────────────────────────────────────────────────────────
    def _card_progress(self, parent):
        card = self._card(parent, "⏳  Progress")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("accent.Horizontal.TProgressbar",
                        troughcolor=SURFACE, background=ACCENT,
                        bordercolor=SURFACE, lightcolor=ACCENT,
                        darkcolor=ACCENT2)

        self._progress_var = tk.DoubleVar(value=0)
        self._progress_bar = ttk.Progressbar(
            card, variable=self._progress_var,
            style="accent.Horizontal.TProgressbar",
            mode="determinate", maximum=100)
        self._progress_bar.pack(fill="x", pady=(0,4))

        self._lbl_progress = tk.Label(
            card, text="Waiting to start…",
            bg=CARD, fg=MUTED, font=(FONT_FAMILY, 9))
        self._lbl_progress.pack(anchor="w")

    # ── Status bar ────────────────────────────────────────────────────────────
    def _statusbar(self):
        bar = tk.Frame(self, bg=SURFACE, height=26)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Frame(bar, bg=ACCENT, width=4).pack(side="left", fill="y")
        self._lbl_status = tk.Label(
            bar, text="  Ready", bg=SURFACE, fg=MUTED,
            font=(FONT_FAMILY, 8), anchor="w")
        self._lbl_status.pack(side="left", fill="x", expand=True)
        tk.Label(bar, text=f"  v3  •  {datetime.now().strftime('%Y-%m-%d')}  ",
                 bg=SURFACE, fg=MUTED, font=(FONT_FAMILY, 8)).pack(side="right")

    # ── Widget helpers ────────────────────────────────────────────────────────
    def _card(self, parent, title, expand=False):
        outer = tk.Frame(parent, bg=BORDER, pady=1)
        outer.pack(fill="x" if not expand else "both",
                   expand=expand, pady=(0, 10))
        inner = tk.Frame(outer, bg=CARD, padx=14, pady=10)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=title, font=(FONT_FAMILY, 9, "bold"),
                 bg=CARD, fg=ACCENT).pack(anchor="w", pady=(0,6))
        return inner

    def _lbl(self, parent, text):
        tk.Label(parent, text=text, bg=CARD, fg=MUTED,
                 font=(FONT_FAMILY, 8)).pack(anchor="w")

    def _btn(self, parent, text, color, cmd, side=None,
             padx=0, fill=None, state="normal", fg="white"):
        btn = tk.Button(parent, text=text, bg=color, fg=fg,
                        font=(FONT_FAMILY, 9, "bold"),
                        relief="flat", cursor="hand2",
                        activebackground=ACCENT2,
                        activeforeground="white",
                        padx=10, pady=6,
                        command=cmd, state=state)
        if side:
            btn.pack(side=side, padx=padx)
        elif fill:
            btn.pack(fill=fill, pady=(3,0))
        else:
            btn.pack(pady=(3,0))

        # hover effect
        btn.bind("<Enter>", lambda e, b=btn, c=color:
                 b.configure(bg=self._lighten(c)))
        btn.bind("<Leave>", lambda e, b=btn, c=color:
                 b.configure(bg=c))
        return btn

    @staticmethod
    def _lighten(hex_color):
        """Slightly lighten a hex color for hover."""
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            r = min(255, r + 30)
            g = min(255, g + 30)
            b = min(255, b + 30)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    # ── Logging ───────────────────────────────────────────────────────────────
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

    # ── Dependency check ──────────────────────────────────────────────────────
    def _check_deps(self):
        if not DEPS_OK:
            self._log_msg(f"Missing dependency: {DEPS_ERROR}", "err")
            self._log_msg("Run:  pip install selenium webdriver-manager beautifulsoup4 pandas", "warn")

    def _check_cookie_file(self):
        p = self._cookies_var.get()
        if os.path.exists(p):
            try:
                with open(p) as f:
                    c = json.load(f)
                self._lbl_cookies_info.configure(
                    text=f"✅  {len(c)} cookies found", fg=GREEN)
            except Exception:
                self._lbl_cookies_info.configure(
                    text="⚠  Could not read file", fg=YELLOW)
        else:
            self._lbl_cookies_info.configure(
                text="❌  File not found — run Refresh Cookies", fg=RED)

    # ── Browsing ──────────────────────────────────────────────────────────────
    def _browse_cookies(self):
        p = filedialog.askopenfilename(
            title="Select fb_cookies.json",
            filetypes=[("JSON files", "*.json"), ("All", "*.*")])
        if p:
            self._cookies_var.set(p)
            self._check_cookie_file()

    def _browse_save(self):
        p = filedialog.asksaveasfilename(
            title="Save CSV as…",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")])
        if p:
            self._save_path.set(p)

    def _open_folder(self):
        p = self._save_path.get()
        folder = os.path.dirname(p) if p else os.getcwd()
        os.startfile(folder)

    def _refresh_cookies(self):
        script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "get_cookies.py")
        if not os.path.exists(script):
            messagebox.showerror("Error", f"get_cookies.py not found:\n{script}")
            return
        import subprocess
        subprocess.Popen([sys.executable, "-X", "utf8", script])
        self._log_msg("get_cookies.py opened in a new window.", "info")
        self._log_msg("Log in, press ENTER, then come back here.", "warn")
        # Poll for cookie file update
        self.after(5000, self._check_cookie_file)

    # ── UI state ──────────────────────────────────────────────────────────────
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
        total  = len(self._posts)
        crime  = sum(1 for p in self._posts if p["category"] == "crime-related")
        clean  = total - crime
        self.after(0, lambda: self._stat_total.configure(text=str(total)))
        self.after(0, lambda: self._stat_crime.configure(text=str(crime)))
        self.after(0, lambda: self._stat_ok.configure(text=str(clean)))

    def _set_progress(self, done, total, msg=""):
        pct = (done / total * 100) if total else 0
        self.after(0, lambda: self._progress_var.set(pct))
        label = msg or f"{done} / {total} posts  ({pct:.0f}%)"
        self.after(0, lambda: self._lbl_progress.configure(text=label))
        self.after(0, lambda: self._lbl_status.configure(text=f"  {label}"))

    # ── Scraping ──────────────────────────────────────────────────────────────
    def _start_scraping(self):
        if not DEPS_OK:
            messagebox.showerror("Missing dependencies",
                                 "Install:  pip install selenium webdriver-manager beautifulsoup4 pandas")
            return

        url_raw = self._url_var.get().strip()
        if not url_raw:
            messagebox.showwarning("No URL", "Please enter a Facebook page URL or username.")
            return

        cookies_path = self._cookies_var.get()
        if not os.path.exists(cookies_path):
            if not messagebox.askyesno(
                    "No cookies",
                    "fb_cookies.json not found.\n\nContinue anyway? "
                    "(you will need to log in manually in the browser)"):
                return

        self._posts     = []
        self._stop_flag = False
        self._set_running(True)
        self._update_stats()
        self._clear_log()

        target = self._target_var.get()
        page_url = normalise_url(url_raw)
        self._log_msg(f"Target page : {page_url}", "info")
        self._log_msg(f"Target posts: {target}", "info")
        self._set_progress(0, target, "Starting…")

        thread = threading.Thread(
            target=self._scrape_thread,
            args=(page_url, target, cookies_path),
            daemon=True)
        thread.start()

    def _stop_scraping(self):
        self._stop_flag = True
        self._log_msg("Stop requested — finishing current scroll…", "warn")

    def _scrape_thread(self, page_url, target, cookies_path):
        driver = None
        try:
            # Build driver
            self._log_msg("Starting Chrome…", "info")
            opts = Options()
            opts.add_argument("--disable-gpu")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            opts.add_experimental_option("useAutomationExtension", False)
            opts.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36")
            svc    = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=svc, options=opts)
            driver.execute_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
            driver.set_window_size(1280, 900)
            self._driver = driver

            # Inject cookies
            cookies = []
            if os.path.exists(cookies_path):
                with open(cookies_path, encoding="utf-8") as f:
                    cookies = json.load(f)
                self._log_msg(f"Injecting {len(cookies)} cookies…", "info")
                driver.get("https://www.facebook.com")
                time.sleep(3)
                driver.delete_all_cookies()
                for c in cookies:
                    try:
                        driver.add_cookie({
                            "name":   c.get("name",""),
                            "value":  c.get("value",""),
                            "domain": ".facebook.com",
                            "path":   "/",
                        })
                    except Exception:
                        pass
            else:
                self._log_msg("No cookies file — opening Facebook for manual login…", "warn")
                driver.get("https://www.facebook.com/login")

            # Navigate to page
            self._log_msg(f"Opening: {page_url}", "info")
            driver.get(page_url)
            time.sleep(6)

            cur = driver.current_url
            if "login" in cur:
                self._log_msg("⚠ Redirected to login — log in manually in the browser!", "warn")
                self._log_msg("After logging in Facebook will redirect to the page.", "warn")
                # Wait up to 90s for user to log in
                for _ in range(90):
                    time.sleep(1)
                    if "login" not in driver.current_url:
                        break
                driver.get(page_url)
                time.sleep(5)

            # Scrape loop
            seen  = set()
            no_new = 0
            MAX_NO_NEW = 10
            scroll_n   = 0

            while len(self._posts) < target and no_new < MAX_NO_NEW and not self._stop_flag:
                scroll_n += 1

                # ── Expand all truncated posts before parsing ──────────────────
                self._click_see_more(driver)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                new  = self._extract(soup, seen, page_url)

                gained = 0
                for p in new:
                    if len(self._posts) >= target or self._stop_flag:
                        break
                    self._posts.append(p)
                    gained += 1
                    tag    = "crime" if p["category"] == "crime-related" else "ok"
                    icon   = "🔴" if tag == "crime" else "🟢"
                    self._log_msg(
                        f"[{len(self._posts):>3}/{target}] {icon} {p['text'][:85]}",
                        tag)
                    self._update_stats()
                    self._set_progress(len(self._posts), target)

                if gained == 0:
                    no_new += 1
                    self._log_msg(
                        f"  scroll {scroll_n} — no new ({no_new}/{MAX_NO_NEW})", "muted")
                else:
                    no_new = 0

                if len(self._posts) >= target or self._stop_flag:
                    break

                # Human-like scroll
                import random
                total_h = driver.execute_script("return document.body.scrollHeight")
                cur_pos = driver.execute_script("return window.pageYOffset")
                step    = random.randint(400, 700)
                while cur_pos < total_h and not self._stop_flag:
                    cur_pos += step
                    driver.execute_script(f"window.scrollTo(0, {cur_pos});")
                    time.sleep(random.uniform(0.2, 0.5))
                time.sleep(random.uniform(3.5, 5))

            # Save CSV
            if self._posts:
                self._save_csv()

        except Exception as ex:
            self._log_msg(f"ERROR: {ex}", "err")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            self._driver = None
            self.after(0, self._on_done)

    def _click_see_more(self, driver):
        """
        Click every visible 'See more' / expand button inside articles
        so that full post text is loaded into the DOM before we parse.
        """
        xpaths = [
            "//div[@role='article']//div[@role='button' and contains(.,'See more')]",
            "//div[@role='article']//span[@role='button' and contains(.,'See more')]",
            "//div[@role='article']//span[text()='See more']",
            "//div[@role='article']//span[text()='See More']",
        ]
        clicked = 0
        for xp in xpaths:
            try:
                btns = driver.find_elements(By.XPATH, xp)
                for btn in btns:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        time.sleep(0.2)
                        driver.execute_script("arguments[0].click();", btn)
                        clicked += 1
                        time.sleep(0.3)
                    except Exception:
                        pass
            except Exception:
                pass
        if clicked:
            self._log_msg(f"  ↳ Expanded {clicked} 'See more' buttons", "muted")
            time.sleep(0.8)  # let DOM update

    def _extract(self, soup, seen, base_url):
        results = []

        for art in soup.find_all(attrs={"role": "article"}):
            post_url = base_url
            for a in art.find_all("a", href=True):
                h = a["href"]
                if any(x in h for x in ["/posts/", "/permalink/", "story_fbid=", "fbid="]):
                    if not h.startswith("http"):
                        h = "https://www.facebook.com" + h
                    post_url = h.split("?")[0]
                    break

            raw = re.sub(r"\s+", " ", art.get_text(" ", strip=True)).strip()
            if not raw or len(raw) < 30 or is_junk(raw):
                continue
            key = raw[:200]
            if key in seen:
                continue
            seen.add(key)
            # Full text — no character limit
            results.append({"text": raw, "url": post_url,
                             "category": classify(raw)})

        # fallback: dir=auto spans
        for el in soup.find_all(["div", "span"], attrs={"dir": "auto"}):
            raw = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
            if not raw or len(raw) < 40 or is_junk(raw):
                continue
            key = raw[:200]
            if key in seen:
                continue
            seen.add(key)
            # Full text — no character limit
            results.append({"text": raw, "url": base_url,
                             "category": classify(raw)})

        return results

    def _save_csv(self):
        import pandas as pd

        # Always create a brand-new timestamped filename so we never
        # collide with a file that may still be open in Excel.
        base_dir = os.path.dirname(self._save_path.get()) \
                   if self._save_path.get() \
                   else os.path.dirname(os.path.abspath(__file__))

        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraped_posts_{ts}.csv"
        path     = os.path.join(base_dir, filename)

        try:
            df = pd.DataFrame(self._posts, columns=["text", "url", "category"])
            df.to_csv(path, index=False, encoding="utf-8-sig")
            # Update the path field in the GUI so the user can see it
            self._save_path.set(path)
            self._log_msg(f"✅  Saved {len(self._posts)} posts →", "info")
            self._log_msg(f"    {path}", "info")
        except PermissionError:
            # Fallback: add extra milliseconds to guarantee a unique name
            import time as _t
            ts2   = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{int(_t.time()*1000)%1000:03d}"
            path2 = os.path.join(base_dir, f"scraped_posts_{ts2}.csv")
            try:
                df.to_csv(path2, index=False, encoding="utf-8-sig")
                self._save_path.set(path2)
                self._log_msg(f"✅  Saved (fallback) → {path2}", "info")
            except Exception as ex2:
                self._log_msg(f"❌  Could not save: {ex2}", "err")
        except Exception as ex:
            self._log_msg(f"❌  Save error: {ex}", "err")

    def _on_done(self):
        self._set_running(False)
        total  = len(self._posts)
        crime  = sum(1 for p in self._posts if p["category"] == "crime-related")
        clean  = total - crime
        self._set_progress(total, self._target_var.get(),
                           f"Done — {total} posts  |  🔴 {crime} crime  |  🟢 {clean} clean")
        self._log_msg("─" * 55, "muted")
        self._log_msg(f"FINISHED  —  Total: {total}  |  Crime: {crime}  |  Clean: {clean}", "bold")


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ScraperGUI()
    app.mainloop()
