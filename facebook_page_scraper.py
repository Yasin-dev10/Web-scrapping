"""
Facebook Page Scraper - MunasarMohamedAbd
==========================================
Script-kani wuxuu ka soo qaadaa posts-ka Facebook page-ka MunasarMohamedAbd,
wuxuuna u kala soocaa:
  - crime-related     : posts xiriira dambiga
  - not crime-related : posts aan xiriirin dambiga

Natiijooyinka waxaa lagu kaydiyaa CSV file.

ISTICMAALKA:
  1. Script-ka fur oo aad browser-ka Chrome ee furmaya
  2. Geli email-kaaga Facebook iyo password-kaaga
  3. Kadib login, script-ka aad ayuu u socon doonaa oo posts shaqeeyaa

"""

import time
import re
import os
import sys
import pandas as pd
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ============================================================
#  XOGTA LOGIN-KA  (kaga buuxi email-kaaga iyo password-kaaga)
# ============================================================
FB_EMAIL    = ""   # <-- Geli email-kaaga Facebook halkan, tusale: "ciidanka@example.com"
FB_PASSWORD = ""   # <-- Geli password-kaaga Facebook halkan

# ============================================================
#  DEJINTA GUUD
# ============================================================
TARGET_PAGE   = "https://www.facebook.com/MunasarMohamedAbd"
MOBILE_PAGE   = "https://mbasic.facebook.com/MunasarMohamedAbd"
MAX_SCROLLS   = 20      # Posts badan oo la helaayo
SCROLL_PAUSE  = 3       # Ilbiriqsi

# ============================================================
#  CRIME KEYWORDS  (Somali + Arabic + English)
# ============================================================
CRIME_KEYWORDS = [
    # --- Somali ---
    "dil","dilka","dilaan","dilay","la dilay","la dili","dilmay",
    "xasuuq","xasuuqa",
    "rasaas","ridmad","ridmo","madaafic","xabbad",
    "dhaawac","dhaawacay","dhaawacmay","dhaawaco",
    "xabsi","xabasheet","xidhiidhiyay","xidhay","la xidhi",
    "kufsi","kasoo xadday","xad-guduub","kufsaday",
    "boob","boobo","boobka","tuugnimo","xaday","tuug",
    "qarax","qarax dhacay","bomba","bomb","qaraxay",
    "colaad","colaada","dagaal","dagaalka","rabshad","rabshadaha",
    "rabsho","mucaarad","xukun",
    "argagax","argagixiso","gacan-ku-haynta","argagixisad",
    "hanjabaad","hanjabaadka","hanjabay","hanjabaadda",
    "maxkamad","garsoor","dacwad","dembi","dembiga",
    "booliska","ciidanka","la qabtay","la xidhay",
    "qabashada","la qabsaday","la dhibaatootiyay",
    "hub","qori","hubka","hubeysi",
    "in la laayo","la weeraray","weerar","weerar",
    "gef","gefka","xaloofo","basaas","basaasta",
    "gaadiidka laga xaday","lacag laga xaday",
    "qashinka","cadaadis","dhibaato","xaaladda",
    "cabsi","baqdin","baqday",
    "gaashaanle","askari",
    "duullaan","duullaanka","xarig","xarigga",
    "dilac","madaxweyne","maamul","khilaaf",
    "badbaado","badbaadin","nafta",
    "guuran","gumaad","dhaqdhaqaaq",
    "beerta","xoogga","ciidamada",
    # --- English ---
    "murder","killed","killing","dead","death",
    "shooting","shot","gunfire","gunman",
    "crime","criminal","criminality",
    "arrested","arrest","detained","detention",
    "attack","attacked","attacker","violence",
    "robbery","robbed","theft","stolen","steal",
    "rape","sexual assault",
    "bomb","explosion","blast","terror","terrorist","terrorism",
    "weapon","gun","knife","stabbing","stabbed",
    "assault","fight","fighting","clash","clashes",
    "police","court","prison","jail","suspect","verdict",
    "hostage","kidnap","kidnapping","abduction",
    "riot","unrest","protest","demonstration",
    "war","conflict","military","troops","forces",
    "threat","threatened","warning",
    "casualty","casualties","wounded","injury","injured",
    "execution","executed",
    # --- Arabic ---
    "قتل","جريمة","سرقة","اعتقال","عنف",
    "انفجار","ارهاب","اغتصاب","اعتداء","شرطة",
    "مقتل","ضحايا","جرح","اطلاق نار","حرب",
    "جيش","قوات","تهديد","احتجاز","اختطاف",
]


