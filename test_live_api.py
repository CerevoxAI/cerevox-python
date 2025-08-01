#!/usr/bin/env python3
"""
Live End-to-End Test Script for Cerevox Client Modules

This script tests all functions in the hippo, async_hippo, account, and async_account
client modules against the live API at https://dev.cerevox.ai/v1

Usage:
    python test_live_api.py --email your@email.com --api-key your_password

Requirements:
    - Valid Cerevox credentials
    - Test file for upload (will be created if not exists)
"""

import argparse
import asyncio
import logging
import os
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cerevox import Account, AsyncAccount, AsyncHippo, Hippo
from cerevox.core import InsufficientPermissionsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("test_live_api.log")],
)
logger = logging.getLogger(__name__)


class TestResult:
    """Track test results"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors: List[str] = []

    def add_pass(self, test_name: str):
        self.passed += 1
        logger.info(f"✅ PASS: {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        logger.error(f"❌ FAIL: {test_name} - {error}")

    def add_skip(self, test_name: str, reason: str):
        self.skipped += 1
        logger.warning(f"⏭️  SKIP: {test_name} - {reason}")

    def summary(self):
        total = self.passed + self.failed + self.skipped
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")
        logger.info(f"Skipped: {self.skipped}")

        if self.errors:
            logger.info(f"\nFAILED TESTS:")
            for error in self.errors:
                logger.info(f"  - {error}")

        success_rate = (self.passed / total * 100) if total > 0 else 0
        logger.info(f"\nSuccess Rate: {success_rate:.1f}%")
        return self.failed == 0


class LiveAPITester:
    """Main test class for live API testing"""

    def __init__(
        self, email: str, api_key: str, base_url: str = "https://dev.cerevox.ai/v1"
    ):
        self.email = email
        self.api_key = api_key
        self.base_url = base_url
        self.result = TestResult()

        # Test data
        self.test_folder_id = f"test_folder_{int(time.time())}"
        self.test_folder_name = "Live API Test Folder"
        self.test_chat_id: Optional[str] = None
        self.test_file_path: Optional[str] = None
        self.created_resources: Dict[str, List[str]] = {
            "folders": [],
            "chats": [],
            "files": [],
        }

    def create_test_file(self) -> str:
        """Create a temporary test file for upload"""
        test_content = """
        # Test Document for Cerevox Live API Testing
        
        This is a test document created for testing the Cerevox RAG functionality.
        
        ## Key Information
        - This document contains sample content for testing
        - It includes multiple sections and formats
        - The content is designed to test RAG question-answering capabilities
        
        ## Sample Data
        The test was conducted on {timestamp} using the Cerevox Python SDK.
        
        ## Technical Details
        - API Endpoint: https://dev.cerevox.ai/v1
        - Client: Python SDK Live Test
        - Purpose: End-to-end functionality validation
        
        This document should be processed by the RAG system and used to answer questions
        about the test setup and configuration.
        """.format(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        # Create temporary file
        fd, path = tempfile.mkstemp(suffix=".txt", prefix="cerevox_test_")
        with os.fdopen(fd, "w") as f:
            f.write(test_content)

        self.test_file_path = path
        return path

    def cleanup_resources(self):
        """Clean up any created resources"""
        logger.info("🧹 Cleaning up test resources...")

        try:
            # Clean up with sync client
            hippo = Hippo(
                email=self.email, api_key=self.api_key, base_url=self.base_url
            )

            # Delete chats first
            for chat_id in self.created_resources.get("chats", []):
                try:
                    hippo.delete_chat(chat_id)
                    logger.info(f"Deleted chat: {chat_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete chat {chat_id}: {e}")

            # Delete folders (which will delete files)
            for folder_id in self.created_resources.get("folders", []):
                try:
                    hippo.delete_folder(folder_id)
                    logger.info(f"Deleted folder: {folder_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete folder {folder_id}: {e}")

        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

        # Clean up test file
        if self.test_file_path and os.path.exists(self.test_file_path):
            try:
                os.unlink(self.test_file_path)
                logger.info("Deleted test file")
            except Exception as e:
                logger.warning(f"Failed to delete test file: {e}")

    def test_sync_account_client(self):
        """Test synchronous Account client"""
        logger.info("🔍 Testing Sync Account Client")

        try:
            client = Account(
                email=self.email, api_key=self.api_key, base_url=self.base_url
            )

            # Test get_account_info
            try:
                account_info = client.get_account_info()
                self.result.add_pass("Account.get_account_info")
                account_id = account_info.account_id
                logger.info(
                    f"Account ID: {account_id}, Name: {account_info.account_name}"
                )
            except Exception as e:
                self.result.add_fail("Account.get_account_info", str(e))
                return

            # Test get_account_plan
            try:
                plan = client.get_account_plan(account_id)
                self.result.add_pass("Account.get_account_plan")
                logger.info(f"Plan: {plan.plan}")
            except Exception as e:
                self.result.add_fail("Account.get_account_plan", str(e))

            # Test get_account_usage
            try:
                usage = client.get_account_usage(account_id)
                self.result.add_pass("Account.get_account_usage")
                logger.info(f"Usage - Files: {usage.files}, Storage: {usage.storage}MB")
            except Exception as e:
                self.result.add_fail("Account.get_account_usage", str(e))

            # Test get_users
            try:
                users = client.get_users()
                self.result.add_pass("Account.get_users")
                logger.info(f"Found {len(users)} users")
            except Exception as e:
                self.result.add_fail("Account.get_users", str(e))

            # Test get_user_me
            try:
                user_me = client.get_user_me()
                self.result.add_pass("Account.get_user_me")
                logger.info(f"Current user: {user_me.name} ({user_me.email})")
            except Exception as e:
                self.result.add_fail("Account.get_user_me", str(e))

            # Test update_user_me (restore original name after)
            try:
                original_name = user_me.name
                test_name = f"{original_name} [TEST]"
                client.update_user_me(test_name)
                # Restore original name
                client.update_user_me(original_name)
                self.result.add_pass("Account.update_user_me")
            except Exception as e:
                self.result.add_fail("Account.update_user_me", str(e))

            # Admin-only functions (may fail with permission errors)
            if len(users) > 0:
                test_user_id = users[0].user_id

                try:
                    user = client.get_user_by_id(test_user_id)
                    self.result.add_pass("Account.get_user_by_id")
                except InsufficientPermissionsError:
                    self.result.add_skip(
                        "Account.get_user_by_id", "Admin permissions required"
                    )
                except Exception as e:
                    self.result.add_fail("Account.get_user_by_id", str(e))

                try:
                    client.update_user_by_id(test_user_id, users[0].name)
                    self.result.add_pass("Account.update_user_by_id")
                except InsufficientPermissionsError:
                    self.result.add_skip(
                        "Account.update_user_by_id", "Admin permissions required"
                    )
                except Exception as e:
                    self.result.add_fail("Account.update_user_by_id", str(e))

        except Exception as e:
            self.result.add_fail("Account client initialization", str(e))

    async def test_async_account_client(self):
        """Test asynchronous Account client"""
        logger.info("🔍 Testing Async Account Client")

        try:
            async with AsyncAccount(
                email=self.email, api_key=self.api_key, base_url=self.base_url
            ) as client:

                # Test get_account_info
                try:
                    account_info = await client.get_account_info()
                    self.result.add_pass("AsyncAccount.get_account_info")
                    account_id = account_info.account_id
                except Exception as e:
                    self.result.add_fail("AsyncAccount.get_account_info", str(e))
                    return

                # Test get_account_plan
                try:
                    plan = await client.get_account_plan(account_id)
                    self.result.add_pass("AsyncAccount.get_account_plan")
                except Exception as e:
                    self.result.add_fail("AsyncAccount.get_account_plan", str(e))

                # Test get_account_usage
                try:
                    usage = await client.get_account_usage(account_id)
                    self.result.add_pass("AsyncAccount.get_account_usage")
                except Exception as e:
                    self.result.add_fail("AsyncAccount.get_account_usage", str(e))

                # Test get_users
                try:
                    users = await client.get_users()
                    self.result.add_pass("AsyncAccount.get_users")
                except Exception as e:
                    self.result.add_fail("AsyncAccount.get_users", str(e))

                # Test get_user_me
                try:
                    user_me = await client.get_user_me()
                    self.result.add_pass("AsyncAccount.get_user_me")
                except Exception as e:
                    self.result.add_fail("AsyncAccount.get_user_me", str(e))

                # Test update_user_me
                try:
                    original_name = user_me.name
                    test_name = f"{original_name} [ASYNC TEST]"
                    await client.update_user_me(test_name)
                    await client.update_user_me(original_name)
                    self.result.add_pass("AsyncAccount.update_user_me")
                except Exception as e:
                    self.result.add_fail("AsyncAccount.update_user_me", str(e))

        except Exception as e:
            self.result.add_fail("AsyncAccount client initialization", str(e))

    def test_sync_hippo_client(self):
        """Test synchronous Hippo client"""
        logger.info("🔍 Testing Sync Hippo Client")

        try:
            client = Hippo(
                email=self.email, api_key=self.api_key, base_url=self.base_url
            )

            # Test create_folder
            try:
                folder_response = client.create_folder(
                    self.test_folder_id, self.test_folder_name
                )
                self.result.add_pass("Hippo.create_folder")
                self.created_resources["folders"].append(self.test_folder_id)
                logger.info(f"Created folder: {self.test_folder_id}")
            except Exception as e:
                self.result.add_fail("Hippo.create_folder", str(e))
                return

            # Test get_folders
            try:
                folders = client.get_folders()
                self.result.add_pass("Hippo.get_folders")
                logger.info(f"Found {len(folders)} folders")
            except Exception as e:
                self.result.add_fail("Hippo.get_folders", str(e))

            # Test get_folder_by_id
            try:
                folder = client.get_folder_by_id(self.test_folder_id)
                self.result.add_pass("Hippo.get_folder_by_id")
                logger.info(f"Folder name: {folder.folder_name}")
            except Exception as e:
                self.result.add_fail("Hippo.get_folder_by_id", str(e))

            # Test update_folder
            try:
                updated_name = f"{self.test_folder_name} [UPDATED]"
                client.update_folder(self.test_folder_id, updated_name)
                self.result.add_pass("Hippo.update_folder")
            except Exception as e:
                self.result.add_fail("Hippo.update_folder", str(e))

            # Test file upload
            test_file = self.create_test_file()
            try:
                upload_response = client.upload_file(self.test_folder_id, test_file)
                self.result.add_pass("Hippo.upload_file")
                logger.info(f"Uploaded file: {upload_response.uploads}")
            except Exception as e:
                self.result.add_fail("Hippo.upload_file", str(e))

            # Test upload_file_from_url
            try:
                url_files = [
                    {
                        "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                        "name": "test_url.pdf",
                        "type": "application/pdf",
                    }
                ]
                url_response = client.upload_file_from_url(
                    self.test_folder_id, url_files
                )
                self.result.add_pass("Hippo.upload_file_from_url")
            except Exception as e:
                self.result.add_fail("Hippo.upload_file_from_url", str(e))

            # Test get_files
            try:
                files = client.get_files(self.test_folder_id)
                self.result.add_pass("Hippo.get_files")
                logger.info(f"Found {len(files)} files in folder")

                if files:
                    # Test get_file_by_id
                    try:
                        file_info = client.get_file_by_id(
                            self.test_folder_id, files[0].file_id
                        )
                        self.result.add_pass("Hippo.get_file_by_id")
                    except Exception as e:
                        self.result.add_fail("Hippo.get_file_by_id", str(e))

            except Exception as e:
                self.result.add_fail("Hippo.get_files", str(e))

            # Test get_folder_file_count
            try:
                count = client.get_folder_file_count(self.test_folder_id)
                self.result.add_pass("Hippo.get_folder_file_count")
                logger.info(f"File count: {count}")
            except Exception as e:
                self.result.add_fail("Hippo.get_folder_file_count", str(e))

            # # Test create_chat
            # try:
            #     chat_response = client.create_chat(self.test_folder_id)
            #     self.test_chat_id = chat_response.chat_id
            #     self.created_resources["chats"].append(self.test_chat_id)
            #     self.result.add_pass("Hippo.create_chat")
            #     logger.info(f"Created chat: {self.test_chat_id}")
            # except Exception as e:
            #     self.result.add_fail("Hippo.create_chat", str(e))
            #     return

            # # Test get_chats
            # try:
            #     chats = client.get_chats()
            #     self.result.add_pass("Hippo.get_chats")
            #     logger.info(f"Found {len(chats)} chats")
            # except Exception as e:
            #     self.result.add_fail("Hippo.get_chats", str(e))

            # # Test get_chat_by_id
            # try:
            #     chat = client.get_chat_by_id(self.test_chat_id)
            #     self.result.add_pass("Hippo.get_chat_by_id")
            # except Exception as e:
            #     self.result.add_fail("Hippo.get_chat_by_id", str(e))

            # # Test update_chat
            # try:
            #     client.update_chat(self.test_chat_id, "Updated Test Chat")
            #     self.result.add_pass("Hippo.update_chat")
            # except Exception as e:
            #     self.result.add_fail("Hippo.update_chat", str(e))

            # # Test submit_ask (core RAG functionality)
            # try:
            #     ask_response = client.submit_ask(
            #         self.test_chat_id,
            #         "What is this document about and when was the test conducted?",
            #         is_qna=True,
            #     )
            #     self.result.add_pass("Hippo.submit_ask")
            #     logger.info(f"Ask response length: {len(ask_response.reply or '')}")
            # except Exception as e:
            #     self.result.add_fail("Hippo.submit_ask", str(e))

            # # Test get_asks
            # try:
            #     asks = client.get_asks(self.test_chat_id)
            #     self.result.add_pass("Hippo.get_asks")
            #     logger.info(f"Found {len(asks)} asks")

            #     if asks:
            #         # Test get_ask_by_index
            #         try:
            #             ask = client.get_ask_by_index(
            #                 self.test_chat_id, 0, show_files=True, show_source=True
            #             )
            #             self.result.add_pass("Hippo.get_ask_by_index")
            #         except Exception as e:
            #             self.result.add_fail("Hippo.get_ask_by_index", str(e))

            # except Exception as e:
            #     self.result.add_fail("Hippo.get_asks", str(e))

            # # Test get_chat_ask_count
            # try:
            #     count = client.get_chat_ask_count(self.test_chat_id)
            #     self.result.add_pass("Hippo.get_chat_ask_count")
            #     logger.info(f"Ask count: {count}")
            # except Exception as e:
            #     self.result.add_fail("Hippo.get_chat_ask_count", str(e))

        except Exception as e:
            self.result.add_fail("Hippo client initialization", str(e))

    async def test_async_hippo_client(self):
        """Test asynchronous Hippo client"""
        logger.info("🔍 Testing Async Hippo Client")

        async_folder_id = f"async_test_folder_{int(time.time())}"
        async_chat_id = None

        try:
            async with AsyncHippo(
                email=self.email, api_key=self.api_key, base_url=self.base_url
            ) as client:

                # Test create_folder
                try:
                    folder_response = await client.create_folder(
                        async_folder_id, "Async Test Folder"
                    )
                    self.result.add_pass("AsyncHippo.create_folder")
                    self.created_resources["folders"].append(async_folder_id)
                except Exception as e:
                    self.result.add_fail("AsyncHippo.create_folder", str(e))
                    return

                # Test get_folders
                try:
                    folders = await client.get_folders()
                    self.result.add_pass("AsyncHippo.get_folders")
                except Exception as e:
                    self.result.add_fail("AsyncHippo.get_folders", str(e))

                # Test get_folder_by_id
                try:
                    folder = await client.get_folder_by_id(async_folder_id)
                    self.result.add_pass("AsyncHippo.get_folder_by_id")
                except Exception as e:
                    self.result.add_fail("AsyncHippo.get_folder_by_id", str(e))

                # Test update_folder
                try:
                    await client.update_folder(
                        async_folder_id, "Async Test Folder [UPDATED]"
                    )
                    self.result.add_pass("AsyncHippo.update_folder")
                except Exception as e:
                    self.result.add_fail("AsyncHippo.update_folder", str(e))

                # Test file upload
                if not self.test_file_path:
                    self.create_test_file()

                try:
                    upload_response = await client.upload_file(
                        async_folder_id, self.test_file_path
                    )
                    self.result.add_pass("AsyncHippo.upload_file")
                except Exception as e:
                    self.result.add_fail("AsyncHippo.upload_file", str(e))

                # Test get_files
                try:
                    files = await client.get_files(async_folder_id)
                    self.result.add_pass("AsyncHippo.get_files")

                    if files:
                        # Test get_file_by_id
                        try:
                            file_info = await client.get_file_by_id(
                                async_folder_id, files[0].file_id
                            )
                            self.result.add_pass("AsyncHippo.get_file_by_id")
                        except Exception as e:
                            self.result.add_fail("AsyncHippo.get_file_by_id", str(e))

                except Exception as e:
                    self.result.add_fail("AsyncHippo.get_files", str(e))

                # Test convenience methods
                try:
                    count = await client.get_folder_file_count(async_folder_id)
                    self.result.add_pass("AsyncHippo.get_folder_file_count")
                except Exception as e:
                    self.result.add_fail("AsyncHippo.get_folder_file_count", str(e))

                # Test create_chat
                try:
                    chat_response = await client.create_chat(async_folder_id)
                    async_chat_id = chat_response.chat_id
                    self.created_resources["chats"].append(async_chat_id)
                    self.result.add_pass("AsyncHippo.create_chat")
                except Exception as e:
                    self.result.add_fail("AsyncHippo.create_chat", str(e))
                    return

                # Test get_chats
                try:
                    chats = await client.get_chats()
                    self.result.add_pass("AsyncHippo.get_chats")
                except Exception as e:
                    self.result.add_fail("AsyncHippo.get_chats", str(e))

                # Test submit_ask
                try:
                    ask_response = await client.submit_ask(
                        async_chat_id,
                        "What type of document is this and what is its purpose?",
                        is_qna=True,
                    )
                    self.result.add_pass("AsyncHippo.submit_ask")
                except Exception as e:
                    self.result.add_fail("AsyncHippo.submit_ask", str(e))

                # Test get_asks
                try:
                    asks = await client.get_asks(async_chat_id)
                    self.result.add_pass("AsyncHippo.get_asks")

                    if asks:
                        # Test get_ask_by_index
                        try:
                            ask = await client.get_ask_by_index(async_chat_id, 0)
                            self.result.add_pass("AsyncHippo.get_ask_by_index")
                        except Exception as e:
                            self.result.add_fail("AsyncHippo.get_ask_by_index", str(e))

                except Exception as e:
                    self.result.add_fail("AsyncHippo.get_asks", str(e))

                # Test get_chat_ask_count
                try:
                    count = await client.get_chat_ask_count(async_chat_id)
                    self.result.add_pass("AsyncHippo.get_chat_ask_count")
                except Exception as e:
                    self.result.add_fail("AsyncHippo.get_chat_ask_count", str(e))

        except Exception as e:
            self.result.add_fail("AsyncHippo client initialization", str(e))

    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting Live API End-to-End Tests")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Email: {self.email}")

        try:
            # Test sync clients
            # self.test_sync_account_client()
            self.test_sync_hippo_client()

            # Test async clients
            # await self.test_async_account_client()
            # await self.test_async_hippo_client()

        finally:
            # Always cleanup
            self.cleanup_resources()

        return self.result.summary()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Live API End-to-End Test for Cerevox Clients"
    )
    parser.add_argument("--email", required=True, help="Cerevox account email")
    parser.add_argument(
        "--api-key", required=True, help="Cerevox account password/API key"
    )
    parser.add_argument(
        "--base-url", default="https://dev.cerevox.ai/v1", help="API base URL"
    )

    args = parser.parse_args()

    # Create tester
    tester = LiveAPITester(
        email=args.email, api_key=args.api_key, base_url=args.base_url
    )

    # Run tests
    try:
        success = asyncio.run(tester.run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        tester.cleanup_resources()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        tester.cleanup_resources()
        sys.exit(1)


if __name__ == "__main__":
    main()
