# -*- coding: utf-8 -*-
"""
app.py — All-In-One Scraper Dashboard (Streamlit)
===================================================
Run:  streamlit run app.py

Wuxuu isticmaalaa shared_db.py (SQLite) si uu xogta uga soo qaato
unified_scraper.db — isku faylka barnaamijyada kale ee GUI-ga oo dhan.
"""
import streamlit as st
import pandas as pd
import os
import re
import time
import sqlite3
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import shared_db

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="All-In-One Scraper Dashboard",
    page_icon="🗄️",
    layout="wide"
)

# ── Crime classifier (same as GUI tools) ─────────────────────────────────────
CRIME_HIGH = [
    "dilka","dilaan","xasuuq","kufsi","kufsaday","qarax","qaraxay","is-miidaamin",
    "toogtay","la toogtay","xasuuqay","la dilay","gantaal","madaafiic","afduub",
    "la afduubay","qaraxa","qaraxyo","miino"
]
CRIME_MED = [
    "dhaawac","xabsi","la xidhay","boob","tuug","tuugnimo","colaad","dagaal",
    "weerar","la weeraray","booliska","askari","ciidanka","hubka","qori",
    "maxkamad","xukun","dacwad","dembi"
]
NEG_KW = [
    "ciyaaraha","kubadda","football","goal","guul","shirka","mashaariic",
    "horumar","shirkad","ganacsiga","dhaqaalaha","maalgashi","isboortiga",
    "hambalyo","ducada","tacsi","geeriyooday","geerida"
]

def classify(text):
    t = (text or "").lower()
    score = 0
    for kw in CRIME_HIGH:
        if re.search(rf"\b{kw}", t): score += 10
    for kw in CRIME_MED:
        if re.search(rf"\b{kw}", t): score += 5
    for kw in NEG_KW:
        if re.search(rf"\b{kw}", t): score -= 8
    return "crime-related" if score >= 10 else "not crime-related"

def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()

