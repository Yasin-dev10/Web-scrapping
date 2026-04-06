# -*- coding: utf-8 -*-
"""
Facebook Page Scraper - MunasarMohamedAbd
==========================================
TARGET : 200 posts
OUTPUT : CSV  =>  text | url | category
METHOD : facebook-scraper library  (+ Selenium fallback)

HOW TO USE
----------
Option A  (cookies — best results):
  1. Install Chrome extension "Cookie-Editor"
     https://chromewebstore.google.com/detail/cookie-editor/
  2. Open Facebook.com and log in
  3. Click Cookie-Editor => Export => "Export as JSON"
  4. Save the file as:  fb_cookies.json   (same folder as this script)
  5. Run:  python fb_scraper_final.py

Option B  (no cookies — public posts only):
  Just run:  python fb_scraper_final.py
  => Browser opens, log in manually, then press ENTER in terminal
"""

import os, sys, json, time, re, subprocess
import pandas as pd
from datetime import datetime

# ── make stdout UTF-8 so Somali / Arabic text prints correctly ──────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ============================================================
#  SETTINGS
# ============================================================
PAGE_NAME    = "MunasarMohamedAbd"
TARGET_ROWS  = 200
COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb_cookies.json")
OUTPUT_DIR   = os.path.dirname(os.path.abspath(__file__))

# ============================================================
#  CRIME KEYWORDS  (Somali + English + Arabic)
# ============================================================
CRIME_KEYWORDS = [
    # ---- Somali ----
    "dil","dilka","dilaan","dilay","la dilay","la dili","dilmay","la laayay",
    "xasuuq","xasuuqa","xasuuqay",
    "rasaas","ridmad","xabbad","madaafiic","hubeysi",
    "dhaawac","dhaawacay","dhaawacmay","dhaawaco",
    "xabsi","xabasheet","xidhay","la xidhay","la xidhi",
    "kufsi","kufsaday","kasoo xadday","xad-guduub",
    "boob","boobo","boobka","tuugnimo","xaday","tuug",
    "qarax","bomba","qaraxay","gantaal",
    "colaad","dagaal","dagaalka","rabshad","rabshadaha",
    "argagax","argagixiso","gacan-ku-haynta","argagixisad",
    "hanjabaad","hanjabaadka","hanjabay",
    "maxkamad","garsoor","dacwad","dembi","dembiga","xukun",
    "booliska","ciidanka","la qabtay","qabashada",
    "hub","qori","hubka",
    "weerar","la weeraray","in la laayo",
    "gef","xaloofo","basaas","cadaadis",
    "nafta","baqdin","cabsi","baqday",
    "duullaan","xarig","dilac",
    "gaadiidka laga xaday","lacag laga xaday",
    "la toogtay","la garaacay",
    "askari","gaashaanle","ciidamada",
    # ---- English ----
    "murder","killed","killing","dead","found dead",
    "shooting","shot","gunfire","gunman",
    "crime","criminal","suspect","convicted",
    "arrested","arrest","detained","detention","jailed",
    "attack","attacked","violence","violent",
    "robbery","robbed","theft","stolen","looted",
    "rape","sexual assault",
    "bomb","explosion","blast","shelling","airstrike",
    "terror","terrorist","terrorism","extremist","militant",
    "weapon","knife","stabbing","stabbed",
    "assault","fight","clash","clashes","riot",
    "kidnap","kidnapping","abduction","hostage","ransom",
    "prison","jail","court","verdict","prosecution",
    "police","troops","military","forces","army",
    "war","conflict","crisis","unrest","protest",
    "casualty","casualties","wounded","injured",
    "execution","executed","tortured",
    "threat","threatened","danger",
    "massacre","genocide",
    # ---- Arabic ----
    "قتل","مقتل","جريمة","سرقة","اعتقال","عنف",
    "انفجار","ارهاب","اغتصاب","اعتداء","شرطة",
    "ضحايا","جرح","اطلاق نار","حرب","معركة",
    "جيش","قوات","تهديد","احتجاز","اختطاف",
    "اعدام","قصف","غارة",
]


def classify(text: str) -> str:
    t = (text or "").lower()
    for kw in CRIME_KEYWORDS:
        if kw.lower() in t:
            return "crime-related"
    return "not crime-related"


# ============================================================
#  HELPER — load cookies
# ============================================================
def load_cookies() -> list:
    if not os.path.exists(COOKIES_FILE):
        return []
    try:
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"  [cookies] Read error: {e}")
        return []


