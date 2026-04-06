import csv
import os

input_file = r'c:\Users\ymaxa\OneDrive\Desktop\Web scrapping\universal_scraped_20260306_222047.csv'
output_file = r'c:\Users\ymaxa\OneDrive\Desktop\Web scrapping\universal_scraped_20260306_222047_clean_cols.csv'

print(f"Cleaning trailing columns in {input_file}...")

try:
    with open(input_file, mode='r', encoding='utf-8', newline='') as infile:
        reader = csv.reader(infile)
        header = next(reader)
        # Keep only the first 3 columns as they are the only ones with names
        clean_header = ['url', 'text', 'category']
        
        with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(clean_header)
            
            for row in reader:
                # Keep only the first 3 columns of each row
                writer.writerow(row[:3])
            
    os.replace(output_file, input_file)
    print(f"Successfully cleaned columns.")

except Exception as e:
    print(f"Error: {e}")
