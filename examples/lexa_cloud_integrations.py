#!/usr/bin/env python3
"""
Cloud Storage Integrations Examples for Cerevox SDK

This comprehensive example demonstrates all cloud integration features available in both
the synchronous (Lexa) and asynchronous (AsyncLexa) clients.

🌟 FEATURES DEMONSTRATED:

SYNCHRONOUS CLIENT (Lexa):
├── Amazon S3: list_s3_buckets(), list_s3_folders(), parse_s3_folder()
├── Box: list_box_folders(), parse_box_folder()
├── Dropbox: list_dropbox_folders(), parse_dropbox_folder()
├── Microsoft SharePoint: list_sharepoint_sites(), list_sharepoint_drives(),
│                        list_sharepoint_folders(), parse_sharepoint_folder()
├── Salesforce: list_salesforce_folders(), parse_salesforce_folder()
└── Sendme: parse_sendme_files()

ASYNCHRONOUS CLIENT (AsyncLexa):
├── All the same methods as above but with async/await syntax
├── Better performance for batch operations
├── Concurrent processing capabilities
└── Context manager support

🔑 AUTHENTICATION PATTERNS:
- Please use the Cerevox UI to establish Authentication for each service.
- AWS S3: Uses AWS credentials (IAM roles, access keys, or AWS CLI config)
- Box/Dropbox/SharePoint/Salesforce: OAuth 2.0 tokens (handled by Cerevox backend)
- All services: Authentication is managed server-side after initial OAuth setup

💡 KEY CONCEPTS:
- All parse_* methods return DocumentBatch objects with parsed content
- All list_* methods return response objects with metadata
- Processing modes: DEFAULT, ADVANCED
- Progress callbacks for long-running operations
- Automatic polling and job status tracking
"""

import asyncio
import os

from cerevox import AsyncLexa, Lexa, LexaError, ProcessingMode


def amazon_s3_example(client: Lexa):
    """
    Amazon S3 Integration Example (Synchronous)

    Demonstrates:
    - Listing available S3 buckets
    - Listing folders within buckets
    - Parsing all documents in a folder
    - AWS authentication is handled automatically via AWS credentials
    """
    print("\n🪣 Amazon S3 Integration Example")
    print("-" * 40)

    try:
        # List available buckets
        print("📋 Listing S3 buckets...")
        buckets = client.list_s3_buckets()
        print(f"✅ Found {len(buckets.buckets)} buckets:")
        for bucket in buckets.buckets[:3]:  # Show first 3
            print(f"   - {bucket.name} (created: {bucket.creation_date})")

        if buckets.buckets:
            # Use first bucket for example
            bucket_name = buckets.buckets[0].name

            # List folders in bucket
            print(f"\n📁 Listing folders in bucket '{bucket_name}'...")
            folders = client.list_s3_folders(bucket_name)
            print(f"✅ Found {len(folders.folders)} folders")

            # Parse documents from a folder
            print(f"\n🚀 Parsing documents from S3 folder...")
            documents = client.parse_s3_folder(
                bucket_name=bucket_name,
                folder_path="documents/",  # Example folder path
                mode=ProcessingMode.DEFAULT,
            )
            print(f"✅ S3 folder parsed: {len(documents)} documents")

            # Display sample results
            for i, doc in enumerate(documents[:2]):  # Show first 2 docs
                print(
                    f"   📄 Document {i+1}: {doc.filename} ({len(doc.content)} chars)"
                )

    except LexaError as e:
        print(f"❌ Amazon S3 error: {e.message}")
        print(
            "💡 Ensure AWS credentials are configured (AWS CLI, IAM role, or env vars)"
        )