def cookies_to_netscape(cookies: list) -> str:
    """Convert Cookie-Editor JSON list => Netscape cookie string for facebook-scraper."""
    parts = []
    for c in cookies:
        nm = c.get("name","")
        vl = c.get("value","")
        if nm:
            parts.append(f"{nm}={vl}")
    return "; ".join(parts)


# ============================================================
#  METHOD 1 — facebook-scraper
# ============================================================
def _import_get_posts():
    """
    Import get_posts from the installed facebook-scraper package
    while ignoring the local facebook_scraper.py file.
    """
    cwd = os.path.dirname(os.path.abspath(__file__))
    # Temporarily strip current dir from path
    orig_path = sys.path[:]
    sys.path = [p for p in sys.path if p not in ("", cwd)]
    try:
        from facebook_scraper import get_posts
        return get_posts
    except ImportError:
        return None
    finally:
        sys.path = orig_path


def method_facebook_scraper(cookies: list) -> list:
    get_posts = _import_get_posts()
    if get_posts is None:
        print("  [M1] facebook-scraper not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "facebook-scraper", "-q"])
        get_posts = _import_get_posts()
    if get_posts is None:
        print("  [M1] Install failed. Skipping method 1.")
        return []

    posts = []
    seen  = set()
    cookie_str = cookies_to_netscape(cookies) if cookies else None

    print(f"  [M1] Page: {PAGE_NAME}  |  Cookies: {'YES' if cookie_str else 'NO (public only)'}")

    options = {"posts_per_page": 10, "progress": False, "allow_extra_requests": True}

    try:
        kw = dict(account=PAGE_NAME, pages=999, options=options,
                  extra_info=False, youtube_dl=False)
        if cookie_str:
            kw["cookies"] = cookie_str

        for post in get_posts(**kw):
            if len(posts) >= TARGET_ROWS:
                break

            text = (post.get("post_text") or post.get("text") or "").strip()
            url  = post.get("post_url") or f"https://www.facebook.com/{PAGE_NAME}"
            dt   = post.get("time")
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S") if hasattr(dt,"strftime") else str(dt or "")

            if not text or text in seen or len(text) < 5:
                continue
            seen.add(text)
            cat = classify(text)
            posts.append({"date": date_str, "text": text[:3000], "url": url, "category": cat})
            marker = "[CRIME]" if cat == "crime-related" else "[OK]"
            print(f"  [{len(posts):>3}/{TARGET_ROWS}] {marker} {text[:90]}")

    except KeyboardInterrupt:
        print("  [M1] Interrupted.")
    except Exception as e:
        print(f"  [M1] Error: {e}")

    return posts


# ============================================================
#  METHOD 2 — Selenium + mbasic.facebook.com
# ============================================================
def method_selenium(needed: int) -> list:
    print(f"\n  [M2] Selenium browser opening... need {needed} more posts")

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        from bs4 import BeautifulSoup
    except ImportError as e:
        print(f"  [M2] Import error: {e}")
        return []

    opts = Options()
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    )

    svc    = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=svc, options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    posts = []
    seen  = set()

    try:
        # ── Login ──────────────────────────────────────────────────────────
        driver.get("https://www.facebook.com/login")
        time.sleep(2)
        print()
        print("  +-------------------------------------------------------+")
        print("  |  BROWSER IS OPEN — LOG IN TO FACEBOOK NOW             |")
        print("  |  1. Enter your email & password in the browser window |")
        print("  |  2. Complete 2FA if asked                             |")
        print("  |  3. Once logged in, come back here and press ENTER    |")
        print("  +-------------------------------------------------------+")
        input("  [Press ENTER after you have logged in] >>> ")

        if "login" in driver.current_url:
            print("  [M2] WARNING: Still on login page. Trying public scrape anyway...")

        # ── mbasic scraping ────────────────────────────────────────────────
        current_url = f"https://mbasic.facebook.com/{PAGE_NAME}"
        page_num = 0

        while len(posts) < needed and page_num < 80:
            page_num += 1
            print(f"  [M2] Page #{page_num:>2} | Got: {len(posts)}/{needed}")

            driver.get(current_url)
            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, "html.parser")

            containers = (
                soup.find_all("div", class_="story_body_container")
                or soup.find_all("div", attrs={"data-ft": True})
                or []
            )

            for c in containers:
                raw = re.sub(r'\s+', ' ', c.get_text(" ", strip=True)).strip()

                post_url = current_url
                for a in c.find_all("a", href=True):
                    h = a["href"]
                    if any(x in h for x in ["/story.php", "/posts/", "/permalink/", "fbid="]):
                        h = re.sub(r'^https?://mbasic\.facebook\.com',
                                   'https://www.facebook.com', h)
                        if h.startswith("/"):
                            h = "https://www.facebook.com" + h
                        post_url = h.split("?")[0]
                        break

                if not raw or raw in seen or len(raw) < 20:
                    continue
                seen.add(raw)

                cat = classify(raw)
                posts.append({
                    "date"    : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "text"    : raw[:3000],
                    "url"     : post_url,
                    "category": cat,
                })
                marker = "[CRIME]" if cat == "crime-related" else "[OK]"
                print(f"    [{len(posts):>3}/{needed}] {marker} {raw[:90]}...")

                if len(posts) >= needed:
                    break

            # ── Next page ──────────────────────────────────────────────────
            next_url = None
            for a in soup.find_all("a", href=True):
                href = a["href"]
                txt  = a.get_text(strip=True).lower()
                if (txt in ("see more stories", "see more", "next", "more posts") or
                        ("timeline" in href and "after=" in href) or
                        ("cursor=" in href and PAGE_NAME.lower() in href.lower())):
                    next_url = ("https://mbasic.facebook.com" + href
                                if href.startswith("/") else href)
                    break

            if not next_url:
                print("  [M2] No next page found. Done.")
                break

            current_url = next_url
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n  [M2] Interrupted by user.")
    finally:
        driver.quit()

    return posts


