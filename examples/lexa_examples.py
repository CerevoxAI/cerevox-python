#!/usr/bin/env python3
"""
Comprehensive Lexa Examples - Cerevox SDK

This example demonstrates the complete functionality of the Cerevox Lexa Python SDK:

📚 BASIC PARSING:
- Parse local files (single and multiple)
- Parse files from URLs
- Different processing modes (DEFAULT, FAST, DETAILED)
- Progress callbacks and timeout handling

☁️ CLOUD STORAGE INTEGRATIONS:
- Amazon S3: List buckets/folders, parse S3 folders
- Box: List folders, parse Box folders
- Dropbox: List folders, parse Dropbox folders
- Microsoft SharePoint: List sites/drives/folders, parse SharePoint folders
- Salesforce: List folders, parse Salesforce folders

🔧 ADVANCED FEATURES:
- Sendme file transfer integration
- Custom timeout and polling intervals
- Progress monitoring with callbacks
- Comprehensive error handling
- Job status monitoring
- Document batch processing

🎯 WHAT YOU'LL SEE:
- File parsing with different input types (paths, URLs, bytes, streams)
- Cloud storage listing and parsing operations
- Real-time job progress monitoring
- Error handling and recovery
- Different processing modes and their effects
- Working with DocumentBatch results

Prerequisites:
- Set CEREVOX_API_KEY environment variable
- Configure cloud storage integrations (if testing those features)
- Ensure you have appropriate permissions for cloud resources
"""

import os
import time
from io import BytesIO
from pathlib import Path

from cerevox import Lexa, LexaError, ProcessingMode


def progress_callback(status):
    """Example progress callback function"""
    print(f"   📊 Job Status: {status.status}")
    if hasattr(status, "progress") and status.progress:
        print(f"   📈 Progress: {status.progress}")


