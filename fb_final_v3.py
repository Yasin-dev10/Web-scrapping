# -*- coding: utf-8 -*-
"""
fb_final_v3.py
==============
Facebook Page Scraper - MunasarMohamedAbd
Based on the working v2 approach that extracted 72 posts,
with improved junk filtering, proper post URL extraction,
and human-like scrolling for more posts.
"""
import os, sys, json, time, re
import pandas as pd
from datetime import datetime
import random

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ─── Settings ─────────────────────────────────────────────────────────────────
PAGE_NAME    = "MunasarMohamedAbd"
TARGET_ROWS  = 200
COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb_cookies.json")
OUTPUT_DIR   = os.path.dirname(os.path.abspath(__file__))
PAGE_URL     = f"https://www.facebook.com/{PAGE_NAME}"

CRIME_KEYWORDS = [
    "dil","dilka","dilaan","dilay","la dilay","la dili","dilmay","la laayay",
    "xasuuq","xasuuqa","xasuuqay",
    "rasaas","ridmad","xabbad","madaafiic",
    "dhaawac","dhaawacay","dhaawacmay",
    "xabsi","xabasheet","xidhay","la xidhay",
    "kufsi","kufsaday","xad-guduub",
    "boob","boobo","tuugnimo","xaday","tuug",
    "qarax","bomba","qaraxay","gantaal",
    "colaad","dagaal","dagaalka","rabshad","rabshadaha",
    "argagax","argagixiso","gacan-ku-haynta",
    "hanjabaad","hanjabay",
    "maxkamad","garsoor","dacwad","dembi","xukun",
    "booliska","ciidanka","la qabtay",
    "hub","qori","hubka",
    "weerar","la weeraray","in la laayo",
    "gef","xaloofo","basaas",
    "nafta","baqdin","cabsi",
    "duullaan","xarig","dilac",
    "la toogtay","la garaacay",
    "askari","gaashaanle","ciidamada",
    "murder","killed","killing","dead","shooting","shot",
    "crime","criminal","suspect","convicted",
    "arrested","arrest","detained","jailed",
    "attack","attacked","violence","robbery","robbed",
    "theft","stolen","rape","bomb","explosion","blast",
    "terror","terrorist","weapon","knife","stabbing",
    "assault","clash","clashes","riot","kidnap","kidnapping",
    "hostage","prison","jail","court","verdict",
    "police","troops","military","forces","war","conflict",
    "casualty","wounded","injured","execution","threat","massacre",
    "قتل","مقتل","جريمة","سرقة","اعتقال","عنف",
    "انفجار","ارهاب","اغتصاب","اعتداء","شرطة",
    "ضحايا","جرح","اطلاق نار","حرب","معركة",
    "جيش","قوات","تهديد","احتجاز","اختطاف",
]

def classify(text):
    t = (text or "").lower()
    for kw in CRIME_KEYWORDS:
        if kw.lower() in t:
            return "crime-related"
    return "not crime-related"

def is_junk(text):
    """Return True only for obvious junk."""
    if not text:
        return True
    words = text.split()
    # Space-separated single characters: 'd o o r n e s p S ...'
    if len(words) >= 8 and all(len(w) <= 2 for w in words[:8]):
        return True
    # Single long word/token with no spaces
    if len(words) == 1 and len(text) > 40:
        return True
    return False

def build_driver():
    opts = Options()
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    svc = Service(ChromeDriverManager().install())
    drv = webdriver.Chrome(service=svc, options=opts)
    drv.execute_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
    )
    drv.set_window_size(1280, 900)
    return drv

def inject_cookies(driver, cookies):
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
    print(f"  Injected {len(cookies)} cookies")

def get_post_url(art):
    """Try to find an actual post permalink inside an article element."""
    for a in art.find_all("a", href=True):
        h = a["href"]
        if any(x in h for x in ["/posts/", "/permalink/", "story_fbid=", "fbid="]):
            if not h.startswith("http"):
                h = "https://www.facebook.com" + h
            return h.split("?")[0]
    return PAGE_URL

def extract_all(soup, seen):
    """
    Two-pass extraction:
    Pass 1: role='article' elements (cleaner, with URL)
    Pass 2: dir='auto' div/span elements (catches what articles miss)
    """
    results = []

    # ── Pass 1: articles ──────────────────────────────────────────────────────
    for art in soup.find_all(attrs={"role": "article"}):
        post_url = get_post_url(art)
        raw = re.sub(r"\s+", " ", art.get_text(" ", strip=True)).strip()
        if not raw or len(raw) < 30 or is_junk(raw):
            continue
        key = raw[:200]
        if key in seen:
            continue
        seen.add(key)
        # NO character limit — store full text
        results.append({"text": raw, "url": post_url, "category": classify(raw)})

    # ── Pass 2: dir=auto fallback ─────────────────────────────────────────────
    for el in soup.find_all(["div", "span"], attrs={"dir": "auto"}):
        raw = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
        if not raw or len(raw) < 40 or is_junk(raw):
            continue
        key = raw[:200]
        if key in seen:
            continue
        seen.add(key)
        # NO character limit
        results.append({"text": raw, "url": PAGE_URL, "category": classify(raw)})

    return results


