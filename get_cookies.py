# -*- coding: utf-8 -*-
"""
get_cookies.py
==============
1. Browser-ka Chrome ayaa furmi doona
2. Facebook-ka ku gal (login samee)
3. ENTER riix — cookies-kaaga ayaa toos loogu keydinayaa fb_cookies.json
4. Kadibna:  python -X utf8 fb_scraper_final.py   socodsii
"""

import os, sys, json, time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb_cookies.json")

def main():
    print()
    print("=" * 55)
    print("  Facebook Cookie Saver")
    print("=" * 55)

    opts = Options()
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

    driver.get("https://www.facebook.com/login")
    time.sleep(2)

    print()
    print("  +--------------------------------------------------+")
    print("  |  BROWSER WAA FURAN YAHAY                        |")
    print("  |  1. Email + Password-kaaga Facebook geli        |")
    print("  |  2. Login xaqiiji (2FA haddii jirto)            |")
    print("  |  3. News Feed la arko kadib, halkan soo laabo   |")
    print("  +--------------------------------------------------+")
    input("  [ENTER riix marka login dhammaato] >>> ")

    # Check login
    if "facebook.com" in driver.current_url and "login" not in driver.current_url:
        print("  Login: SUCCESS")
    else:
        print("  Login: still on login page, saving cookies anyway...")

    # Save cookies
    raw_cookies = driver.get_cookies()
    driver.quit()

    # Convert to Cookie-Editor JSON format
    cookie_list = []
    for c in raw_cookies:
        cookie_list.append({
            "name"    : c.get("name", ""),
            "value"   : c.get("value", ""),
            "domain"  : c.get("domain", ".facebook.com"),
            "path"    : c.get("path", "/"),
            "secure"  : c.get("secure", False),
            "httpOnly": c.get("httpOnly", False),
            "sameSite": c.get("sameSite", "None"),
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cookie_list, f, ensure_ascii=False, indent=2)

    print()
    print(f"  Cookies saved: {OUTPUT_FILE}")
    print(f"  Total cookies: {len(cookie_list)}")
    print()
    print("  Hadda scraper-ka socodsii:")
    print("  python -X utf8 fb_scraper_final.py")
    print()

if __name__ == "__main__":
    main()
