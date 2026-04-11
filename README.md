# 🗄️ All-In-One Web Scraper & Crime Data Dashboard

Mashruucan wuxuu isticmaalaa Python si uu u soo uruuriyo, u nadiifiyo, kuna keydiyaa xogta warbaahinta iyo Facebook — meel keliya (SQLite Database).

---

## 📦 Shuruudaha (Prerequisites)
1. **Python 3.9+**
2. **Google Chrome** (Scraping-ga)

## ⚙️ Rakibidda (Installation)
```bash
pip install -r requirements.txt
```

---

## 🔄 Habka Shaqada (Workflow)

```
1. Scrape Xogta  →  2. Nadiifi / Kala Qaybi  →  3. Eeg & CSV Download
```

### Tallaabo 1 — Soo uruurso Xogta

```bash
# News & Social Media Scraper (wuu ku keydinayaa DB & CSV)
python -X utf8 news_scraper_gui.py

# Facebook Crime Scraper (wuu ku keydinayaa DB & CSV)
python facebook_scraper_gui.py
```

### Tallaabo 2 — Nadiifi & Kala Qaybi

```bash
# Crime Filter Tool — kaliya crime-related ayuu keydinayaa DB
python -X utf8 CrimeFilterTool.py

# Not Crime Filter — kaliya not crime-related ayuu keydinayaa DB
python not_crime_filter_gui.py

# Split Crime Data — labadaba kala saara oo DB ku keydinayaa
python -X utf8 split_crime_data.py

# Data Separator (GUI)
python data_separator.py

# Data Validator (GUI)
python data_validator_gui.py
```

### Tallaabo 3 — Eeg Xogta & Soo Daaji CSV

```bash
# Dashboard cusub (Tkinter) — Xogta oo dhan eeg, shaandheey, CSV download
python db_dashboard.py

# Streamlit Dashboard (Web) — full web app
streamlit run app.py

# Main Dashboard — Dhammaan barnaamijyada meel ka bilow
python main_dashboard.py
```

---

## 🗄️ Database-ka (unified_scraper.db)

Xogta **dhammaan barnaamijyada** waxay si toos ah ugu keydinayaan:
- `unified_scraper.db` — SQLite database (local, degdeg)

| Tiirka      | Sharaxaad                     |
|-------------|-------------------------------|
| `id`        | Lambarka gaarka ah            |
| `url`       | Xiriirka maqaalka / postka    |
| `text`      | Qoraalka oo dhan              |
| `category`  | `crime-related` / `not crime-related` |
| `source`    | Barnaamijka soo uruuriyay     |
| `scraped_at`| Taariikhda la soo uruuriyay   |

---

## 📥 Soo Daajinta CSV (Export)

### Hab 1 — Streamlit (Web)
```bash
streamlit run app.py
```
Fur: http://localhost:8501 → **"Xogta Database → Soo Daaji CSV"**

### Hab 2 — Tkinter Dashboard
```bash
python db_dashboard.py
```
Dooro filter, taabo **"📥 Soo Daaji CSV"**

---

## 📂 Faylasha Muhiimka Ah

| Faylka              | Shaqada                                 |
|---------------------|-----------------------------------------|
| `shared_db.py`      | Database module (wadaagta dhammaan)     |
| `news_scraper_gui.py` | News & Social scraper                 |
| `facebook_scraper_gui.py` | Facebook scraper               |
| `CrimeFilterTool.py` | Crime-only filter                      |
| `not_crime_filter_gui.py` | Not-crime filter               |
| `split_crime_data.py` | Crime/NotCrime kala saar              |
| `db_dashboard.py`   | Database viewer + CSV export (Tkinter)  |
| `app.py`            | Web dashboard (Streamlit)               |
| `main_dashboard.py` | Dhammaan barnaamijyada hal meel         |
