import csv
import os

input_file = r'c:\Users\ymaxa\OneDrive\Desktop\Web scrapping\universal_scraped_20260306_222047.csv'
output_file = r'c:\Users\ymaxa\OneDrive\Desktop\Web scrapping\universal_scraped_20260306_222047_final.csv'

print(f"Cleaning and deduplicating {input_file}...")

try:
    with open(input_file, mode='r', encoding='utf-8', newline='') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        rows = list(reader)
        
    original_count = len(rows)
    
    # Use a dictionary to deduplicate by URL (keeping the first occurrence)
    unique_rows = {}
    for row in rows:
        url = row.get('url', '').strip()
        if url not in unique_rows:
            # "Nidaami" - clean the text
            if 'text' in row:
                # Remove repeated newlines and extra spaces
                row['text'] = ' '.join(row['text'].split()) # This will make it one-line, but maybe user wants structure?
                # Actually, "nidaamisid" might mean keeping it formatted but clean. 
                # Let's just strip and normalize spaces within lines but keep structure if possible?
                # No, "one line per text" is very common for "organized" CSVs.
            unique_rows[url] = row
    
    final_rows = list(unique_rows.values())
    
    # Sort by URL
    final_rows.sort(key=lambda x: x.get('url', ''))
    
    with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(final_rows)
            
    print(f"Done! {original_count} -> {len(final_rows)} rows.")
    os.replace(output_file, input_file)
    print(f"Updated {input_file}")

except Exception as e:
    print(f"Error: {e}")