def box_example(client: Lexa):
    """
    Box Integration Example (Synchronous)

    Demonstrates:
    - Listing available Box folders
    - Parsing all documents in a folder
    - Box OAuth authentication is handled server-side by Cerevox
    """
    print("\n📦 Box Integration Example")
    print("-" * 40)

    try:
        # List Box folders
        print("📋 Listing Box folders...")
        folders = client.list_box_folders()
        print(f"✅ Found {len(folders.folders)} folders:")
        for folder in folders.folders[:3]:  # Show first 3
            print(f"   - {folder.name} (ID: {folder.id})")

        if folders.folders:
            # Parse documents from first folder
            folder_id = folders.folders[0].id
            print(
                f"\n🚀 Parsing documents from Box folder '{folders.folders[0].name}'..."
            )
            documents = client.parse_box_folder(
                box_folder_id=folder_id, mode=ProcessingMode.DEFAULT
            )
            print(f"✅ Box folder parsed: {len(documents)} documents")

            # Display sample results
            for i, doc in enumerate(documents[:2]):  # Show first 2 docs
                print(
                    f"   📄 Document {i+1}: {doc.filename} ({len(doc.content)} chars)"
                )

    except LexaError as e:
        print(f"❌ Box error: {e.message}")
        print("💡 Ensure Box OAuth is configured in your Cerevox account")


def dropbox_example(client: Lexa):
    """
    Dropbox Integration Example (Synchronous)

    Demonstrates:
    - Listing available Dropbox folders
    - Parsing all documents in a specific folder path
    - Dropbox OAuth authentication is handled server-side by Cerevox
    """
    print("\n📁 Dropbox Integration Example")
    print("-" * 40)

    try:
        # List Dropbox folders
        print("📋 Listing Dropbox folders...")
        folders = client.list_dropbox_folders()
        print(f"✅ Found {len(folders.folders)} folders:")
        for folder in folders.folders[:3]:  # Show first 3
            print(f"   - {folder.name} (path: {folder.path})")

        # Parse documents from a specific folder path
        print(f"\n🚀 Parsing documents from Dropbox folder...")
        documents = client.parse_dropbox_folder(
            folder_path="/Documents", mode=ProcessingMode.DEFAULT  # Example folder path
        )
        print(f"✅ Dropbox folder parsed: {len(documents)} documents")

        # Display sample results
        for i, doc in enumerate(documents[:2]):  # Show first 2 docs
            print(f"   📄 Document {i+1}: {doc.filename} ({len(doc.content)} chars)")

    except LexaError as e:
        print(f"❌ Dropbox error: {e.message}")
        print("💡 Ensure Dropbox OAuth is configured in your Cerevox account")


def microsoft_sharepoint_example(client: Lexa):
    """
    Microsoft SharePoint Integration Example (Synchronous)

    Demonstrates:
    - Listing SharePoint sites, drives, and folders in hierarchy
    - Parsing all documents in a SharePoint folder
    - Microsoft OAuth authentication is handled server-side by Cerevox
    """
    print("\n🏢 Microsoft SharePoint Integration Example")
    print("-" * 40)

    try:
        # List SharePoint sites
        print("📋 Listing SharePoint sites...")
        sites = client.list_sharepoint_sites()
        print(f"✅ Found {len(sites.sites)} sites:")
        for site in sites.sites[:3]:  # Show first 3
            print(f"   - {site.name} (ID: {site.id})")

        if sites.sites:
            site_id = sites.sites[0].id

            # List drives in site
            print(f"\n💾 Listing drives in site '{sites.sites[0].name}'...")
            drives = client.list_sharepoint_drives(site_id)
            print(f"✅ Found {len(drives.drives)} drives")

            if drives.drives:
                drive_id = drives.drives[0].id

                # List folders in drive
                print(f"\n📁 Listing folders in drive '{drives.drives[0].name}'...")
                folders = client.list_sharepoint_folders(drive_id)
                print(f"✅ Found {len(folders.folders)} folders")

                if folders.folders:
                    folder_id = folders.folders[0].id

                    # Parse documents from SharePoint folder
                    print(
                        f"\n🚀 Parsing documents from SharePoint folder '{folders.folders[0].name}'..."
                    )
                    documents = client.parse_sharepoint_folder(
                        drive_id=drive_id,
                        folder_id=folder_id,
                        mode=ProcessingMode.DEFAULT,
                    )
                    print(f"✅ SharePoint folder parsed: {len(documents)} documents")

                    # Display sample results
                    for i, doc in enumerate(documents[:2]):  # Show first 2 docs
                        print(
                            f"   📄 Document {i+1}: {doc.filename} ({len(doc.content)} chars)"
                        )

    except LexaError as e:
        print(f"❌ Microsoft SharePoint error: {e.message}")
        print("💡 Ensure Microsoft 365 OAuth is configured in your Cerevox account")


