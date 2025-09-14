from supabase import create_client, Client
import os
from typing import Optional
from dotenv import load_dotenv

class SupabaseClient:
    def __init__(self):
        load_dotenv()
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.url, self.key)
        print(f"Supabase client created: {self.client.auth.get_user()}")
    
    def get_client(self) -> Client:
        return self.client

# Global instance
_supabase_client: Optional[SupabaseClient] = None

def get_supabase_client() -> SupabaseClient:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client

from postgrest import APIError
import httpx

def supabase_health(client):
    try:
        res = client.rpc("ping", {}).execute()
        return res.data == "pong" or res.data == [{"ping":"pong"}]  # 兼容不同返回包装
    except (APIError, httpx.HTTPError) as e:
        print("Health check failed:", e)
        return False

if __name__ == "__main__":
    client = get_supabase_client()
    print(supabase_health(client.get_client()))