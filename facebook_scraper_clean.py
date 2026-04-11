import os
import sys
import time
import json
import re
from datetime import datetime
import pandas as pd

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"Error: Fadlan install garee dependencies-ka: {e}")
    print("Run: pip install selenium webdriver-manager beautifulsoup4 pandas")
    sys.exit()

# Setup encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ============================================================
#  SETTINGS (Halkan ka bedel Settings-ka)
# ============================================================
TARGET_URL = "https://www.facebook.com/MunasarMohamedAbd" 
TARGET_POSTS = 50  # Inteeda post inaad soo qaadato rabtaa
COOKIES_FILE = "fb_cookies.json" # Faylka loginka (hadii uu jiro)

# ============================================================
#  NOISE FILTER (Waxyaabaha aan muhiimka ahayn ee laga reebayo)
# ============================================================
def is_junk_text(text):
    """
    Function-kan wuxuu hubinayaa in qoraalka uu yahay mid aan muhiim ahayn
    sida menu-yada facebook, likes, comments, iwm.
    """
    text = text.strip()
    
    # Haddii qoraalka aad u gaabanyahay
    if len(text) < 15:
        return True
        
    lower_text = text.lower()
    
    # Ereyada baraha bulshada caadiga u ah
    junk_patterns = [
        r"^like\b", r"\d+\s*likes?\b", 
        r"^comment\b", r"\d+\s*comments?\b",
        r"^share\b", r"\d+\s*shares?\b",
        r"^see more$", r"^see translation$",
        r"^write a comment\.\.\.$",
        r"^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$",
        r"^\d+\s*(h|m|d)\b" # 5 h, 2 m, 1 d
    ]
    
    for pattern in junk_patterns:
        if re.match(pattern, lower_text):
            return True
            
    # Haddii qoraalku u badan yahay links kaliya
    words = text.split()
    if all(w.startswith('http') or w.startswith('#') or w.startswith('@') for w in words):
        return True
        
    return False

def clean_post_text(text):
    """Nadiifi qoraalka saxda ah, ka saar space-ka badan"""
    # Badel "See more" iyo waxyaabaha la midka ah
    text = re.sub(r'See more\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'See translation\s*', '', text, flags=re.IGNORECASE)
    # Nadiifi space-ka iyo newlines-ka xad-dhaafka ah
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

# ============================================================
#  CRIME CATEGORY (Soomaali)
# ============================================================
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

# ============================================================
#  SCRAPER LOGIC
# ============================================================
def setup_driver():
    opts = Options()
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    
    print("🌐 Furayaa browser-ka...")
    svc = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=svc, options=opts)
    driver.set_window_size(1280, 900)
    return driver

def inject_cookies(driver):
    if os.path.exists(COOKIES_FILE):
        print("🍪 Akhrinayaa cookies-ka si loginka loo dhaafo...")
        driver.get("https://www.facebook.com/")
        time.sleep(2)
        try:
            with open(COOKIES_FILE, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            for cookie in cookies:
                cookie_dict = {
                    "name": cookie.get("name", ""),
                    "value": cookie.get("value", ""),
                    "domain": ".facebook.com",
                    "path": "/"
                }
                driver.add_cookie(cookie_dict)
            return True
        except Exception as e:
            print(f"⚠️ Cilad cookies-ka: {e}")
    else:
        print("⚠️ Faylka 'fb_cookies.json' lama helin. Waa inaad login ku gasho gacanta.")
    return False

def scrape_facebook():
    driver = setup_driver()
    
    # Tallaabada 1: Gali Cookies (Login)
    has_cookies = inject_cookies(driver)
    
    # Tallaabada 2: Aad Page-ka
    print(f"🚀 Tagayaa page-ka: {TARGET_URL}")
    driver.get(TARGET_URL)
    
    if not has_cookies:
        print("🛑 FADLAN: Geli email-kaaga iyo password-kaaga browser-ka")
        input("👉 Markaad login dhameeyso, riix ENTER halkan...")
        driver.get(TARGET_URL) # Dib u rari

    time.sleep(5)
    
    posts_data = []
    seen_texts = set()
    no_new_posts_count = 0
    scroll_attempts = 0
    
    print("\n⏳ Bilaabayaa inaan aruuriyo qoraalada (Scraping)...")
    
    try:
        while len(posts_data) < TARGET_POSTS and no_new_posts_count < 10:
            # Fur dhammaan 'See more' (Sii aqri) si qoraalka oo dhan u soo baxo
            try:
                see_more_btns = driver.find_elements(By.XPATH, "//div[@role='button' and (contains(., 'See more') or contains(., 'See More'))]")
                for btn in see_more_btns:
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                    except:
                        pass
                time.sleep(0.5)
            except:
                pass
                
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Raadi qaybaha qoraalada
            fb_posts = soup.find_all("div", attrs={"data-ad-preview": "message"})
            if not fb_posts:
                # Fallback u samee container kale oo qoraal yeelan kara
                fb_posts = soup.find_all("div", dir="auto")
                
            new_found = 0
            
            for post in fb_posts:
                raw_text = post.get_text(" ", strip=True)
                cleaned_text = clean_post_text(raw_text)
                
                # Ka saar waxyaabaha aan muhiimka ahayn (Noise filtering)
                if is_junk_text(cleaned_text):
                    continue
                    
                # Halkan waxaa lagu hubinayaa inay CRIME tahay
                cat = classify(cleaned_text)
                if cat != "crime-related":
                    continue
                    
                # Ka fiiri in qoraalkan horey loo qaatay
                text_signature = cleaned_text[:100].lower()
                if text_signature in seen_texts:
                    continue
                    
                seen_texts.add(text_signature)
                
                # Qoraalka waa diyaar, keydi
                posts_data.append({
                    "date_scraped": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "text": cleaned_text,
                    "url": driver.current_url
                })
                
                new_found += 1
                print(f"✅ [{len(posts_data)}/{TARGET_POSTS}] Helay: {cleaned_text[:60]}...")
                
                if len(posts_data) >= TARGET_POSTS:
                    break
                    
            if new_found == 0:
                no_new_posts_count += 1
            else:
                no_new_posts_count = 0
                
            # Scroll samee si post-yo cusub usoo baxaan
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(3)
            scroll_attempts += 1
            
            if scroll_attempts > 50:
                print("⚠️ Scroll aad u badan ayaa dhacay, malaha boggu wuu dhamaaday.")
                break

    except KeyboardInterrupt:
        print("\n🛑 Joojin Gacanta ah (Interrupted)")
    finally:
        print("\nDhameeyay scraping! Xidhayaa browser-ka...")
        driver.quit()
        
    return posts_data

def save_data(data):
    if not data:
        print("❌ Ma jiro wax xog ah oo la helay.")
        return
        
    df = pd.DataFrame(data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"facebook_crime_posts_{timestamp}.csv"
    
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"\n🎉 WAA LAGU GUULEYSTAY! Xogta waxaa la dhigay: {filename}")
    print(f"Wadar ahaan: {len(data)} posts oo dambi (crime) ah ayaa la helay.")

if __name__ == "__main__":
    extracted_data = scrape_facebook()
    save_data(extracted_data)