def classify_post(text: str) -> str:
    """Post-ka u kala sooc: crime-related ama not crime-related."""
    if not text:
        return "not crime-related"
    text_lower = text.lower()
    for kw in CRIME_KEYWORDS:
        if kw.lower() in text_lower:
            return "crime-related"
    return "not crime-related"


def setup_driver():
    """Chrome driver-ka dejinta."""
    options = Options()
    # HEADLESS = False  =>  browser-ka waxad arki doontaa (login ugu fudud)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def login_facebook(driver):
    """
    Facebook-ka ku gal.
    Haddii email/password-ku madhan yihiin, waxaad gacanta ku gelisaa inta lagu sugayo.
    """
    print("\n[LOGIN] Facebook login-ka...")
    driver.get("https://www.facebook.com/login")
    time.sleep(3)

    if FB_EMAIL and FB_PASSWORD:
        # Auto-login
        try:
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_input.clear()
            email_input.send_keys(FB_EMAIL)

            pass_input = driver.find_element(By.ID, "pass")
            pass_input.clear()
            pass_input.send_keys(FB_PASSWORD)
            pass_input.send_keys(Keys.RETURN)

            print("[LOGIN] Email iyo password-ka waa la gelinay. Sugaya...")
            time.sleep(6)

            if "checkpoint" in driver.current_url:
                print("[LOGIN] ⚠️  Xaqiijinta 2-tallaaboodka ama checkpoint ayaa muuqday.")
                print("       Gacanta ku xaqiiji browser-ka, kadibna Enter ku dhufo halkan.")
                input("       [Press ENTER marka aad browser-ka ku dhameyso login...] ")
            elif "login" in driver.current_url:
                print("[LOGIN] ⚠️  Login ma shaqeyn. Fadlan browser-ka gacanta ku gal.")
                input("       [Press ENTER marka aad browser-ka ku dhameyso login...] ")
        except Exception as e:
            print(f"[LOGIN] Khalad: {e}")
            print("[LOGIN] Fadlan gacanta ku gal browser-ka.")
            input("       [Press ENTER marka aad browser-ka ku dhameyso login...] ")
    else:
        # Manual login - isticmaalaha ayaa gacanta galaya
        print("[LOGIN] ════════════════════════════════════════")
        print("[LOGIN]  FADLAN GACANTA KU GAL FACEBOOK!")
        print("[LOGIN]  Browser-ka ayaa furan yahay.")
        print("[LOGIN]  1. Email iyo password-kaaga geli")
        print("[LOGIN]  2. Login-ka xaqiiji (2FA haddii jirto)")
        print("[LOGIN]  3. Marka aad galeen, terminal-kan ku soo laabo")
        print("[LOGIN] ════════════════════════════════════════")
        input("       [Press ENTER marka aad browser-ka ku dhameyso login...] ")

    print(f"[LOGIN] URL hadda: {driver.current_url[:60]}")
    if "facebook.com" in driver.current_url and "login" not in driver.current_url:
        print("[LOGIN] ✅ Login waa lagu guuleystay!")
        return True
    else:
        print("[LOGIN] ⚠️  Login wali ma dhamin. Waxaan isku dayi doonaa scraping-ka...")
        return False


