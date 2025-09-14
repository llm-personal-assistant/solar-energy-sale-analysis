#!/usr/bin/env python3
"""
Python script to set up the database schema using Supabase client
"""
import os
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

async def setup_database():
    """Set up the database schema using Supabase client"""
    
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        return
    
    # Create Supabase client
    supabase: Client = create_client(url, key)
    
    try:
        # Read the schema file
        with open('database_schema.sql', 'r') as file:
            schema_sql = file.read()
        
        print("Setting up database schema...")
        
        # Execute the schema (Note: This requires service role key for DDL operations)
        # For production, you should use the service role key instead of anon key
        response = supabase.rpc('exec_sql', {'sql': schema_sql}).execute()
        print(f"Response: {response.data}")
        
        
        print("Database schema setup complete!")
        print("Tables created:")
        print("- profiles")
        print("- email_accounts") 
        print("- email_messages")
        print("- oauth_states")
        print("\nRow Level Security policies have been applied.")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        print("\nNote: You may need to use the Supabase Dashboard or CLI")
        print("to apply the schema, as some operations require elevated permissions.")

if __name__ == "__main__":
    asyncio.run(setup_database())
