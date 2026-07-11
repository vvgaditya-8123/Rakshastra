#!/usr/bin/env python3
import csv
import os
import json

def ingest():
    csv_dir = r"C:\Users\intel\Downloads\Published dataset\Publish dataset"
    output_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # c:\Rakshastra\rakshastra_core\intelligence
    output_path = os.path.join(output_dir, "rakshastra_core", "intelligence", "flagged_handles.json")
    
    print(f"Reading datasets from: {csv_dir}")
    print(f"Target output: {output_path}")
    
    flagged_handles = set()
    total_processed = 0
    
    for filename in ["Main_data.csv", "Other_data.csv"]:
        filepath = os.path.join(csv_dir, filename)
        if not os.path.exists(filepath):
            print(f"Warning: File {filename} not found.")
            continue
            
        print(f"Processing {filename}...")
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if len(row) < 2:
                        continue
                    url, label = row[0], row[1]
                    total_processed += 1
                    
                    if label == 'T':
                        # Extract username from url: https://twitter.com/username/status/...
                        parts = url.split('/')
                        if len(parts) > 3:
                            username = parts[3].strip()
                            if username and username.lower() not in ["twitter", "home", "search", "explore", "messages", "notifications", "i", "settings"]:
                                flagged_handles.add(username)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    handles_list = sorted(list(flagged_handles))
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(handles_list, f, indent=2)
        
    print(f"Successfully processed {total_processed} rows.")
    print(f"Extracted and saved {len(handles_list)} unique drug-related handles.")
    print(f"Sample handles: {handles_list[:15]}")

if __name__ == "__main__":
    ingest()
