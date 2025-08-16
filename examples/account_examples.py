#!/usr/bin/env python3
"""
Comprehensive Account Management Examples - Cerevox SDK

This example demonstrates the complete functionality of the Cerevox Account Python SDK:

🔐 AUTHENTICATION:
- Login with email/password to get access tokens
- Refresh access tokens using refresh tokens
- Revoke tokens when done

📊 ACCOUNT MANAGEMENT:
- Get current account information
- Retrieve account plan and limits
- Check account usage metrics

👥 USER MANAGEMENT:
- Create new users in your account
- List all users in the account
- Get and update current user information
- Admin operations: get, update, delete users by ID

🎯 WHAT YOU'LL SEE:
- Authentication flow with token management
- Account information retrieval
- User creation and management
- Error handling and permissions management
- Both synchronous and asynchronous usage patterns

Prerequisites:
- Cerevox API key (set as CEREVOX_API_KEY environment variable)
- Valid email and password for login demonstration
- Admin privileges for user management operations

Usage:
    python account_examples.py
"""

import asyncio
import os
import sys
from typing import Optional

from cerevox import Account, AsyncAccount
from cerevox.account import InsufficientPermissionsError, UserManagementError
from cerevox.exceptions import (
    LexaAuthError,
    LexaError,
    LexaValidationError,
)


def print_header(title: str) -> None:
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}")


def print_sub_header(title: str) -> None:
    """Print a formatted sub-section header"""
    print(f"\n🔹 {title}")
    print("-" * 40)


def demonstrate_authentication(client: Account) -> Optional[str]:
    """
    Demonstrate authentication functionality
    Returns account_id for later use
    """
    print_header("AUTHENTICATION EXAMPLES")

    try:
        print_sub_header("Login with Email/Password")
        # Note: In real usage, you would get these from user input or secure storage
        email = os.getenv("DEMO_EMAIL")
        password = os.getenv("DEMO_PASSWORD")

        if not email or not password:
            print("⚠️  DEMO_EMAIL and DEMO_PASSWORD not set, skipping login demo")
            print("   Set these environment variables to test authentication")
            return None

        tokens = client._login(email, password)
        print(f"✅ Login successful!")
        print(f"   Access Token: {tokens.access_token[:20]}...")
        print(f"   Token Type: {tokens.token_type}")
        print(f"   Expires In: {tokens.expires_in} seconds")
        print(f"   Refresh Token: {tokens.refresh_token[:20]}...")

        print_sub_header("Refresh Token")
        new_tokens = client._refresh_token(tokens.refresh_token)
        print(f"✅ Token refresh successful!")
        print(f"   New Access Token: {new_tokens.access_token[:20]}...")

        print_sub_header("Revoke Token")
        revoke_response = client._revoke_token()
        print(f"✅ Token revocation: {revoke_response.message}")

        return None  # Would return account_id in real scenario

    except LexaAuthError as e:
        print(f"❌ Authentication failed: {e}")
        return None
    except LexaError as e:
        print(f"❌ API error during authentication: {e}")
        return None


def demonstrate_account_management(
    client: Account, account_id: Optional[str] = None
) -> Optional[str]:
    """
    Demonstrate account management functionality
    Returns account_id for later use
    """
    print_header("ACCOUNT MANAGEMENT EXAMPLES")

    try:
        print_sub_header("Get Account Information")
        account_info = client.get_account_info()
        print(f"✅ Account Information:")
        print(f"   Account ID: {account_info.account_id}")
        print(f"   Account Name: {account_info.account_name}")

        # Use the account ID from response for subsequent calls
        account_id = account_info.account_id

        print_sub_header("Get Account Plan")
        plan_info = client.get_account_plan(account_id)
        print(f"✅ Account Plan:")
        print(f"   Plan: {plan_info.plan}")
        print(f"   Base Limit: {plan_info.base}")
        print(f"   Storage Limit: {plan_info.bytes:,} bytes")
        print(f"   Status: {plan_info.status}")
        if plan_info.messages:
            print(f"   Message Limit: {plan_info.messages}")

        print_sub_header("Get Account Usage")
        usage_info = client.get_account_usage(account_id)
        print(f"✅ Account Usage:")
        print(f"   Files: {usage_info.files}")
        print(f"   Pages: {usage_info.pages}")
        print(f"   Advanced Pages: {usage_info.advanced_pages}")
        print(f"   Storage: {usage_info.storage}")

        return account_id

    except LexaError as e:
        print(f"❌ Error getting account information: {e}")
        return account_id


def demonstrate_user_management(client: Account) -> None:
    """Demonstrate user management functionality"""
    print_header("USER MANAGEMENT EXAMPLES")

    try:
        print_sub_header("Get Current User Information")
        current_user = client.get_user_me()
        print(f"✅ Current User:")
        print(f"   User ID: {current_user.user_id}")
        print(f"   Email: {current_user.email}")
        print(f"   Name: {current_user.name}")
        print(f"   Admin: {current_user.isadmin}")
        print(f"   Account ID: {current_user.account_id}")

        print_sub_header("Update Current User Information")
        original_name = current_user.name
        updated_response = client.update_user_me("Updated Test Name")
        print(f"✅ User update: {updated_response.status}")

        # Restore original name
        client.update_user_me(original_name)
        print(f"✅ Name restored to: {original_name}")

        print_sub_header("List All Users")
        users = client.get_users()
        print(f"✅ Found {len(users)} users in account:")
        for user in users[:3]:  # Show first 3 users
            print(f"   • {user.name} ({user.email}) - Admin: {user.isadmin}")

        if len(users) > 3:
            print(f"   ... and {len(users) - 3} more users")

    except InsufficientPermissionsError as e:
        print(f"⚠️  Permission error: {e}")
        print("   Some operations require admin privileges")
    except LexaError as e:
        print(f"❌ Error in user management: {e}")


