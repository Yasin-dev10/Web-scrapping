# Facebook Keyword Scraper

This tool uses Python and Selenium to scrape Facebook posts for specific keywords.

## Shuruudaha (Prerequisites)
1.  **Python**: Make sure Python is installed.
2.  **Chrome Browser**: Make sure Google Chrome is installed.

## Sida loo rakibo (Installation)
Fur Command Prompt oo qor:

```bash
python -m pip install -r requirements.txt
```

## Sida loo wado (How to Run)
Qor amarka soo socda:
## All in one
python main_dashboard.py

     ## News Scraper
python -X utf8 news_scraper_gui.py

     ## Nadiifinta xogta
python -X utf8 CrimeFilterTool.py

     ## Facebook Scraper
python -X utf8 facebook_scraper_clean.py

python facebook_scraper_gui.py
 

      ## Not Crime Scraper
python not_crime_filter_gui.py


     ## Split Data
python -X utf8 split_crime_data.py

     ## Data Separator
python data_separator.py

     ## Data Validator
python data_validator_gui.py

streamlit run app.py



```

Process-ka:
1.  Daaqad Chrome ah ayaa furmi doonta.
2.  **Gacanta ku gal Facebook (Login manually)** 60 ilbiriqsi gudahood.
3.  Barnaamijka ayaa bilaabi doona inuu raadiyo ereyada (keywords) oo keydiyo natiijada.

## Natiijada (Output)
Xogta waxaa lagu keydin doonaa fayl CSV ah: `facebook_data_TIMESTAMP.csv`.