# ============================================================
#  SAVE CSV
# ============================================================
def save_csv(posts: list) -> str:
    df = pd.DataFrame(posts)
    cols = [c for c in ["date", "text", "url", "category"] if c in df.columns]
    df = df[cols]
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"munasar_{ts}.csv")
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


# ============================================================
#  MAIN
# ============================================================
def main():
    print()
    print("=" * 57)
    print("  Facebook Scraper  --  MunasarMohamedAbd")
    print(f"  Target : {TARGET_ROWS} posts")
    print(f"  Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 57)
    print()

    all_posts = []

    # ── Method 1: facebook-scraper ────────────────────────────
    print("[METHOD 1]  facebook-scraper library")
    cookies = load_cookies()
    if cookies:
        print(f"  Cookies found: {COOKIES_FILE}  ({len(cookies)} entries)")
    else:
        print(f"  No cookies file found ({COOKIES_FILE})")
        print("  Will try public scraping (may get fewer posts).")

    m1 = method_facebook_scraper(cookies)
    all_posts.extend(m1)
    print(f"  => Method 1 collected: {len(m1)} posts")

    # ── Method 2: Selenium fallback ───────────────────────────
    if len(all_posts) < TARGET_ROWS:
        still_needed = TARGET_ROWS - len(all_posts)
        print()
        print(f"[METHOD 2]  Selenium manual login")
        print(f"  Still need {still_needed} more posts.")
        ans = input("  Open browser to log in manually? (y/n) >>> ").strip().lower()
        if ans == "y":
            m2_raw = method_selenium(needed=still_needed + 30)
            existing = {p["text"][:80] for p in all_posts}
            m2_new   = [p for p in m2_raw if p["text"][:80] not in existing]
            all_posts.extend(m2_new)
            print(f"  => Method 2 added: {len(m2_new)} new posts")

    # ── Summary ───────────────────────────────────────────────
    print()
    print("=" * 57)
    print(f"  TOTAL POSTS  : {len(all_posts)}")
    print("=" * 57)

    if all_posts:
        crime     = sum(1 for p in all_posts if p["category"] == "crime-related")
        not_crime = len(all_posts) - crime
        print(f"  crime-related     : {crime}")
        print(f"  not crime-related : {not_crime}")

        path = save_csv(all_posts)
        print(f"\n  CSV saved  =>  {path}")

        print("\n  Preview (first 5 posts):")
        for i, p in enumerate(all_posts[:5], 1):
            marker = "[CRIME]" if p["category"] == "crime-related" else "[OK]   "
            print(f"\n  [{i}] {marker} Category: {p['category']}")
            print(f"       Text : {p['text'][:120]}...")
            print(f"       URL  : {p['url']}")
    else:
        print()
        print("  No posts found.")
        print()
        print("  SOLUTION:")
        print("  ---------")
        print("  1. Create 'fb_cookies.json':")
        print("     a) Chrome > facebook.com > log in")
        print("     b) Install 'Cookie-Editor' Chrome extension")
        print("     c) Click extension > Export > 'Export as JSON'")
        print(f"     d) Save as: {COOKIES_FILE}")
        print("     e) Run script again")
        print()
        print("  2. OR:  run script again and choose 'y' for Selenium")

    print()


if __name__ == "__main__":
    main()
