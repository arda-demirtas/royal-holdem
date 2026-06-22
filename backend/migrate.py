import sqlite3
import os

def run_migration():
    db_path = os.path.join(os.path.dirname(__file__), "poker.db")
    if not os.path.exists(db_path):
        # Local fallback if directory structure is different
        db_path = "poker.db"
    
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    columns_to_add = [
        ("lp", "INTEGER DEFAULT 0"),
        ("league_tier", "INTEGER DEFAULT 1"),
        ("league_division", "INTEGER DEFAULT 3")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};")
            print(f"Column '{col_name}' added successfully.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column '{col_name}' already exists.")
            else:
                print(f"Error adding column '{col_name}': {e}")
                
    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    run_migration()