def demonstrate_basic_parsing(client):
    """Demonstrate basic file parsing functionality"""
    print("\n" + "=" * 60)
    print("📚 BASIC FILE PARSING")
    print("=" * 60)

    # Create test files for demonstration
    test_files = []

    # Test file 1: Simple text file
    test_file1 = Path("test_document.txt")
    with open(test_file1, "w") as f:
        f.write("This is a test document for Cerevox parsing.\n")
        f.write("It contains sample text to demonstrate basic parsing.\n")
        f.write("The Lexa service will extract and structure this content.\n")
    test_files.append(test_file1)

    # Test file 2: Another text file
    test_file2 = Path("test_document2.txt")
    with open(test_file2, "w") as f:
        f.write("Second test document.\n")
        f.write("This demonstrates parsing multiple files in a batch.\n")
        f.write("Each file will be processed individually.\n")
    test_files.append(test_file2)

    try:
        # Example 1: Parse single file
        print("\n🔍 Example 1: Parse Single File")
        print(f"   Parsing: {test_file1}")
        documents = client.parse(str(test_file1))
        print(f"   ✅ Success! Parsed {len(documents)} document(s)")
        if documents:
            print(f"   📄 First document preview: {documents[0].content[:100]}...")

        # Example 2: Parse multiple files
        print("\n🔍 Example 2: Parse Multiple Files")
        file_paths = [str(f) for f in test_files]
        print(f"   Parsing: {file_paths}")
        documents = client.parse(file_paths, mode=ProcessingMode.DEFAULT)
        print(f"   ✅ Success! Parsed {len(documents)} document(s)")

        # Example 3: Parse with different modes
        print("\n🔍 Example 3: Different Processing Modes")
        for mode in [ProcessingMode.DEFAULT, ProcessingMode.FAST]:
            print(f"   Testing mode: {mode.value}")
            documents = client.parse(str(test_file1), mode=mode)
            print(f"   ✅ Mode {mode.value}: {len(documents)} document(s)")

        # Example 4: Parse with progress callback
        print("\n🔍 Example 4: Parse with Progress Callback")
        documents = client.parse(
            str(test_file1),
            progress_callback=progress_callback,
            timeout=60.0,
            poll_interval=1.0,
        )
        print(f"   ✅ Success with callback! Parsed {len(documents)} document(s)")

        # Example 5: Parse bytes content
        print("\n🔍 Example 5: Parse Raw Bytes")
        content = (
            b"Raw byte content for parsing.\nThis is direct content without a file."
        )
        documents = client.parse(content)
        print(f"   ✅ Success! Parsed {len(documents)} document(s) from bytes")

        # Example 6: Parse file-like object
        print("\n🔍 Example 6: Parse File-like Object")
        content_stream = BytesIO(
            b"Stream content for parsing.\nThis comes from a BytesIO stream."
        )
        documents = client.parse(content_stream)
        print(f"   ✅ Success! Parsed {len(documents)} document(s) from stream")

    except LexaError as e:
        print(f"   ❌ Lexa error: {e.message}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
    finally:
        # Clean up test files
        for test_file in test_files:
            if test_file.exists():
                test_file.unlink()
        print(f"   🧹 Cleaned up test files")


def demonstrate_url_parsing(client):
    """Demonstrate URL parsing functionality"""
    print("\n" + "=" * 60)
    print("🌐 URL PARSING")
    print("=" * 60)

    # Example URLs (using publicly accessible documents)
    example_urls = [
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "https://www.learningcontainer.com/wp-content/uploads/2019/09/sample-pdf-file.pdf",
    ]

    try:
        # Example 1: Parse single URL
        print("\n🔍 Example 1: Parse Single URL")
        url = example_urls[0]
        print(f"   Parsing: {url}")
        documents = client.parse_urls(url)
        print(f"   ✅ Success! Parsed {len(documents)} document(s)")

        # Example 2: Parse multiple URLs
        print("\n🔍 Example 2: Parse Multiple URLs")
        print(f"   Parsing {len(example_urls)} URLs...")
        documents = client.parse_urls(example_urls, mode=ProcessingMode.DEFAULT)
        print(f"   ✅ Success! Parsed {len(documents)} document(s)")

        # Example 3: Parse URLs with callback
        print("\n🔍 Example 3: Parse URLs with Progress Callback")
        documents = client.parse_urls(
            example_urls[0],
            progress_callback=progress_callback,
            timeout=120.0,  # URLs might take longer
        )
        print(f"   ✅ Success with callback! Parsed {len(documents)} document(s)")

    except LexaError as e:
        print(f"   ❌ Lexa error: {e.message}")
        print("   💡 This might be expected if the example URLs are not accessible")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")


def demonstrate_s3_integration(client):
    """Demonstrate Amazon S3 integration functionality"""
    print("\n" + "=" * 60)
    print("☁️ AMAZON S3 INTEGRATION")
    print("=" * 60)

    try:
        # Example 1: List available S3 buckets
        print("\n🔍 Example 1: List S3 Buckets")
        try:
            buckets = client.list_s3_buckets()
            print(f"   ✅ Found {len(buckets.buckets)} bucket(s)")
            for bucket in buckets.buckets[:3]:  # Show first 3
                print(f"   📦 Bucket: {bucket.name}")
                if bucket.creation_date:
                    print(f"      Created: {bucket.creation_date}")
        except LexaError as e:
            print(f"   ❌ Could not list buckets: {e.message}")
            print("   💡 Make sure S3 integration is configured")
            return

        # Example 2: List folders in a bucket (if we have buckets)
        if buckets.buckets:
            print("\n🔍 Example 2: List Folders in S3 Bucket")
            bucket_name = buckets.buckets[0].name
            print(f"   Exploring bucket: {bucket_name}")
            try:
                folders = client.list_s3_folders(bucket_name)
                print(f"   ✅ Found {len(folders.folders)} folder(s)")
                for folder in folders.folders[:5]:  # Show first 5
                    print(f"   📁 Folder: {folder.name}")
                    if folder.size:
                        print(f"      Size: {folder.size} bytes")

                # Example 3: Parse files from S3 folder (if we have folders)
                if folders.folders:
                    print("\n🔍 Example 3: Parse S3 Folder")
                    folder_path = folders.folders[0].name
                    print(f"   Parsing folder: {folder_path}")
                    print("   ⏳ This may take a while depending on folder size...")

                    documents = client.parse_s3_folder(
                        bucket_name=bucket_name,
                        folder_path=folder_path,
                        mode=ProcessingMode.DEFAULT,
                        progress_callback=progress_callback,
                        timeout=300.0,  # 5 minutes timeout
                    )
                    print(f"   ✅ Success! Parsed {len(documents)} document(s)")

                    # Show document details
                    for i, doc in enumerate(documents[:2]):  # Show first 2
                        print(f"   📄 Document {i+1}:")
                        print(f"      Content preview: {doc.content[:100]}...")
                        if hasattr(doc, "metadata") and doc.metadata:
                            print(f"      Metadata keys: {list(doc.metadata.keys())}")
                else:
                    print("   💡 No folders found to parse")

            except LexaError as e:
                print(f"   ❌ Could not list folders: {e.message}")

    except LexaError as e:
        print(f"   ❌ S3 integration error: {e.message}")
        print(
            "   💡 Ensure S3 credentials are configured and you have appropriate permissions"
        )
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")


def demonstrate_box_integration(client):
    """Demonstrate Box integration functionality"""
    print("\n" + "=" * 60)
    print("📦 BOX INTEGRATION")
    print("=" * 60)

    try:
        # Example 1: List available Box folders
        print("\n🔍 Example 1: List Box Folders")
        try:
            folders = client.list_box_folders()
            print(f"   ✅ Found {len(folders.folders)} folder(s)")
            for folder in folders.folders[:5]:  # Show first 5
                print(f"   📁 Folder: {folder.name}")
                if hasattr(folder, "id"):
                    print(f"      ID: {folder.id}")
        except LexaError as e:
            print(f"   ❌ Could not list folders: {e.message}")
            print("   💡 Make sure Box integration is configured")
            return

        # Example 2: Parse files from Box folder (if we have folders)
        if folders.folders:
            print("\n🔍 Example 2: Parse Box Folder")
            folder = folders.folders[0]
            folder_id = getattr(folder, "id", folder.name)
            print(f"   Parsing folder: {folder.name} (ID: {folder_id})")
            print("   ⏳ This may take a while depending on folder size...")

            documents = client.parse_box_folder(
                box_folder_id=folder_id,
                mode=ProcessingMode.DEFAULT,
                progress_callback=progress_callback,
                timeout=300.0,
            )
            print(f"   ✅ Success! Parsed {len(documents)} document(s)")

            # Show document details
            for i, doc in enumerate(documents[:2]):
                print(f"   📄 Document {i+1}:")
                print(f"      Content preview: {doc.content[:100]}...")
        else:
            print("   💡 No folders found to parse")

    except LexaError as e:
        print(f"   ❌ Box integration error: {e.message}")
        print("   💡 Ensure Box authentication is configured")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")


def demonstrate_dropbox_integration(client):
    """Demonstrate Dropbox integration functionality"""
    print("\n" + "=" * 60)
    print("📁 DROPBOX INTEGRATION")
    print("=" * 60)

    try:
        # Example 1: List available Dropbox folders
        print("\n🔍 Example 1: List Dropbox Folders")
        try:
            folders = client.list_dropbox_folders()
            print(f"   ✅ Found {len(folders.folders)} folder(s)")
            for folder in folders.folders[:5]:  # Show first 5
                print(f"   📁 Folder: {folder.name}")
        except LexaError as e:
            print(f"   ❌ Could not list folders: {e.message}")
            print("   💡 Make sure Dropbox integration is configured")
            return

        # Example 2: Parse files from Dropbox folder (if we have folders)
        if folders.folders:
            print("\n🔍 Example 2: Parse Dropbox Folder")
            folder_path = folders.folders[0].name
            print(f"   Parsing folder: {folder_path}")
            print("   ⏳ This may take a while depending on folder size...")

            documents = client.parse_dropbox_folder(
                folder_path=folder_path,
                mode=ProcessingMode.DEFAULT,
                progress_callback=progress_callback,
                timeout=300.0,
            )
            print(f"   ✅ Success! Parsed {len(documents)} document(s)")

            # Show document details
            for i, doc in enumerate(documents[:2]):
                print(f"   📄 Document {i+1}:")
                print(f"      Content preview: {doc.content[:100]}...")
        else:
            print("   💡 No folders found to parse")

    except LexaError as e:
        print(f"   ❌ Dropbox integration error: {e.message}")
        print("   💡 Ensure Dropbox authentication is configured")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")


def demonstrate_sharepoint_integration(client):
    """Demonstrate Microsoft SharePoint integration functionality"""
    print("\n" + "=" * 60)
    print("🏢 MICROSOFT SHAREPOINT INTEGRATION")
    print("=" * 60)

    try:
        # Example 1: List available SharePoint sites
        print("\n🔍 Example 1: List SharePoint Sites")
        try:
            sites = client.list_sharepoint_sites()
            print(f"   ✅ Found {len(sites.sites)} site(s)")
            for site in sites.sites[:3]:  # Show first 3
                print(f"   🏢 Site: {site.name}")
                if hasattr(site, "id"):
                    print(f"      ID: {site.id}")
                if hasattr(site, "url"):
                    print(f"      URL: {site.url}")
        except LexaError as e:
            print(f"   ❌ Could not list sites: {e.message}")
            print("   💡 Make sure SharePoint integration is configured")
            return

        # Example 2: List drives in a site (if we have sites)
        if sites.sites:
            print("\n🔍 Example 2: List Drives in SharePoint Site")
            site = sites.sites[0]
            site_id = getattr(site, "id", site.name)
            print(f"   Exploring site: {site.name}")
            try:
                drives = client.list_sharepoint_drives(site_id)
                print(f"   ✅ Found {len(drives.drives)} drive(s)")
                for drive in drives.drives[:3]:  # Show first 3
                    print(f"   💾 Drive: {drive.name}")
                    if hasattr(drive, "id"):
                        print(f"      ID: {drive.id}")

                # Example 3: List folders in a drive (if we have drives)
                if drives.drives:
                    print("\n🔍 Example 3: List Folders in SharePoint Drive")
                    drive = drives.drives[0]
                    drive_id = getattr(drive, "id", drive.name)
                    print(f"   Exploring drive: {drive.name}")
                    try:
                        folders = client.list_sharepoint_folders(drive_id)
                        print(f"   ✅ Found {len(folders.folders)} folder(s)")
                        for folder in folders.folders[:5]:  # Show first 5
                            print(f"   📁 Folder: {folder.name}")

                        # Example 4: Parse files from SharePoint folder (if we have folders)
                        if folders.folders:
                            print("\n🔍 Example 4: Parse SharePoint Folder")
                            folder = folders.folders[0]
                            folder_id = getattr(folder, "id", folder.name)
                            print(f"   Parsing folder: {folder.name}")
                            print(
                                "   ⏳ This may take a while depending on folder size..."
                            )

                            documents = client.parse_sharepoint_folder(
                                drive_id=drive_id,
                                folder_id=folder_id,
                                mode=ProcessingMode.DEFAULT,
                                progress_callback=progress_callback,
                                timeout=300.0,
                            )
                            print(f"   ✅ Success! Parsed {len(documents)} document(s)")

                            # Show document details
                            for i, doc in enumerate(documents[:2]):
                                print(f"   📄 Document {i+1}:")
                                print(f"      Content preview: {doc.content[:100]}...")
                        else:
                            print("   💡 No folders found to parse")
                    except LexaError as e:
                        print(f"   ❌ Could not list folders: {e.message}")
                else:
                    print("   💡 No drives found")
            except LexaError as e:
                print(f"   ❌ Could not list drives: {e.message}")

    except LexaError as e:
        print(f"   ❌ SharePoint integration error: {e.message}")
        print("   💡 Ensure SharePoint authentication is configured")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")


def demonstrate_salesforce_integration(client):
    """Demonstrate Salesforce integration functionality"""
    print("\n" + "=" * 60)
    print("⚡ SALESFORCE INTEGRATION")
    print("=" * 60)

    try:
        # Example 1: List available Salesforce folders
        print("\n🔍 Example 1: List Salesforce Folders")
        try:
            folders = client.list_salesforce_folders()
            print(f"   ✅ Found {len(folders.folders)} folder(s)")
            for folder in folders.folders[:5]:  # Show first 5
                print(f"   📁 Folder: {folder.name}")
        except LexaError as e:
            print(f"   ❌ Could not list folders: {e.message}")
            print("   💡 Make sure Salesforce integration is configured")
            return

        # Example 2: Parse files from Salesforce folder (if we have folders)
        if folders.folders:
            print("\n🔍 Example 2: Parse Salesforce Folder")
            folder_name = folders.folders[0].name
            print(f"   Parsing folder: {folder_name}")
            print("   ⏳ This may take a while depending on folder size...")

            documents = client.parse_salesforce_folder(
                folder_name=folder_name,
                mode=ProcessingMode.DEFAULT,
                progress_callback=progress_callback,
                timeout=300.0,
            )
            print(f"   ✅ Success! Parsed {len(documents)} document(s)")

            # Show document details
            for i, doc in enumerate(documents[:2]):
                print(f"   📄 Document {i+1}:")
                print(f"      Content preview: {doc.content[:100]}...")
        else:
            print("   💡 No folders found to parse")

    except LexaError as e:
        print(f"   ❌ Salesforce integration error: {e.message}")
        print("   💡 Ensure Salesforce authentication is configured")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")


def demonstrate_sendme_integration(client):
    """Demonstrate Sendme integration functionality"""
    print("\n" + "=" * 60)
    print("📨 SENDME INTEGRATION")
    print("=" * 60)

    # Note: This is a special integration that requires a ticket
    print("\n🔍 Example: Parse Sendme Files")
    print("   💡 Sendme integration requires a valid ticket ID")
    print("   💡 Replace 'your-ticket-id' with an actual Sendme ticket")

    # Example ticket (users should replace with real ticket)
    example_ticket = "your-ticket-id"

    if example_ticket != "your-ticket-id":
        try:
            print(f"   Parsing Sendme ticket: {example_ticket}")
            print("   ⏳ This may take a while depending on file size...")

            documents = client.parse_sendme_files(
                ticket=example_ticket,
                mode=ProcessingMode.DEFAULT,
                progress_callback=progress_callback,
                timeout=300.0,
            )
            print(f"   ✅ Success! Parsed {len(documents)} document(s)")

            # Show document details
            for i, doc in enumerate(documents[:2]):
                print(f"   📄 Document {i+1}:")
                print(f"      Content preview: {doc.content[:100]}...")

        except LexaError as e:
            print(f"   ❌ Sendme integration error: {e.message}")
            print("   💡 Ensure the ticket ID is valid and accessible")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
    else:
        print("   ⚠️  Skipping Sendme example - no valid ticket provided")
        print("   📝 To test Sendme integration:")
        print("      1. Get a valid Sendme ticket ID")
        print("      2. Replace 'your-ticket-id' with the actual ticket")
        print("      3. Run the example again")


def demonstrate_advanced_features(client):
    """Demonstrate advanced features like error handling, job monitoring, and DocumentBatch"""
    print("\n" + "=" * 60)
    print("🔧 ADVANCED FEATURES")
    print("=" * 60)

    # Create test files for advanced examples
    test_files = []

    # Create different types of test files
    advanced_file1 = Path("advanced_test.txt")
    with open(advanced_file1, "w") as f:
        f.write("Advanced test document with structured content.\n")
        f.write("Title: Important Document\n")
        f.write("Author: Test User\n")
        f.write("Content: This document demonstrates advanced parsing features.\n")
        f.write("Keywords: parsing, advanced, features, testing\n")
    test_files.append(advanced_file1)

    advanced_file2 = Path("metadata_test.txt")
    with open(advanced_file2, "w") as f:
        f.write("Document with rich metadata for testing.\n")
        f.write("Created: 2024-01-01\n")
        f.write("Category: Test\n")
        f.write("Priority: High\n")
        f.write("This content will be used to test metadata extraction.\n")
    test_files.append(advanced_file2)

    try:
        # Example 1: Custom timeout and polling
        print("\n🔍 Example 1: Custom Timeout and Polling")
        print("   Parsing with custom timeout (30s) and poll interval (0.5s)")
        documents = client.parse(str(advanced_file1), timeout=30.0, poll_interval=0.5)
        print(f"   ✅ Success with custom timing! Parsed {len(documents)} document(s)")

        # Example 2: Detailed progress monitoring
        print("\n🔍 Example 2: Detailed Progress Monitoring")

        def detailed_progress_callback(status):
            """More detailed progress callback"""
            print(f"   📊 Status: {status.status}")
            if hasattr(status, "progress") and status.progress:
                print(f"   📈 Progress: {status.progress}")
            if hasattr(status, "message") and status.message:
                print(f"   💬 Message: {status.message}")
            if hasattr(status, "timestamp"):
                print(f"   ⏰ Timestamp: {status.timestamp}")

        documents = client.parse(
            str(advanced_file2),
            progress_callback=detailed_progress_callback,
            poll_interval=1.0,
        )
        print(
            f"   ✅ Success with detailed monitoring! Parsed {len(documents)} document(s)"
        )

        # Example 3: Working with DocumentBatch
        print("\n🔍 Example 3: Working with DocumentBatch")
        documents = client.parse([str(f) for f in test_files])
        print(f"   ✅ Parsed batch of {len(documents)} document(s)")

        # Demonstrate DocumentBatch features
        print("   📊 DocumentBatch Analysis:")
        print(f"      Total documents: {len(documents)}")

        if documents:
            # Show first document details
            first_doc = documents[0]
            print(f"      First document:")
            print(f"         Content length: {len(first_doc.content)} characters")
            print(f"         Content preview: {first_doc.content[:150]}...")

            # Check for metadata
            if hasattr(first_doc, "metadata") and first_doc.metadata:
                print(f"         Metadata keys: {list(first_doc.metadata.keys())}")
                for key, value in list(first_doc.metadata.items())[:3]:  # Show first 3
                    print(f"         {key}: {value}")

            # Check for other attributes
            if hasattr(first_doc, "filename"):
                print(f"         Filename: {first_doc.filename}")
            if hasattr(first_doc, "file_type"):
                print(f"         File type: {first_doc.file_type}")

        # Example 4: Processing mode comparison
        print("\n🔍 Example 4: Processing Mode Comparison")
        file_path = str(advanced_file1)

        # Test different modes
        modes_to_test = [ProcessingMode.DEFAULT, ProcessingMode.FAST]
        results = {}

        for mode in modes_to_test:
            print(f"   Testing {mode.value} mode...")
            start_time = time.time()
            try:
                docs = client.parse(file_path, mode=mode)
                end_time = time.time()
                duration = end_time - start_time
                results[mode.value] = {
                    "documents": len(docs),
                    "duration": duration,
                    "success": True,
                }
                print(f"   ✅ {mode.value}: {len(docs)} docs in {duration:.2f}s")
            except Exception as e:
                results[mode.value] = {"error": str(e), "success": False}
                print(f"   ❌ {mode.value}: {str(e)}")

        # Show comparison
        print("   📊 Mode Comparison Summary:")
        for mode, result in results.items():
            if result["success"]:
                print(
                    f"      {mode}: {result['documents']} docs, {result['duration']:.2f}s"
                )
            else:
                print(f"      {mode}: Failed - {result['error']}")

        # Example 5: Error handling demonstration
        print("\n🔍 Example 5: Error Handling")

        # Test with non-existent file
        print("   Testing with non-existent file...")
        try:
            client.parse("non_existent_file.txt")
        except ValueError as e:
            print(f"   ✅ Caught ValueError as expected: {e}")
        except Exception as e:
            print(f"   ⚠️  Caught unexpected error: {e}")

        # Test with invalid URL
        print("   Testing with invalid URL...")
        try:
            client.parse_urls("not-a-valid-url")
        except ValueError as e:
            print(f"   ✅ Caught ValueError as expected: {e}")
        except LexaError as e:
            print(f"   ✅ Caught LexaError as expected: {e.message}")
        except Exception as e:
            print(f"   ⚠️  Caught unexpected error: {e}")

        # Test with very short timeout
        print("   Testing with very short timeout...")
        try:
            client.parse(str(advanced_file1), timeout=0.1)  # 0.1 second timeout
        except LexaError as e:
            print(f"   ✅ Caught timeout error as expected: {e.message}")
        except Exception as e:
            print(f"   ⚠️  Caught unexpected error: {e}")

    except Exception as e:
        print(f"   ❌ Unexpected error in advanced features: {e}")
    finally:
        # Clean up test files
        for test_file in test_files:
            if test_file.exists():
                test_file.unlink()
        print(f"   🧹 Cleaned up {len(test_files)} test files")


def demonstrate_best_practices(client):
    """Demonstrate best practices for using the Lexa SDK"""
    print("\n" + "=" * 60)
    print("✨ BEST PRACTICES")
    print("=" * 60)

    print("\n📝 Best Practice Examples:")

    # Best Practice 1: Batch processing
    print("\n1️⃣ Batch Processing")
    print("   💡 Process multiple files in a single request for efficiency")

    # Create sample files
    batch_files = []
    for i in range(3):
        file_path = Path(f"batch_file_{i+1}.txt")
        with open(file_path, "w") as f:
            f.write(f"Batch processing example file {i+1}.\n")
            f.write(f"This demonstrates efficient multi-file processing.\n")
            f.write(f"File ID: {i+1}\n")
        batch_files.append(file_path)

    try:
        # Process all files in one batch
        print(f"   Processing {len(batch_files)} files in a single batch...")
        documents = client.parse([str(f) for f in batch_files])
        print(f"   ✅ Batch processed {len(documents)} document(s) efficiently")

        # Best Practice 2: Error handling with retries
        print("\n2️⃣ Proper Error Handling")
        print("   💡 Always handle different types of errors appropriately")

        def safe_parse_with_retry(client, files, max_retries=3):
            """Example of safe parsing with retry logic"""
            for attempt in range(max_retries):
                try:
                    return client.parse(files, timeout=60.0)
                except LexaError as e:
                    if "timeout" in e.message.lower() and attempt < max_retries - 1:
                        print(f"   ⏳ Timeout on attempt {attempt + 1}, retrying...")
                        continue
                    else:
                        print(
                            f"   ❌ Lexa error after {attempt + 1} attempts: {e.message}"
                        )
                        raise
                except ValueError as e:
                    print(f"   ❌ Validation error: {e}")
                    raise
                except Exception as e:
                    print(f"   ❌ Unexpected error: {e}")
                    raise
            return None

        print("   Testing safe parsing function...")
        try:
            docs = safe_parse_with_retry(client, str(batch_files[0]))
            print(f"   ✅ Safe parsing succeeded: {len(docs)} document(s)")
        except Exception as e:
            print(f"   ❌ Safe parsing failed: {e}")

        # Best Practice 3: Progress monitoring for long operations
        print("\n3️⃣ Progress Monitoring")
        print("   💡 Use progress callbacks for long-running operations")

        def production_progress_callback(status):
            """Production-ready progress callback with logging"""
            status_msg = f"Job {status.status}"
            if hasattr(status, "progress") and status.progress:
                status_msg += f" ({status.progress})"
            print(f"   📊 {status_msg}")

            # In production, you might log this or update a UI
            # logger.info(f"Parsing job status: {status_msg}")

        print("   Processing with production-style progress monitoring...")
        docs = client.parse(
            str(batch_files[1]),
            progress_callback=production_progress_callback,
            timeout=120.0,
            poll_interval=5.0,  # Check every 5 seconds
        )
        print(f"   ✅ Monitored processing completed: {len(docs)} document(s)")

        # Best Practice 4: Choosing the right processing mode
        print("\n4️⃣ Processing Mode Selection")
        print("   💡 Choose processing modes based on your needs")
        print("      - DEFAULT: Balanced speed and accuracy")
        print("      - FAST: Quick processing for simple documents")
        print("      - DETAILED: Thorough analysis for complex documents")

        # Best Practice 5: Resource management
        print("\n5️⃣ Resource Management")
        print("   💡 Clean up resources and handle large datasets efficiently")
        print("   💡 Use appropriate timeouts for different file sizes")
        print("   💡 Consider processing limits and rate limiting")

        # Show file size recommendations
        file_size = batch_files[0].stat().st_size
        print(f"   Example file size: {file_size} bytes")
        if file_size < 1024 * 1024:  # Less than 1MB
            print("   📝 Recommendation: Use FAST mode for small text files")
        elif file_size < 10 * 1024 * 1024:  # Less than 10MB
            print("   📝 Recommendation: Use DEFAULT mode with 60s timeout")
        else:
            print("   📝 Recommendation: Use longer timeout and progress monitoring")

    finally:
        # Clean up batch files
        for file_path in batch_files:
            if file_path.exists():
                file_path.unlink()
        print(f"   🧹 Cleaned up {len(batch_files)} batch files")


def main():
    print("🔧 Cerevox SDK - Comprehensive Lexa Examples")
    print("=" * 60)

    # Initialize the client
    try:
        client = Lexa(
            api_key="your-api-key",  # Or set CEREVOX_API_KEY env var
        )
        print("✅ Lexa client initialized successfully")
    except ValueError as e:
        print(f"❌ Failed to initialize client: {e}")
        print("💡 Make sure to set CEREVOX_API_KEY environment variable")
        return

    # Run basic parsing demonstrations
    demonstrate_basic_parsing(client)

    # Run URL parsing demonstrations
    demonstrate_url_parsing(client)

    # Run cloud storage demonstrations
    demonstrate_s3_integration(client)
    demonstrate_box_integration(client)
    demonstrate_dropbox_integration(client)
    demonstrate_sharepoint_integration(client)
    demonstrate_salesforce_integration(client)
    demonstrate_sendme_integration(client)

    # Advanced features and best practices
    demonstrate_advanced_features(client)
    demonstrate_best_practices(client)

    print("\n🎉 ALL EXAMPLES COMPLETED! 🎉")
    print("=" * 60)
    print("📚 Summary of what was demonstrated:")
    print("   ✅ Basic file parsing (single & multiple files)")
    print("   ✅ URL parsing")
    print("   ✅ Cloud storage integrations (S3, Box, Dropbox, SharePoint, Salesforce)")
    print("   ✅ Sendme integration")
    print("   ✅ Advanced features (timeouts, progress monitoring, error handling)")
    print("   ✅ Best practices for production use")
    print("   ✅ DocumentBatch processing")
    print("   ✅ Processing mode comparisons")
    print("\n💡 Next steps:")
    print("   1. Set up your cloud storage integrations")
    print("   2. Configure your API key")
    print("   3. Start parsing your own documents!")
    print("   4. Check the documentation for more advanced features")
    print("\n🔗 For more information, visit: https://docs.cerevox.ai")


if __name__ == "__main__":
    main()