def scrape_posts_mbasic(driver) -> list[dict]:
    """
    mbasic.facebook.com - HTML fudud ayaa la isticmaalaa.
    """
    posts_data = []
    seen_texts = set()

    # mbasic-ka u gudub
    mbasic_url = f"https://mbasic.facebook.com/MunasarMohamedAbd"
    print(f"\n[mbasic] Furaya: {mbasic_url}")
    driver.get(mbasic_url)
    time.sleep(4)

    current_url = mbasic_url
    page_num = 0

    while page_num < MAX_SCROLLS:
        page_num += 1
        print(f"  [mbasic] Bog #{page_num} la baarayo... ({len(posts_data)} posts ilaa hadda)")

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # ---- Posts raadi ----
        # mbasic Facebook: posts waxay ku jiraan divs oo leh data-ft attribute
        story_bodies = soup.find_all("div", class_="story_body_container")
        if not story_bodies:
            story_bodies = soup.find_all("div", attrs={"data-ft": True})
        if not story_bodies:
            # Fallback: wax kasta oo text ah > 50 chars
            story_bodies = [div for div in soup.find_all("div")
                            if div.get_text(strip=True) and len(div.get_text(strip=True)) > 50
                            and div.parent and not div.find("div")]

        for story in story_bodies:
            raw_text = story.get_text(separator=" ", strip=True)
            raw_text = re.sub(r'\s+', ' ', raw_text).strip()

            # URL
            post_url = ""
            for a in story.find_all("a", href=True):
                href = a["href"]
                if any(x in href for x in ["/story.php", "/posts/", "/permalink/", "fbid="]):
                    # Clean-up mbasic URLs => www.facebook.com
                    clean = re.sub(r'^https?://mbasic\.facebook\.com', 'https://www.facebook.com', href)
                    clean = re.sub(r'^/', 'https://www.facebook.com/', clean)
                    clean = clean.split("?")[0]
                    post_url = clean
                    break

            if not raw_text or raw_text in seen_texts or len(raw_text) < 30:
                continue

            seen_texts.add(raw_text)
            category = classify_post(raw_text)
            posts_data.append({
                "text": raw_text[:3000],
                "url": post_url if post_url else current_url,
                "category": category,
            })
            icon = "🔴" if category == "crime-related" else "🟢"
            print(f"    {icon} Post #{len(posts_data)}: [{category}] {raw_text[:90]}...")

        # ---- Bogga xiga raadi ----
        next_link = None

        # "See More Stories" ama "Next" button
        for a in soup.find_all("a", href=True):
            link_text = a.get_text(strip=True).lower()
            href = a["href"]
            if link_text in ["see more", "next", "more posts", "view more"] \
               or ("cursor=" in href and "MunasarMohamedAbd" in href) \
               or ("timeline" in href.lower() and "after=" in href.lower()):
                next_link = href
                break

        if not next_link:
            print(f"  [mbasic] Bogga xiga lama helin. Dhammaatay.")
            break

        # URL full-ka samee
        if next_link.startswith("/"):
            current_url = "https://mbasic.facebook.com" + next_link
        elif next_link.startswith("http"):
            current_url = next_link
        else:
            current_url = "https://mbasic.facebook.com/" + next_link.lstrip("/")

        print(f"  [mbasic] Bogga xiga: {current_url[:100]}")
        driver.get(current_url)
        time.sleep(SCROLL_PAUSE)

    return posts_data


