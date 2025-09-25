"""
API usage examples for email data sync routes.
Demonstrates how to use the REST API endpoints for email synchronization.
"""

import requests
import json
from typing import Dict, Any


class EmailDataSyncAPI:
    """Client for email data sync API."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """Initialize API client."""
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json'
        }
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
    
    def get_user_accounts(self, active_only: bool = True) -> Dict[str, Any]:
        """Get user's email accounts."""
        url = f"{self.base_url}/data-sync/accounts"
        params = {
            'active_only': active_only
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def sync_emails(self, max_messages: int = 100, 
                   folder: str = None, background_sync: bool = False) -> Dict[str, Any]:
        """Sync emails for a user."""
        url = f"{self.base_url}/data-sync/sync"
        data = {
            'max_messages': max_messages,
            'folder': folder,
            'background_sync': background_sync
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def sync_account_emails(self, account_id: str, 
                           max_messages: int = 100, folder: str = None) -> Dict[str, Any]:
        """Sync emails for a specific account."""
        url = f"{self.base_url}/data-sync/sync/account/{account_id}"
        params = {
            'max_messages': max_messages,
            'folder': folder
        }
        
        response = requests.post(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status for a user."""
        url = f"{self.base_url}/data-sync/status"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_user_messages(self, limit: int = 50, offset: int = 0,
                         folder: str = None, unread_only: bool = False) -> Dict[str, Any]:
        """Get user messages."""
        url = f"{self.base_url}/data-sync/messages"
        params = {
            'limit': limit,
            'offset': offset,
            'folder': folder,
            'unread_only': unread_only
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read."""
        url = f"{self.base_url}/data-sync/messages/{message_id}/read"
        
        response = requests.patch(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_provider_folders(self, provider: str, 
                           account_id: str = None) -> Dict[str, Any]:
        """Get available folders for a provider."""
        url = f"{self.base_url}/data-sync/folders/{provider}"
        params = {
            'account_id': account_id
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()


def example_usage():
    """Example usage of the email data sync API."""
    
    # Initialize API client
    api = EmailDataSyncAPI(
        base_url="http://localhost:8000",  # Replace with your API URL
        api_key="your_api_key_here"  # Replace with your API key
    )
    
    user_id = "user_123"
    
    print("=== Email Data Sync API Examples ===\n")
    
    # 1. Get user's email accounts
    print("1. Getting user's email accounts...")
    try:
        accounts_response = api.get_user_accounts()
        print(f"Found {accounts_response['total']} accounts:")
        for account in accounts_response['accounts']:
            print(f"  - {account['email']} ({account['provider']}) - {'Active' if account['is_active'] else 'Inactive'}")
    except Exception as e:
        print(f"Error getting accounts: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 2. Get sync status
    print("2. Getting sync status...")
    try:
        status_response = api.get_sync_status()
        print(f"Sync Status:")
        print(f"  Total messages: {status_response['total_messages']}")
        print(f"  Unread messages: {status_response['unread_messages']}")
        print(f"  Folder counts: {status_response['folder_counts']}")
        print(f"  Latest sync: {status_response['latest_sync']}")
    except Exception as e:
        print(f"Error getting sync status: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 3. Sync emails for user
    print("3. Syncing emails for user...")
    try:
        sync_response = api.sync_emails(
            max_messages=50,
            folder="inbox",
            background_sync=False
        )
        print(f"Sync Result:")
        print(f"  Success: {sync_response['success']}")
        print(f"  Message: {sync_response['message']}")
        if sync_response.get('data'):
            data = sync_response['data']
            print(f"  Messages synced: {data.get('messages_synced', 0)}")
            print(f"  Messages created: {data.get('messages_created', 0)}")
            print(f"  Messages updated: {data.get('messages_updated', 0)}")
    except Exception as e:
        print(f"Error syncing emails: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 4. Get user messages
    print("4. Getting user messages...")
    try:
        messages_response = api.get_user_messages(
            limit=10,
            offset=0,
            folder="inbox"
        )
        print(f"Retrieved {len(messages_response['messages'])} messages:")
        for i, message in enumerate(messages_response['messages'][:3]):  # Show first 3
            print(f"  Message {i+1}:")
            print(f"    Subject: {message.get('subject', 'No subject')}")
            print(f"    From: {message.get('sender', 'Unknown sender')}")
            print(f"    Folder: {message.get('folder', 'Unknown folder')}")
            print(f"    Is Read: {message.get('is_read', False)}")
    except Exception as e:
        print(f"Error getting messages: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 5. Get Gmail folders
    print("5. Getting Gmail folders...")
    try:
        folders_response = api.get_provider_folders("google")
        print(f"Gmail folders for {folders_response['account_email']}:")
        for folder in folders_response['folders']:
            print(f"  - {folder['name']} ({folder['type']})")
    except Exception as e:
        print(f"Error getting Gmail folders: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 6. Background sync example
    print("6. Starting background sync...")
    try:
        bg_sync_response = api.sync_emails(
            max_messages=100,
            background_sync=True
        )
        print(f"Background sync started: {bg_sync_response['success']}")
        print(f"Message: {bg_sync_response['message']}")
    except Exception as e:
        print(f"Error starting background sync: {e}")


def curl_examples():
    """Example curl commands for the API."""
    
    base_url = "http://localhost:8000"
    user_id = "user_123"
    
    print("=== cURL Examples ===\n")
    
    # 1. Get user accounts
    print("1. Get user email accounts:")
    print(f"""curl -X GET "{base_url}/data-sync/accounts?active_only=true" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your_api_key_here"
""")
    
    # 2. Sync emails
    print("2. Sync emails for user:")
    print(f"""curl -X POST "{base_url}/data-sync/sync" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your_api_key_here" \\
  -d '{{
    "max_messages": 100,
    "folder": "inbox",
    "background_sync": false
  }}'
""")
    
    # 3. Get sync status
    print("3. Get sync status:")
    print(f"""curl -X GET "{base_url}/data-sync/status" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your_api_key_here"
""")
    
    # 4. Get user messages
    print("4. Get user messages:")
    print(f"""curl -X GET "{base_url}/data-sync/messages?limit=50&offset=0&folder=inbox" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your_api_key_here"
""")
    
    # 5. Mark message as read
    print("5. Mark message as read:")
    print(f"""curl -X PATCH "{base_url}/data-sync/messages/message_123/read" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your_api_key_here"
""")
    
    # 6. Get Gmail folders
    print("6. Get Gmail folders:")
    print(f"""curl -X GET "{base_url}/data-sync/folders/google" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your_api_key_here"
""")


if __name__ == "__main__":
    print("Email Data Sync API Usage Examples")
    print("=" * 60)
    
    # Run Python examples
    example_usage()
    
    print("\n" + "=" * 60 + "\n")
    
    # Show curl examples
    curl_examples()
    
    print("\nTo use these examples:")
    print("1. Start your FastAPI server")
    print("2. Replace 'http://localhost:8000' with your actual API URL")
    print("3. Replace 'your_api_key_here' with your actual API key")
    print("4. Replace 'user_123' with an actual user ID")