def demonstrate_admin_operations(client: Account) -> None:
    """Demonstrate admin-only user management operations"""
    print_header("ADMIN USER MANAGEMENT EXAMPLES")

    try:
        print_sub_header("Create New User (Admin Only)")
        test_email = "test.user@example.com"
        test_name = "Test User"

        try:
            create_response = client.create_user(test_email, test_name)
            print(f"✅ User creation: {create_response.status}")
            created_user_id = None  # Would get from response in real scenario

            if created_user_id:
                print_sub_header("Get User by ID (Admin Only)")
                user_details = client.get_user_by_id(created_user_id)
                print(f"✅ User Details:")
                print(f"   Name: {user_details.name}")
                print(f"   Email: {user_details.email}")

                print_sub_header("Update User by ID (Admin Only)")
                update_response = client.update_user_by_id(
                    created_user_id, "Updated Test User"
                )
                print(f"✅ User update: {update_response.status}")

                print_sub_header("Delete User by ID (Admin Only)")
                delete_response = client.delete_user_by_id(created_user_id, test_email)
                print(f"✅ User deletion: {delete_response.status}")

        except InsufficientPermissionsError as e:
            print(f"⚠️  Admin operation failed: {e}")
            print("   These operations require admin privileges")

    except LexaValidationError as e:
        print(f"❌ Validation error: {e}")
        if e.validation_errors:
            for field, error in e.validation_errors.items():
                print(f"   {field}: {error}")
    except LexaError as e:
        print(f"❌ Error in admin operations: {e}")


def demonstrate_error_handling(client: Account) -> None:
    """Demonstrate comprehensive error handling"""
    print_header("ERROR HANDLING EXAMPLES")

    print_sub_header("Invalid Authentication")
    try:
        client._login("invalid@example.com", "wrong-password")
    except LexaAuthError as e:
        print(f"✅ Caught authentication error: {e}")
        print(f"   Status Code: {e.status_code}")
        print(f"   Request ID: {e.request_id}")

    print_sub_header("Invalid User Creation")
    try:
        client.create_user("invalid-email", "Test User")
    except LexaValidationError as e:
        print(f"✅ Caught validation error: {e}")
        if e.validation_errors:
            for field, error in e.validation_errors.items():
                print(f"   {field}: {error}")
    except InsufficientPermissionsError as e:
        print(f"✅ Caught permission error: {e}")
    except LexaError as e:
        print(f"✅ Caught general error: {e}")

    print_sub_header("Rate Limiting Handling")
    print("💡 Rate limiting would be handled automatically with retry logic")
    print(
        "   The client includes intelligent retry strategies for different error types"
    )


async def demonstrate_async_usage() -> None:
    """Demonstrate asynchronous Account client usage"""
    print_header("ASYNCHRONOUS ACCOUNT CLIENT EXAMPLES")

    try:
        async with AsyncAccount() as client:
            print_sub_header("Async Account Information")
            account_info = await client.get_account_info()
            print(
                f"✅ Account: {account_info.account_name} (ID: {account_info.account_id})"
            )

            print_sub_header("Async User Information")
            current_user = await client.get_user_me()
            print(f"✅ Current User: {current_user.name} ({current_user.email})")

            print_sub_header("Async User List")
            users = await client.get_users()
            print(f"✅ Found {len(users)} users in account")

    except LexaError as e:
        print(f"❌ Async error: {e}")


def main() -> None:
    """Run comprehensive Account client examples"""
    print("🚀 CEREVOX ACCOUNT SDK EXAMPLES")
    print("=" * 60)
    print("This example demonstrates the Cerevox Account management SDK")
    print("Make sure you have CEREVOX_API_KEY set in your environment")
    print()

    # Check for API key
    api_key = os.getenv("CEREVOX_API_KEY")
    if not api_key:
        print("❌ CEREVOX_API_KEY environment variable not set")
        print("   Please set your API key and try again")
        sys.exit(1)

    try:
        # Initialize client
        print("🔧 Initializing Account client...")
        with Account() as client:
            print("✅ Account client initialized successfully")

            # Run demonstrations
            account_id = demonstrate_authentication(client)
            account_id = demonstrate_account_management(client, account_id)
            demonstrate_user_management(client)
            demonstrate_admin_operations(client)
            demonstrate_error_handling(client)

        # Demonstrate async usage
        print("\n🔧 Running async examples...")
        asyncio.run(demonstrate_async_usage())

        print_header("EXAMPLE COMPLETED")
        print("✅ All Account management examples completed successfully!")
        print("   Check the output above for detailed results")

    except KeyboardInterrupt:
        print("\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
