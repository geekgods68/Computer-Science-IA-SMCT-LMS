#!/usr/bin/env python3
"""
Database initialization script for School Management Portal
Creates database structure using schema.sql (no test data)
"""

import sqlite3
import os
import sys

def create_database():
    """Create database using schema.sql file (structure only)"""
    # Check if schema.sql exists
    schema_file = 'database/schema.sql'
    if not os.path.exists(schema_file):
        print(f"Error: {schema_file} not found!")
        sys.exit(1)
    
    # Read schema file
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Connect to database
    conn = sqlite3.connect('users.db')
    conn.execute('PRAGMA foreign_keys = ON')
    
    try:
        # Execute schema (structure only)
        conn.executescript(schema_sql)
        conn.commit()
        print("✓ Database structure created successfully from schema.sql")
        
        # Verify tables were created
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✓ Created {len(tables)} tables")
        
    except Exception as e:
        print(f"✗ Database creation failed: {e}")
        sys.exit(1)
    finally:
        conn.close()

def reset_database():
    """Reset database by deleting and recreating"""
    if os.path.exists('users.db'):
        os.remove('users.db')
        print("� Existing database deleted")
    
    create_database()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize or reset the database')
    parser.add_argument('--reset', action='store_true', help='Reset database (delete and recreate)')
    args = parser.parse_args()
    
    if args.reset:
        reset_database()
    else:
        if os.path.exists('users.db'):
            print("⚠ Database already exists. Use --reset to recreate it.")
            sys.exit(1)
        create_database()
