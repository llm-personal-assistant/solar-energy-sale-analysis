#!/usr/bin/env python3
"""
Script to copy the database schema to clipboard for easy pasting into Supabase Dashboard
"""
import pyperclip
import os

def copy_schema_to_clipboard():
    """Copy the database schema to clipboard"""
    
    try:
        # Read the schema file
        with open('database_schema.sql', 'r') as file:
            schema_content = file.read()
        
        # Copy to clipboard
        pyperclip.copy(schema_content)
        
        print("✅ Database schema copied to clipboard!")
        print("\nNow you can:")
        print("1. Go to your Supabase Dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Click 'New Query'")
        print("4. Paste (Ctrl+V) the schema")
        print("5. Click 'Run' to execute")
        
    except FileNotFoundError:
        print("❌ Error: database_schema.sql file not found")
    except ImportError:
        print("❌ Error: pyperclip not installed")
        print("Install it with: pip install pyperclip")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    copy_schema_to_clipboard()