def human_scroll(driver):
    """Simulate a slower human-like scroll in several increments."""
    total_h = driver.execute_script("return document.body.scrollHeight")
    current = driver.execute_script("return window.pageYOffset")
    step    = random.randint(400, 700)
    while current < total_h:
        current += step
        driver.execute_script(f"window.scrollTo(0, {current});")
        time.sleep(random.uniform(0.3, 0.7))
    # Then wait for lazy content to load
    time.sleep(random.uniform(3, 5))

def click_see_more(driver):
    """
    Expand ALL truncated posts by clicking every 'See more' button visible
    on the current page. Called before extracting text each scroll.
    """
    # XPath selectors covering different Facebook 'See more' button types
    xpaths = [
        # Standard span-based 'See more'
        "//div[@role='article']//div[@role='button' and contains(.,'See more')]",
        "//div[@role='article']//span[@role='button' and contains(.,'See more')]",
        # Sometimes it's just a plain span with the text
        "//div[@role='article']//span[text()='See more']",
        "//div[@role='article']//span[text()='See More']",
        # For Somali / Arabic versions (fallback)
        "//div[@role='article']//span[contains(.,'…')]",
    ]
    clicked = 0
    for xp in xpaths:
        try:
            btns = driver.find_elements(By.XPATH, xp)
            for btn in btns:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    time.sleep(0.3)
                    driver.execute_script("arguments[0].click();", btn)
                    clicked += 1
                    time.sleep(0.4)
                except Exception:
                    pass
        except Exception:
            pass
    if clicked:
        print(f"    [see-more] Expanded {clicked} truncated posts")
        time.sleep(1)  # wait for DOM to update


def scrape(driver):
    posts = []
    seen  = set()

    print(f"  Opening: {PAGE_URL}")
    driver.get(PAGE_URL)
    time.sleep(6)

    cur = driver.current_url
    print(f"  Current URL: {cur}")

    if "login" in cur:
        print("\n  +--------------------------------------------------+")
        print("  |  LOG IN TO FACEBOOK IN THE BROWSER NOW          |")
        print("  |  Then press ENTER here to continue              |")
        print("  +--------------------------------------------------+")
        input("  [ENTER] >>> ")
        driver.get(PAGE_URL)
        time.sleep(6)

    no_new     = 0
    MAX_NO_NEW = 10
    scroll_n   = 0

    while len(posts) < TARGET_ROWS and no_new < MAX_NO_NEW:
        scroll_n += 1

        # ── Expand all 'See more' buttons before parsing ──────────────────────
        click_see_more(driver)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        new  = extract_all(soup, seen)

        count_before = len(posts)
        for p in new:
            posts.append(p)
            m = "[CRIME]" if p["category"] == "crime-related" else "[OK]"
            print(f"  [{len(posts):>3}/{TARGET_ROWS}] {m} {p['text'][:90]}")
            if len(posts) >= TARGET_ROWS:
                break

        gained = len(posts) - count_before
        if gained == 0:
            no_new += 1
            print(f"  [s{scroll_n}] No new ({no_new}/{MAX_NO_NEW}). Total: {len(posts)}")
        else:
            no_new = 0
            print(f"  [s{scroll_n}] +{gained}. Total: {len(posts)}")

        if len(posts) >= TARGET_ROWS:
            break

        # Human-like scroll
        human_scroll(driver)

    return posts

def save_csv(posts):
    df   = pd.DataFrame(posts, columns=["text", "url", "category"])
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"munasar_{ts}.csv")
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path

def main():
    print()
    print("=" * 60)
    print("  Facebook Scraper v3 -- MunasarMohamedAbd")
    print(f"  Target : {TARGET_ROWS} posts")
    print(f"  Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if not os.path.exists(COOKIES_FILE):
        print(f"\n  ERROR: {COOKIES_FILE} not found.")
        print("  Run:  python -X utf8 get_cookies.py  first")
        return

    with open(COOKIES_FILE, encoding="utf-8") as f:
        cookies = json.load(f)
    print(f"  Cookies: {len(cookies)} loaded")

    driver = build_driver()
    posts  = []

    try:
        inject_cookies(driver, cookies)
        posts = scrape(driver)
    except KeyboardInterrupt:
        print("\n  Interrupted by user.")
    finally:
        driver.quit()

    print()
    print("=" * 60)
    print(f"  TOTAL POSTS : {len(posts)}")
    print("=" * 60)

    if posts:
        crime     = sum(1 for p in posts if p["category"] == "crime-related")
        not_crime = len(posts) - crime
        print(f"  crime-related     : {crime}")
        print(f"  not crime-related : {not_crime}")

        path = save_csv(posts)
        print(f"\n  Saved CSV: {path}")
        print(f"\n  Preview (first 5 posts):")
        for i, p in enumerate(posts[:5], 1):
            m = "[CRIME]" if p["category"] == "crime-related" else "[OK]"
            print(f"\n  [{i}] {m}")
            print(f"       {p['text'][:130]}")
            print(f"       URL: {p['url']}")
    else:
        print("\n  No posts collected.")
        print("  Cookies may be expired. Run get_cookies.py to refresh them.")

if __name__ == "__main__":
    main()
