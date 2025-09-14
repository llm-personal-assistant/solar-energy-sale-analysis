#!/usr/bin/env python3
"""
Script to check if environment variables are properly configured
"""
import os
from dotenv import load_dotenv

def check_environment():
    """Check if all required environment variables are set"""
    
    print("🔍 Checking environment configuration...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Required variables
    required_vars = {
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_ANON_KEY': os.getenv('SUPABASE_ANON_KEY')
    }
    
    # Check each variable
    all_good = True
    for var_name, var_value in required_vars.items():
        if var_value:
            # Mask the key for security
            if 'KEY' in var_name:
                masked_value = var_value[:8] + "..." + var_value[-8:] if len(var_value) > 16 else "***"
            else:
                masked_value = var_value
            print(f"✅ {var_name}: {masked_value}")
        else:
            print(f"❌ {var_name}: NOT SET")
            all_good = False
    
    print("\n" + "=" * 50)
    
    if not all_good:
        print("❌ Missing required environment variables!")
        print("\nTo fix this:")
        print("1. Copy env.example to .env:")
        print("   cp env.example .env")
        print("\n2. Edit .env file with your Supabase credentials:")
        print("   - SUPABASE_URL: Get from Supabase Dashboard > Settings > API")
        print("   - SUPABASE_ANON_KEY: Get from Supabase Dashboard > Settings > API")
        print("\n3. Your .env file should look like:")
        print("   SUPABASE_URL=https://your-project.supabase.co")
        print("   SUPABASE_ANON_KEY=your-anon-key-here")
    else:
        print("✅ All environment variables are set!")
        print("You can now run the database setup.")
    
    return all_good

if __name__ == "__main__":
    check_environment()