def salesforce_example(client: Lexa):
    """
    Salesforce Integration Example (Synchronous)

    Demonstrates:
    - Listing available Salesforce folders
    - Parsing all documents in a Salesforce folder
    - Salesforce OAuth authentication is handled server-side by Cerevox
    """
    print("\n⚡ Salesforce Integration Example")
    print("-" * 40)

    try:
        # List Salesforce folders
        print("📋 Listing Salesforce folders...")
        folders = client.list_salesforce_folders()
        print(f"✅ Found {len(folders.folders)} folders:")
        for folder in folders.folders[:3]:  # Show first 3
            print(f"   - {folder.name} (ID: {folder.id})")

        if folders.folders:
            # Parse documents from first folder
            folder_name = folders.folders[0].name
            print(f"\n🚀 Parsing documents from Salesforce folder '{folder_name}'...")
            documents = client.parse_salesforce_folder(
                folder_name=folder_name, mode=ProcessingMode.DEFAULT
            )
            print(f"✅ Salesforce folder parsed: {len(documents)} documents")

            # Display sample results
            for i, doc in enumerate(documents[:2]):  # Show first 2 docs
                print(
                    f"   📄 Document {i+1}: {doc.filename} ({len(doc.content)} chars)"
                )

    except LexaError as e:
        print(f"❌ Salesforce error: {e.message}")
        print("💡 Ensure Salesforce OAuth is configured in your Cerevox account")


def sendme_example(client: Lexa):
    """
    Sendme Integration Example (Synchronous)

    Demonstrates:
    - Parsing documents from a Sendme ticket
    - Sendme is a file sharing service integrated with Cerevox
    """
    print("\n📬 Sendme Integration Example")
    print("-" * 40)

    # Example Sendme ticket ID - replace with actual ticket
    ticket_id = "example-ticket-123"
    print(f"💡 Using example ticket ID: {ticket_id}")
    print("   (Replace with actual Sendme ticket ID)")

    try:
        # Parse documents from Sendme ticket
        print(f"\n🚀 Parsing documents from Sendme ticket...")
        documents = client.parse_sendme_files(
            ticket=ticket_id, mode=ProcessingMode.DEFAULT
        )
        print(f"✅ Sendme files parsed: {len(documents)} documents")

        # Display sample results
        for i, doc in enumerate(documents[:2]):  # Show first 2 docs
            print(f"   📄 Document {i+1}: {doc.filename} ({len(doc.content)} chars)")

    except LexaError as e:
        print(f"❌ Sendme error: {e.message}")
        print("💡 Ensure Sendme integration is configured in your Cerevox account")


# ASYNCHRONOUS EXAMPLES


async def async_amazon_s3_example(client: AsyncLexa):
    """
    Amazon S3 Integration Example (Asynchronous)

    Demonstrates async version with better performance for large operations
    """
    print("\n🪣 Amazon S3 Integration Example (Async)")
    print("-" * 45)

    try:
        # List available buckets
        print("📋 Listing S3 buckets...")
        buckets = await client.list_s3_buckets()
        print(f"✅ Found {len(buckets.buckets)} buckets:")
        for bucket in buckets.buckets[:3]:  # Show first 3
            print(f"   - {bucket.name} (created: {bucket.creation_date})")

        if buckets.buckets:
            # Use first bucket for example
            bucket_name = buckets.buckets[0].name

            # List folders in bucket
            print(f"\n📁 Listing folders in bucket '{bucket_name}'...")
            folders = await client.list_s3_folders(bucket_name)
            print(f"✅ Found {len(folders.folders)} folders")

            # Parse documents from a folder (async)
            print(f"\n🚀 Parsing documents from S3 folder (async)...")
            documents = await client.parse_s3_folder(
                bucket_name=bucket_name,
                folder_path="documents/",  # Example folder path
                mode=ProcessingMode.DEFAULT,
            )
            print(f"✅ S3 folder parsed: {len(documents)} documents")

            # Display sample results
            for i, doc in enumerate(documents[:2]):  # Show first 2 docs
                print(
                    f"   📄 Document {i+1}: {doc.filename} ({len(doc.content)} chars)"
                )

    except LexaError as e:
        print(f"❌ Amazon S3 error: {e.message}")
        print(
            "💡 Ensure AWS credentials are configured (AWS CLI, IAM role, or env vars)"
        )


