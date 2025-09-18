#!/usr/bin/env python3
"""
Test script for authentication functionality
"""
import asyncio
import sys
import os

# Add the parent directory to the path so we can import from the provider module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .auth_service import AuthService
from .models import UserSignUp, UserSignIn

async def test_auth():
    """Test the authentication functionality"""
    print("Testing Authentication System")
    print("=" * 40)
    
    # Initialize auth service
    auth_service = AuthService()
    
    # Test data
    test_email = "test@example.com"
    test_password = "testpassword123"
    test_name = "Test User"
    
    try:
        # Test 1: Sign Up
        print("\n1. Testing Sign Up...")
        signup_data = UserSignUp(
            email=test_email,
            password=test_password,
            full_name=test_name
        )
        
        try:
            signup_result = await auth_service.sign_up(signup_data)
            print(f"✅ Sign up successful!")
            print(f"   User ID: {signup_result.user.id}")
            print(f"   Email: {signup_result.user.email}")
            print(f"   Full Name: {signup_result.user.full_name}")
            print(f"   Access Token: {signup_result.access_token[:20]}...")
        except Exception as e:
            print(f"❌ Sign up failed: {e}")
            return
        
        # Test 2: Get Current User
        print("\n2. Testing Get Current User...")
        try:
            current_user = await auth_service.get_current_user()
            if current_user:
                print(f"✅ Current user retrieved!")
                print(f"   User ID: {current_user.id}")
                print(f"   Email: {current_user.email}")
            else:
                print("❌ No current user found")
        except Exception as e:
            print(f"❌ Get current user failed: {e}")
        
        # Test 3: Sign Out
        print("\n3. Testing Sign Out...")
        try:
            signout_result = await auth_service.sign_out()
            if signout_result:
                print("✅ Sign out successful!")
            else:
                print("❌ Sign out failed")
        except Exception as e:
            print(f"❌ Sign out failed: {e}")
        
        # Test 4: Sign In
        print("\n4. Testing Sign In...")
        signin_data = UserSignIn(
            email=test_email,
            password=test_password
        )
        
        try:
            signin_result = await auth_service.sign_in(signin_data)
            print(f"✅ Sign in successful!")
            print(f"   User ID: {signin_result.user.id}")
            print(f"   Email: {signin_result.user.email}")
            print(f"   Access Token: {signin_result.access_token[:20]}...")
        except Exception as e:
            print(f"❌ Sign in failed: {e}")
        
        # Test 5: Password Reset
        print("\n5. Testing Password Reset...")
        try:
            reset_result = await auth_service.reset_password(test_email)
            if reset_result:
                print("✅ Password reset email sent!")
            else:
                print("❌ Password reset failed")
        except Exception as e:
            print(f"❌ Password reset failed: {e}")
        
        print("\n" + "=" * 40)
        print("Authentication tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth())
