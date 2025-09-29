from supabase import create_client, Client
import os
from typing import Optional
from dotenv import load_dotenv
load_dotenv()
class SupabaseClient:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.url, self.key)
        self.admin_client: Optional[Client] = None
        if self.service_key:
            try:
                self.admin_client = create_client(self.url, self.service_key)
            except Exception:
                self.admin_client = None
    
    def get_client(self) -> Client:
        return self.client
    
    def get_admin_client(self) -> Optional[Client]:
        return self.admin_client

# Global instance
_supabase_client: Optional[SupabaseClient] = None

def get_supabase_client() -> SupabaseClient:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client


if __name__ == "__main__":
    client = get_supabase_client()
    print(supabase_health(client.get_client()))
