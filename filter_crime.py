import csv
import os

input_file = r'c:\Users\ymaxa\OneDrive\Desktop\Web scrapping\universal_scraped_20260306_222047.csv'
output_file = r'c:\Users\ymaxa\OneDrive\Desktop\Web scrapping\crime_related_only.csv'

print(f"Processing {input_file}...")

try:
    with open(input_file, mode='r', encoding='utf-8', newline='') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            count = 0
            for row in reader:
                # Clean up category and check if it's crime-related
                category = row.get('category', '').strip().lower()
                if category == 'crime-related':
                    # "Nidaamisid" - let's clean up the text a bit (strip whitespace)
                    if 'text' in row:
                        row['text'] = row['text'].strip()
                    writer.writerow(row)
                    count += 1
            
    print(f"Done! Filtered {count} rows into {output_file}")
    
    # Overwrite the original file if requested (The user said "saar file ka" - meaning keep only those in the file)
    # I will keep the original as a backup just in case, but usually I should fulfill the request.
    # The user said "kaliya xoga category keeda uu crime-realted bis iigu reeb"
    # I'll replace the original.
    
    os.replace(output_file, input_file)
    print(f"Original file has been updated.")

except Exception as e:
    print(f"Error: {e}")