def is_valid_link(base, href):
    if not href or href.startswith(("javascript","#","mailto","tel")):
        return False
    full = urljoin(base, href)
    pb, pf = urlparse(base), urlparse(full)
    if pb.netloc not in pf.netloc and pf.netloc not in pb.netloc:
        return False
    skip = ["/contact","/about","/privacy","/terms","/search","/login","/tag","/author"]
    lp = pf.path.lower()
    return not any(s in lp for s in skip)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,so;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def fetch_page(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        r.encoding = r.apparent_encoding
        return r.text
    except Exception:
        return None

def scrape_url(base_url, target_count, delay, progress_cb, log_cb, stop_flag):
    """
    Recursive crawler — soo qaada maqaalada/postka oo xogta soo celi.
    progress_cb(done, total) , log_cb(msg, level)  — callbacks
    stop_flag: list[bool]  (mutable)
    returns: list of dicts {url, text, category}
    """
    visited  = set()
    pending  = [base_url]
    results  = []

    while pending and len(results) < target_count and not stop_flag[0]:
        url = pending.pop(0)
        if url in visited:
            continue
        visited.add(url)

        html = fetch_page(url)
        if not html:
            log_cb(f"⚠️ Skip (load failed): {url[:60]}", "warn")
            continue

        soup = BeautifulSoup(html, "html.parser")

        # ── Collect new links ───────────────────────────────────────────
        for a in soup.find_all("a", href=True):
            full_link = urljoin(base_url, a["href"]).split("#")[0]
            if is_valid_link(base_url, a["href"]) and full_link not in visited and full_link not in pending:
                pending.append(full_link)

        # ── Extract article text ────────────────────────────────────────
        h1    = soup.find("h1")
        title = clean(h1.get_text()) if h1 else ""
        paras = [clean(p.get_text()) for p in soup.find_all("p") if len(p.get_text().strip()) > 30]
        body  = "\n".join(paras)

        if len(body) < 80:
            continue   # page has no real content

        full_text = (title + "\n" + body).strip()
        cat       = classify(full_text)
        results.append({"url": url, "text": full_text, "category": cat})
        progress_cb(len(results), target_count)
        tag = "🚨" if cat == "crime-related" else "✅"
        log_cb(f"{tag} [{len(results)}/{target_count}] {title[:60] or url[:60]}", "ok")

        time.sleep(delay)

    return results


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/fluency/96/database.png", width=60)
st.sidebar.title("📋 Dooro Qaybta")

menu = [
    "🏠 Dashboard (Xogta Guud)",
    "🌐 Web Scraper (Scrapp Halkan)",
    "📊 Xogta Database (Data View & CSV Download)",
    "📥 CSV Soo Geli Database",
    "📝 Xog Gelin Gacanta (Manual Entry)",
    "✅ Data Validator (Hubinta Xogta)",
    "⚖️  Data Separator (Kala Saar & Balans)",
]
choice = st.sidebar.radio("", menu)

st.sidebar.markdown("---")
st.sidebar.caption(f"🗄️ DB: `{os.path.basename(shared_db.DB_PATH)}`")

try:
    _stats = shared_db.get_stats()
    st.sidebar.metric("Dhammaan Xogta", _stats["total"])
    st.sidebar.metric("Crime",          _stats["crime"])
    st.sidebar.metric("Not Crime",      _stats["not_crime"])
except Exception as _e:
    st.sidebar.warning(f"DB error: {_e}")

# ══════════════════════════════════════════════════════════════════════════════
#  1. Dashboard
# ══════════════════════════════════════════════════════════════════════════════
if choice == "🏠 Dashboard (Xogta Guud)":
    st.title("🏠 Ku Soo Dhawow — Web Scraper Dashboard")
    st.caption("Warbixinta guud ee xogta ku keydsan Database-ka (unified_scraper.db)")

    try:
        stats = shared_db.get_stats()
        col1, col2, col3 = st.columns(3)
        col1.metric("📦 Dhammaan Xogta",   stats["total"])
        col2.metric("🚨 Crime-Related",     stats["crime"])
        col3.metric("✅ Not Crime-Related", stats["not_crime"])

        st.markdown("---")
        if stats["total"] > 0:
            st.subheader("📊 Tirakoobka Category-ga")
            cat_data = pd.DataFrame({
                "Category": ["crime-related","not crime-related"],
                "Tirada":   [stats["crime"], stats["not_crime"]]
            }).set_index("Category")
            st.bar_chart(cat_data)

            if stats["sources"]:
                st.subheader("🔎 Barnaamijyada Xogta Ka Soo Timid")
                src_df = pd.DataFrame(
                    list(stats["sources"].items()),
                    columns=["Source","Tirada"]
                ).set_index("Source")
                st.bar_chart(src_df)
        else:
            st.info("ℹ️ Database-ka waa madhan yahay. Isticmaal '🌐 Web Scraper' si aad xog u hesho.")
    except Exception as e:
        st.error(f"Database cilad: {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  2. WEB SCRAPER (CUSUB — si toos ah waa kaga shaqeynayaa browser-ka)
# ══════════════════════════════════════════════════════════════════════════════
elif choice == "🌐 Web Scraper (Scrapp Halkan)":
    st.title("🌐 Web Scraper — Toos Halkan Ka Shaqee")
    st.markdown("""
    > **Waa sidee u shaqeeyso?**  Ku geli URL-ka websiteka aad rabto, 
    > barnaamijku wuxuu si toos ah u soo qaadaa maqaalada, u kala soocaa 
    > **Crime** iyo **Not Crime**, kuna keydinayaa database-ka.  
    > Selenium lagama baahno — waxay ku shaqeysaa browser-ka web-ka ah.
    """)

    st.markdown("---")

    # ── Settings ──────────────────────────────────────────────────────────────
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        url_input = st.text_input(
            "🔗 URL-ka Websiteka (News / Social)",
            value="https://www.bbc.com/somali",
            placeholder="https://rbc.so  |  https://hiiraan.com  |  https://goobjoog.com"
        )
    with col_s2:
        target_n = st.number_input("🎯 Tirada Maqaalada", min_value=1, max_value=500, value=20)

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        delay_s = st.slider("⏱️ Xilliyada u dhaxeeya (seconds)", 0.5, 5.0, 1.5, 0.5)
    with col_d2:
        save_to_db = st.checkbox("💾 Toos ugu Keydi Database-ka", value=True)

    # Quick-access URLs
    st.markdown("**⚡ Degdeg u isticmaal:**")
    quick_cols = st.columns(5)
    quick_sites = [
        ("BBC Somali",    "https://www.bbc.com/somali"),
        ("RBC",           "https://rbc.so"),
        ("Hiiraan",       "https://www.hiiraan.com"),
        ("Goobjoog",      "https://goobjoog.com"),
        ("VOA Somali",    "https://www.voasomali.com"),
    ]
    for i, (label, site_url) in enumerate(quick_sites):
        if quick_cols[i].button(label, key=f"quick_{i}"):
            st.session_state["_quick_url"] = site_url
            st.rerun()

    if "_quick_url" in st.session_state:
        url_input = st.session_state.pop("_quick_url")
        st.rerun()

    st.markdown("---")

    # ── Run ───────────────────────────────────────────────────────────────────
    run_btn  = st.button("🚀 Bilow Scraping-ga", type="primary", use_container_width=True)
    stop_ref = st.session_state.get("_stop_flag_ref", [False])

    if st.button("⏹ Jooji", use_container_width=False):
        stop_ref[0] = True
        st.session_state["_stop_flag_ref"] = stop_ref
        st.warning("Joojinta waa la codsaday...")

    if run_btn:
        if not url_input.strip().startswith("http"):
            st.error("Fadlan geli URL sax ah (waa inuu ku bilaabmaa http)")
            st.stop()

        stop_ref = [False]
        st.session_state["_stop_flag_ref"] = stop_ref

        progress_bar  = st.progress(0, text="Bilaabayaa...")
        log_container = st.container()
        log_box       = log_container.empty()
        log_lines     = []

        def _progress(done, total):
            pct = int(done / total * 100) if total else 0
            progress_bar.progress(pct, text=f"La soo qabanayaa: {done}/{total} ({pct}%)")

        def _log(msg, level="info"):
            icon = {"info":"ℹ️","ok":"✅","warn":"⚠️","err":"❌"}.get(level,"•")
            log_lines.insert(0, f"{icon} {msg}")
            log_box.code("\n".join(log_lines[:30]), language=None)

        _log(f"Bilaabayaa: {url_input}", "info")
        _log(f"Target: {target_n} maqaal | Delay: {delay_s}s", "info")

        with st.spinner("Waa la soo qabanayaa xogta..."):
            results = scrape_url(
                base_url     = url_input.strip(),
                target_count = target_n,
                delay        = delay_s,
                progress_cb  = _progress,
                log_cb       = _log,
                stop_flag    = stop_ref
            )

        progress_bar.progress(100, text=f"Dhammaatay — {len(results)} maqaal")

        if not results:
            st.warning("Wax maqaal ah lagama helin. Isku day URL kale.")
            st.stop()

        df_res = pd.DataFrame(results)
        crime_count    = (df_res["category"] == "crime-related").sum()
        nc_count       = len(df_res) - crime_count

        st.success(f"✅ **{len(results)}** maqaal ayaa la helay — 🚨 Crime: **{crime_count}** | ✅ Not Crime: **{nc_count}**")

        # ── Preview ───────────────────────────────────────────────────────
        with st.expander("📋 Muruqo (Preview)", expanded=True):
            st.dataframe(df_res[["category","url","text"]].head(20), use_container_width=True)

        # ── Save ──────────────────────────────────────────────────────────
        if save_to_db:
            try:
                src = urlparse(url_input.strip()).netloc or "WebScraper"
                shared_db.insert_many(results, source=f"WebApp-{src}")
                st.success(f"🗄️ Database-ka waxaa lagu daray **{len(results)}** xog!")
            except Exception as db_e:
                st.error(f"Database cilad: {db_e}")

        # ── Download ──────────────────────────────────────────────────────
        st.markdown("### 📥 Soo Daaji")
        dl1, dl2, dl3 = st.columns(3)
        with dl1:
            st.download_button(
                "📦 Dhammaan CSV",
                data=df_res.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                file_name="scraped_all.csv", mime="text/csv"
            )
        with dl2:
            c_only = df_res[df_res["category"]=="crime-related"]
            if not c_only.empty:
                st.download_button(
                    "🚨 Crime Kaliya",
                    data=c_only.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name="scraped_crime.csv", mime="text/csv"
                )
        with dl3:
            nc_only = df_res[df_res["category"]=="not crime-related"]
            if not nc_only.empty:
                st.download_button(
                    "✅ Not Crime Kaliya",
                    data=nc_only.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name="scraped_not_crime.csv", mime="text/csv"
                )

# ══════════════════════════════════════════════════════════════════════════════
#  3. Data View & CSV Download
# ══════════════════════════════════════════════════════════════════════════════
elif choice == "📊 Xogta Database (Data View & CSV Download)":
    st.title("📊 Xogta ku jirta Database-ka")

    try:
        stats = shared_db.get_stats()

        col_f1, col_f2, col_f3 = st.columns([2, 2, 3])
        with col_f1:
            cat_filter = st.selectbox("🔽 Sifee Category",
                ["Dhamaan","crime-related","not crime-related"])
        with col_f2:
            src_options = ["Dhamaan"] + sorted(stats["sources"].keys())
            src_filter = st.selectbox("🔽 Sifee Source", src_options)
        with col_f3:
            search_q = st.text_input("🔍 Raadi qoraalka", placeholder="Geli erey...")

        conn = sqlite3.connect(shared_db.DB_PATH)
        query = "SELECT id, url, text, category, source, scraped_at FROM posts WHERE 1=1"
        params = []
        if cat_filter != "Dhamaan":
            query += " AND category = ?"; params.append(cat_filter)
        if src_filter != "Dhamaan":
            query += " AND source = ?"; params.append(src_filter)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if search_q.strip():
            df = df[df["text"].astype(str).str.contains(search_q, case=False, na=False)]

        st.markdown(f"**La Muujinayaa:** `{len(df)}` xog")
        st.dataframe(df, use_container_width=True, height=460)

        st.markdown("---")
        st.subheader("📥 Soo Daaji CSV")
        dl1, dl2, dl3 = st.columns(3)

        with dl1:
            if not df.empty:
                st.download_button("⬇️ La Muujinayaa (Filtered)",
                    data=df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name="export_filtered.csv", mime="text/csv")

        with dl2:
            conn2 = sqlite3.connect(shared_db.DB_PATH)
            df_crime = pd.read_sql_query(
                "SELECT * FROM posts WHERE category='crime-related'", conn2)
            conn2.close()
            if not df_crime.empty:
                st.download_button("🚨 Crime Kaliya",
                    data=df_crime.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name="crime_only_export.csv", mime="text/csv")

        with dl3:
            conn3 = sqlite3.connect(shared_db.DB_PATH)
            df_nc = pd.read_sql_query(
                "SELECT * FROM posts WHERE category='not crime-related'", conn3)
            conn3.close()
            if not df_nc.empty:
                st.download_button("✅ Not Crime Kaliya",
                    data=df_nc.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name="not_crime_only_export.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Cillad: {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  4. CSV Import
# ══════════════════════════════════════════════════════════════════════════════
elif choice == "📥 CSV Soo Geli Database":
    st.title("📥 CSV Soo Geli Database-ka")
    st.write("Upload-garee CSV file-kaaga si toos ah loogu galiyo database-ka.")

    uploaded_files = st.file_uploader(
        "Dooro CSV files (oo leh: url, text, category)",
        accept_multiple_files=True, type="csv")
    source_override = st.text_input("Source name (ikhtiyaari):", placeholder="Tus: Manual-Import")

    if st.button("🚀 Geli Database-ka", type="primary"):
        if not uploaded_files:
            st.error("Fadlan soo dooro ugu yaraan 1 CSV file.")
        else:
            total_added = 0
            for file in uploaded_files:
                try:
                    df = pd.read_csv(file, encoding="utf-8-sig")
                    df.columns = df.columns.str.lower().str.strip()
                    rows = [{
                        "url": str(r.get("url","")),
                        "text": str(r.get("text","")),
                        "category": str(r.get("category","None"))
                    } for _, r in df.iterrows()]
                    shared_db.insert_many(rows, source=source_override.strip() or file.name)
                    total_added += len(rows)
                    st.success(f"✅ {len(rows)} xog: **{file.name}**")
                except Exception as e:
                    st.error(f"Cillad — {file.name}: {e}")
            if total_added:
                st.balloons()
                st.success(f"Wadar: **{total_added}** xog ayaa lagu daray!")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  4.5 Manual Data Entry
# ══════════════════════════════════════════════════════════════════════════════
elif choice == "📝 Xog Gelin Gacanta (Manual Entry)":
    st.title("📝 Xog Gelin Gacanta (Manual Entry)")
    st.write("Halkan waxaad gacanta uga gelin kartaa xog kasta oo aad u baahantahay (Tusaale ahaan: qoraal aad meel kale ka soo koobiyeeysay).")

    with st.form("manual_entry_form"):
        m_url = st.text_input("URL (Ikhtiyaari):", placeholder="Tusaale: https://example.com/warka")
        m_text = st.text_area("Qoraalka Xogta (Text):", height=200, placeholder="Halkan ku qor xogta...")
        
        col1, col2 = st.columns(2)
        with col1:
            m_cat = st.selectbox("Category:", ["crime-related", "not crime-related"])
        with col2:
            m_source = st.text_input("Source (Halka aad ka keentay):", value="Manual Entry")
        
        submitted = st.form_submit_button("💾 Keydi Xogta", type="primary")
        
        if submitted:
            if not m_text.strip():
                st.error("Fadlan qoraalka xogta waa muhiim in aad geliso!")
            else:
                try:
                    row = [{
                        "url": m_url.strip(),
                        "text": m_text.strip(),
                        "category": m_cat
                    }]
                    shared_db.insert_many(row, source=m_source.strip())
                    st.success("✅ Xogta si guul ah ayaa loogu daray Database-ka!")
                except Exception as e:
                    st.error(f"Cillad ayaa dhacday: {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  5. Data Validator
# ══════════════════════════════════════════════════════════════════════════════
elif choice == "✅ Data Validator (Hubinta Xogta)":
    st.title("✅ Data Validator — Hubinta Xogta Mid-mid")
    st.write("Mid-mid u akhri qoraalada oo sax noocooda.")

    if "validator_idx" not in st.session_state:
        st.session_state.validator_idx = 0

    conn = sqlite3.connect(shared_db.DB_PATH)
    df_val = pd.read_sql_query("SELECT id, text, category FROM posts ORDER BY id", conn)
    conn.close()

    if df_val.empty:
        st.warning("Database-ka wax xog ah kuma jiraan.")
    else:
        total = len(df_val)
        idx   = st.session_state.validator_idx

        if idx >= total:
            st.success("🎉 Waxaad dhamaysay dhammaan xogta!")
            if st.button("Dib ugu noqo bilowga"):
                st.session_state.validator_idx = 0; st.rerun()
        else:
            row = df_val.iloc[idx]
            post_id, post_cat = int(row["id"]), str(row["category"])

            st.progress(idx / total, text=f"{idx+1} / {total}")
            st.markdown(f"**Category Hadda:** `{post_cat}`")
            edited_text = st.text_area("Qoraalka:", value=str(row["text"]),
                                        height=160, key=f"val_txt_{idx}")
            custom_cat  = st.text_input("Category cusub (ikhtiyaari):", key=f"val_cust_{idx}")

            def _update(new_cat):
                final = custom_cat.strip() if custom_cat.strip() else new_cat
                db = sqlite3.connect(shared_db.DB_PATH)
                db.execute("UPDATE posts SET category=?, text=? WHERE id=?",
                           (final, edited_text, post_id))
                db.commit(); db.close()
                st.session_state.validator_idx += 1

            c1,c2,c3,c4 = st.columns(4)
            with c1:
                if st.button("🩸 Crime",       key=f"cr_{idx}"): _update("crime-related");     st.rerun()
            with c2:
                if st.button("🟢 Not Crime",   key=f"nc_{idx}"): _update("not crime-related"); st.rerun()
            with c3:
                if st.button("✅ Dhaaf (Keep)",key=f"sv_{idx}"): _update(post_cat);             st.rerun()
            with c4:
                if st.button("⬅️ Dib u nogo", key=f"bk_{idx}"):
                    if st.session_state.validator_idx > 0:
                        st.session_state.validator_idx -= 1
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  6. Data Separator
# ══════════════════════════════════════════════════════════════════════════════
elif choice == "⚖️  Data Separator (Kala Saar & Balans)":
    st.title("⚖️ Data Separator & Balancer")
    st.write("Ka soo qaado xogta database-ka, isugu dheelli-tir, oo CSV ahaan soo daaji.")

    conn = sqlite3.connect(shared_db.DB_PATH)
    df_all = pd.read_sql_query("SELECT * FROM posts", conn)
    conn.close()

    if df_all.empty:
        st.warning("Database-ka waa madhan yahay.")
    else:
        df_all["_cat"] = df_all["category"].str.strip().str.lower()
        crime_df = df_all[df_all["_cat"] == "crime-related"].drop(columns=["_cat"])
        nc_df    = df_all[df_all["_cat"] == "not crime-related"].drop(columns=["_cat"])

        col_s1, col_s2 = st.columns(2)
        col_s1.metric("🚨 Crime Available",    len(crime_df))
        col_s2.metric("✅ Not Crime Available", len(nc_df))

        st.markdown("---")
        max_n  = max(1, min(len(crime_df), len(nc_df)))
        target = st.slider("Tirada file kasta:", 1, max_n, min(50, max_n))

        if st.button("⚖️ Kala Saar & Balansi", type="primary"):
            n         = min(target, max_n)
            c_sample  = crime_df.sample(n=n, random_state=42)
            nc_sample = nc_df.sample(n=n, random_state=42)
            combined  = pd.concat([c_sample, nc_sample]).sample(frac=1, random_state=42)

            st.success(f"✅ {n} Crime + {n} Not Crime = {len(combined)} Combined")

            d1,d2,d3 = st.columns(3)
            with d1:
                st.download_button("🚨 Crime CSV",
                    data=c_sample.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name="balanced_crime.csv", mime="text/csv")
            with d2:
                st.download_button("✅ Not Crime CSV",
                    data=nc_sample.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name="balanced_not_crime.csv", mime="text/csv")
            with d3:
                st.download_button("📦 Combined CSV",
                    data=combined.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name="balanced_combined.csv", mime="text/csv")
