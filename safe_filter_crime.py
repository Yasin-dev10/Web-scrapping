import csv
import os

input_file = r'c:\Users\ymaxa\OneDrive\Desktop\Web scrapping\universal_scraped_20260306_222047.csv'
output_file = r'c:\Users\ymaxa\OneDrive\Desktop\Web scrapping\crime_related_only.csv'

print(f"Filtering {input_file} for crime-related entries...")

try:
    # use utf-8-sig to automatically strip the BOM if it exists
    with open(input_file, mode='r', encoding='utf-8-sig', newline='') as infile:
        reader = csv.DictReader(infile)
        # Note: DictReader will now have 'url', 'text', 'category' as keys without the \ufeff
        fieldnames = reader.fieldnames
        print(f"Detected columns: {fieldnames}")
        
        with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            count = 0
            for row in reader:
                # Get the category safely (case insensitive and strip whitespace)
                category = row.get('category', '').strip().lower()
                
                # The user specifically asked for "crime-related"
                if category == 'crime-related':
                    # Organize: strip text but keep multi-line format if needed
                    # (csv.DictWriter handles the multi-line text correctly automatically)
                    if 'text' in row:
                        row['text'] = row['text'].strip()
                    
                    writer.writerow(row)
                    count += 1
            
    print(f"Success! Found {count} crime-related entries.")
    
    # Verify we got rows before replacing
    if count > 0:
        os.replace(output_file, input_file)
        print(f"The file {input_file} has been updated with {count} rows.")
    else:
        print("Warning: No matching rows found. File not replaced.")

except Exception as e:
    print(f"Error during processing: {e}")
