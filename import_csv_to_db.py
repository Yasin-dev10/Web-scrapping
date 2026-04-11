import sqlite3
import pandas as pd
from database import insert_post, init_db
import sys
import os

def import_csv(csv_path, default_source="Imported CSV"):
    if not os.path.exists(csv_path):
        print(f"File '{csv_path}' lama helin!")
        return

    init_db()
    try:
        df = pd.read_csv(csv_path)
        count = 0
        for _, row in df.iterrows():
            # Support various column names gracefully
            url = row['Url'] if 'Url' in df.columns else (row['URL'] if 'URL' in df.columns else '')
            text = row['Text'] if 'Text' in df.columns else (row['text'] if 'text' in df.columns else str(row))
            category = row['Category'] if 'Category' in df.columns else (row['category'] if 'category' in df.columns else 'None')
            
            insert_post(url, text, category, default_source)
            count += 1
        print(f"Guul! Waxaa la galiyay {count} xog ah Database-ka!")
    except Exception as e:
        print(f"Cilad ayaa dhacday: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        import_csv(sys.argv[1])
    else:
        print("Fadlan raaci magaca CSV faylka aad rabto inaad u wareejiso Database-ka.")
        print("Tusaale: python import_csv_to_db.py Not_Crime_Data.csv")
