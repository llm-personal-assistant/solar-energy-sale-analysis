"""
API Usage Examples

This file contains examples of how to use the Email Service API endpoints.
"""

import requests
import json
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

# Example user and account IDs
USER_ID = "user_123"
ACCOUNT_ID = "account_456"

def make_request(method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[Any, Any]:
    """Make an HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=data)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return {}


def example_get_emails():
    """Example: Get emails from an account."""
    print("=== Getting Emails ===")
    
    endpoint = f"/emails/{USER_ID}/{ACCOUNT_ID}"
    params = {
        "limit": 10,
        "unread_only": False
    }
    
    result = make_request("GET", endpoint, params)
    print(f"Result: {json.dumps(result, indent=2)}")


def example_search_emails():
    """Example: Search emails."""
    print("=== Searching Emails ===")
    
    endpoint = f"/emails/{USER_ID}/{ACCOUNT_ID}/search"
    params = {
        "query": "important",
        "limit": 5
    }
    
    result = make_request("GET", endpoint, params)
    print(f"Result: {json.dumps(result, indent=2)}")


def example_send_email():
    """Example: Send an email."""
    print("=== Sending Email ===")
    
    endpoint = f"/send/{USER_ID}/{ACCOUNT_ID}"
    data = {
        "to_emails": ["recipient@example.com"],
        "subject": "Test Email from API",
        "body": "This is a test email sent via the Email Service API.",
        "is_html": False,
        "cc_emails": ["cc@example.com"],
        "bcc_emails": ["bcc@example.com"]
    }
    
    result = make_request("POST", endpoint, data)
    print(f"Result: {json.dumps(result, indent=2)}")


def example_create_draft():
    """Example: Create a draft."""
    print("=== Creating Draft ===")
    
    endpoint = f"/drafts/{USER_ID}/{ACCOUNT_ID}"
    data = {
        "to_emails": ["recipient@example.com"],
        "subject": "Draft Email",
        "body": "This is a draft email created via the API.",
        "is_html": False
    }
    
    result = make_request("POST", endpoint, data)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Return draft ID for other examples
    if result.get("success"):
        return result.get("draft_id")
    return None


def example_update_draft(draft_id: str):
    """Example: Update a draft."""
    if not draft_id:
        print("No draft ID provided, skipping update example")
        return
    
    print("=== Updating Draft ===")
    
    endpoint = f"/drafts/{USER_ID}/{draft_id}"
    data = {
        "subject": "Updated Draft Email",
        "body": "This is an updated draft email."
    }
    
    result = make_request("PUT", endpoint, data)
    print(f"Result: {json.dumps(result, indent=2)}")


def example_get_drafts():
    """Example: Get user drafts."""
    print("=== Getting Drafts ===")
    
    endpoint = f"/drafts/{USER_ID}"
    params = {
        "limit": 10
    }
    
    result = make_request("GET", endpoint, params)
    print(f"Result: {json.dumps(result, indent=2)}")


def example_send_draft(draft_id: str):
    """Example: Send a draft."""
    if not draft_id:
        print("No draft ID provided, skipping send draft example")
        return
    
    print("=== Sending Draft ===")
    
    endpoint = f"/drafts/{USER_ID}/{draft_id}/send"
    
    result = make_request("POST", endpoint)
    print(f"Result: {json.dumps(result, indent=2)}")


def example_get_accounts():
    """Example: Get user accounts."""
    print("=== Getting Accounts ===")
    
    endpoint = f"/accounts/{USER_ID}"
    
    result = make_request("GET", endpoint)
    print(f"Result: {json.dumps(result, indent=2)}")


def example_get_auth_url():
    """Example: Get OAuth auth URL."""
    print("=== Getting Auth URL ===")
    
    endpoint = f"/accounts/{USER_ID}/auth-url/google"
    
    result = make_request("GET", endpoint)
    print(f"Result: {json.dumps(result, indent=2)}")


def example_get_statistics():
    """Example: Get email statistics."""
    print("=== Getting Statistics ===")
    
    endpoint = f"/accounts/{USER_ID}/statistics"
    
    result = make_request("GET", endpoint)
    print(f"Result: {json.dumps(result, indent=2)}")


def main():
    """Run all examples."""
    print("Email Service API Examples")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        if response.status_code == 200:
            print("✓ Server is running")
        else:
            print("✗ Server is not responding properly")
            return
    except requests.exceptions.RequestException:
        print("✗ Server is not running. Please start the server first:")
        print("  cd email_service && python start_server.py")
        return
    
    print()
    
    # Run examples
    example_get_accounts()
    print()
    
    example_get_auth_url()
    print()
    
    example_get_emails()
    print()
    
    example_search_emails()
    print()
    
    draft_id = example_create_draft()
    print()
    
    example_update_draft(draft_id)
    print()
    
    example_get_drafts()
    print()
    
    # Uncomment to actually send the draft
    # example_send_draft(draft_id)
    # print()
    
    example_get_statistics()
    print()
    
    # Uncomment to actually send an email
    # example_send_email()
    # print()
    
    print("Examples completed!")


if __name__ == "__main__":
    main()