async def async_cloud_integrations_demo():
    """
    Demonstrate async cloud integrations with better performance
    """
    print("\n🚀 ASYNCHRONOUS CLOUD INTEGRATIONS DEMO")
    print("=" * 60)
    print("💡 Async client provides better performance for:")
    print("   - Concurrent operations")
    print("   - Large batch processing")
    print("   - Non-blocking I/O operations")

    async with AsyncLexa() as client:
        # Example with S3
        await async_amazon_s3_example(client)


def main():
    """
    Main function demonstrating all synchronous cloud integrations
    """
    print("\n🌐 SYNCHRONOUS CLOUD INTEGRATIONS DEMO")
    print("=" * 60)
    print("💡 Authentication is managed server-side via OAuth setup in Cerevox UI")
    print("💡 AWS S3 uses your configured AWS credentials")

    # Initialize the synchronous client
    try:
        client = Lexa()
        print("✅ Lexa client initialized successfully")
    except ValueError as e:
        print(f"❌ Failed to initialize client: {e}")
        print("💡 Make sure to set CEREVOX_API_KEY environment variable")
        return

    # Run examples for each cloud provider
    try:
        # Core cloud storage providers
        amazon_s3_example(client)
        box_example(client)
        dropbox_example(client)
        microsoft_sharepoint_example(client)
        salesforce_example(client)
        sendme_example(client)

        print("\n🎉 Synchronous cloud integrations demo completed!")
        print("\n💡 Next steps:")
        print(
            "   - Run async demo with: python -c 'import asyncio; from cloud_integrations import async_cloud_integrations_demo; asyncio.run(async_cloud_integrations_demo())'"
        )
        print("   - Configure OAuth for each service in your Cerevox dashboard")
        print("   - Use progress callbacks for long-running operations")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def run_both_demos():
    """
    Run both synchronous and asynchronous demos
    """
    # Run synchronous demo
    main()

    # Run asynchronous demo
    await async_cloud_integrations_demo()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--async":
        # Run async demo only
        asyncio.run(async_cloud_integrations_demo())
    elif len(sys.argv) > 1 and sys.argv[1] == "--both":
        # Run both demos
        asyncio.run(run_both_demos())
    else:
        # Run sync demo only (default)
        main()

"""
USAGE INSTRUCTIONS:

1. Basic sync demo (default):
   python cloud_integrations.py

2. Async demo only:
   python cloud_integrations.py --async

3. Both sync and async demos:
   python cloud_integrations.py --both

SETUP REQUIREMENTS:

1. Environment Variable:
   export CEREVOX_API_KEY="your-api-key"

2. OAuth Configuration (via Cerevox Dashboard):
   - Box: Configure Box OAuth app and authorize 
   - Dropbox: Configure Dropbox OAuth app and authorize
   - Microsoft SharePoint: Configure Microsoft 365 OAuth app and authorize
   - Salesforce: Configure Salesforce OAuth app and authorize

3. AWS S3 Credentials (for S3 integration):
   - Use AWS CLI: aws configure
   - Or set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
   - Or use IAM roles if running on AWS infrastructure

4. Sendme Integration:
   - Configure Sendme integration in your Cerevox dashboard
   - Obtain valid Sendme ticket IDs for processing

PROCESSING MODES:
- ProcessingMode.DEFAULT: Standard processing with full features  
- ProcessingMode.ADVANCED: Advanced processing with enhanced accuracy

RESPONSE OBJECTS:
- parse_* methods return DocumentBatch objects with parsed content
- list_* methods return response objects with metadata and IDs
- All methods support progress callbacks for monitoring long-running operations
"""
