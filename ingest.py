import os
import json
import sqlite3
import glob

def ingest_data(data_dir, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all categories (subdirectories)
    categories = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]

    for category in categories:
        table_name = category
        print(f"Processing table: {table_name}")
        
        category_dir = os.path.join(data_dir, category)
        jsonl_files = glob.glob(os.path.join(category_dir, "*.jsonl"))
        
        if not jsonl_files:
            continue
            
        # Peek at the first file to get columns
        with open(jsonl_files[0], 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if not first_line:
                continue
            first_record = json.loads(first_line)
            columns = list(first_record.keys())
        
        # Create table with dynamic columns (all TEXT for simplicity, can refine later)
        cols_def = ", ".join([f'"{col}" TEXT' for col in columns])
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(f"CREATE TABLE {table_name} ({cols_def})")
        
        # Insert records
        placeholders = ", ".join(["?" for _ in columns])
        insert_sql = f"INSERT INTO {table_name} ({', '.join([f'\"{c}\"' for c in columns])}) VALUES ({placeholders})"
        
        for jsonl_file in jsonl_files:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                records = []
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    row = []
                    for col in columns:
                        val = record.get(col)
                        if isinstance(val, (dict, list)):
                            val = json.dumps(val)
                        row.append(val)
                    records.append(row)
                
                cursor.executemany(insert_sql, records)
        
        conn.commit()
    
    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    DATA_DIR = "sap-o2c-data"
    DB_PATH = "o2c.db"
    ingest_data(DATA_DIR, DB_PATH)