def scrape_posts_main_fb(driver) -> list[dict]:
    """
    Main Facebook - Selenium scroll approach.
    """
    posts_data = []
    seen_texts = set()

    print(f"\n[main FB] Furaya: {TARGET_PAGE}")
    driver.get(TARGET_PAGE)
    time.sleep(5)

    last_height = driver.execute_script("return document.body.scrollHeight")

    for scroll_i in range(1, MAX_SCROLLS + 1):
        print(f"  [main FB] Scroll #{scroll_i}/{MAX_SCROLLS}... ({len(posts_data)} posts)")

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Post containers
        containers = soup.find_all("div", attrs={"role": "article"})

        for c in containers:
            raw_text = c.get_text(separator=" ", strip=True)
            raw_text = re.sub(r'\s+', ' ', raw_text).strip()

            # URL
            post_url = TARGET_PAGE
            for a in c.find_all("a", href=True):
                href = a["href"]
                if any(x in href for x in ["/posts/", "/permalink/", "/story.php", "fbid="]):
                    clean = href.split("?")[0]
                    if not clean.startswith("http"):
                        clean = "https://www.facebook.com" + clean
                    post_url = clean
                    break

            if not raw_text or raw_text in seen_texts or len(raw_text) < 30:
                continue

            seen_texts.add(raw_text)
            category = classify_post(raw_text)
            posts_data.append({
                "text": raw_text[:3000],
                "url": post_url,
                "category": category,
            })
            icon = "🔴" if category == "crime-related" else "🟢"
            print(f"    {icon} Post #{len(posts_data)}: [{category}] {raw_text[:90]}...")

        # Scroll
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print(f"  [main FB] Xaddiga bog-ka laga gaay (scroll #{scroll_i}).")
            break
        last_height = new_height

    return posts_data


def save_csv(posts: list[dict]) -> str:
    """Natiijada u keydi CSV file."""
    df = pd.DataFrame(posts, columns=["text", "url", "category"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"munasar_posts_{timestamp}.csv"
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    df.to_csv(full_path, index=False, encoding="utf-8-sig")
    return full_path


def main():
    print("=" * 60)
    print("  Facebook Page Scraper - MunasarMohamedAbd")
    print("=" * 60)
    print(f"  Target  : {TARGET_PAGE}")
    print(f"  Scrolls : {MAX_SCROLLS}")
    print(f"  Waqtiga : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ---- Driver ----
    driver = setup_driver()

    all_posts = []

    try:
        # 1. Login
        login_facebook(driver)

        # 2. Scrape: mbasic (waa fudud)
        print("\n[STEP 1] mbasic.facebook.com...")
        mbasic_posts = scrape_posts_mbasic(driver)
        all_posts.extend(mbasic_posts)
        print(f"  → mbasic: {len(mbasic_posts)} posts ayaa la helay.")

        # 3. Haddii yar, main FB ku xooji
        if len(all_posts) < 10:
            print("\n[STEP 2] Main facebook.com (scroll)...")
            main_posts = scrape_posts_main_fb(driver)
            existing = {p["text"][:80] for p in all_posts}
            new_ones = [p for p in main_posts if p["text"][:80] not in existing]
            all_posts.extend(new_ones)
            print(f"  → main FB: {len(new_ones)} posts cusub ayaa la helay.")

    except KeyboardInterrupt:
        print("\n[INFO] Isticmaalaha ayaa joojiyay (Ctrl+C).")
    finally:
        driver.quit()

    # ---- Natiijada ----
    print("\n" + "=" * 60)
    print(f"  WADARTA GUUD: {len(all_posts)} posts")
    print("=" * 60)

    if all_posts:
        crime_count     = sum(1 for p in all_posts if p["category"] == "crime-related")
        not_crime_count = len(all_posts) - crime_count
        print(f"  🔴 crime-related     : {crime_count}")
        print(f"  🟢 not crime-related : {not_crime_count}")

        csv_path = save_csv(all_posts)
        print(f"\n  ✅ CSV file: {csv_path}")

        print("\n  Hore u fiiri (first 5):")
        for i, p in enumerate(all_posts[:5], 1):
            icon = "🔴" if p["category"] == "crime-related" else "🟢"
            print(f"  [{i}] {icon} [{p['category']}]")
            print(f"       Text: {p['text'][:100]}...")
            print(f"       URL : {p['url']}")
            print()
    else:
        print("  ⚠️  Wax posts ah lama helin.")
        print()
        print("  SABABO SUURTOGALKA AH:")
        print("  1. Login lama samayn — Username/password geli script-ka")
        print("  2. Page-ka private ayuu yahay")
        print("  3. Facebook selenium-ka ku ogaaday — ku sug daqiiqad oo mar kale isku day")


if __name__ == "__main__":
    main()
