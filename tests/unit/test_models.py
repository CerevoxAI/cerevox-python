"""
Tests for cerevox.core.models

Comprehensive tests to achieve 100% code coverage for the models,
including all methods, error handling, and edge cases.
"""

from io import BytesIO, StringIO
from pathlib import Path

import pytest
from pydantic import ValidationError

from cerevox.core import (
    VALID_MODES,
    BucketInfo,
    BucketListResponse,
    DriveInfo,
    DriveListResponse,
    FileContentInput,
    FileInfo,
    FileInput,
    FilePathInput,
    FileStreamInput,
    FileURLInput,
    FolderInfo,
    FolderListResponse,
    IngestionResult,
    JobResponse,
    JobStatus,
    ProcessingMode,
    SiteInfo,
    SiteListResponse,
)


class TestEnums:
    """Test enum classes and their values"""

    def test_job_status_enum_values(self):
        """Test all JobStatus enum values"""
        assert JobStatus.COMPLETE == "complete"
        assert JobStatus.FAILED == "failed"
        assert JobStatus.INTERNAL_ERROR == "internal_error"
        assert JobStatus.NOT_FOUND == "not_found"
        assert JobStatus.PARTIAL_SUCCESS == "partial_success"
        assert JobStatus.PROCESSING == "processing"

    def test_processing_mode_enum_values(self):
        """Test all ProcessingMode enum values"""
        assert ProcessingMode.ADVANCED == "advanced"
        assert ProcessingMode.DEFAULT == "default"

    def test_valid_modes_constant(self):
        """Test VALID_MODES constant contains all ProcessingMode values"""
        assert VALID_MODES == ["advanced", "default"]
        assert len(VALID_MODES) == 2
        for mode in ProcessingMode:
            assert mode.value in VALID_MODES


class TestBucketInfo:
    """Test BucketInfo model"""

    def test_bucket_info_creation_with_field_names(self):
        """Test creating BucketInfo with standard field names"""
        bucket = BucketInfo(name="test-bucket", creation_date="2023-01-01T00:00:00Z")
        assert bucket.name == "test-bucket"
        assert bucket.creation_date == "2023-01-01T00:00:00Z"

    def test_bucket_info_creation_with_aliases(self):
        """Test creating BucketInfo with field aliases"""
        bucket = BucketInfo(Name="test-bucket", CreationDate="2023-01-01T00:00:00Z")
        assert bucket.name == "test-bucket"
        assert bucket.creation_date == "2023-01-01T00:00:00Z"

    def test_bucket_info_mixed_fields_and_aliases(self):
        """Test creating BucketInfo with mixed field names and aliases"""
        bucket = BucketInfo(Name="test-bucket", creation_date="2023-01-01T00:00:00Z")
        assert bucket.name == "test-bucket"
        assert bucket.creation_date == "2023-01-01T00:00:00Z"

    def test_bucket_info_validation_error(self):
        """Test BucketInfo validation with missing required fields"""
        with pytest.raises(ValidationError) as excinfo:
            BucketInfo(name="test-bucket")  # Missing creation_date
        assert "CreationDate" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            BucketInfo(creation_date="2023-01-01T00:00:00Z")  # Missing name
        assert "Name" in str(excinfo.value)


class TestBucketListResponse:
    """Test BucketListResponse model"""

    def test_bucket_list_response_creation(self):
        """Test creating BucketListResponse"""
        buckets = [
            BucketInfo(name="bucket1", creation_date="2023-01-01T00:00:00Z"),
            BucketInfo(name="bucket2", creation_date="2023-01-02T00:00:00Z"),
        ]
        response = BucketListResponse(request_id="req123", buckets=buckets)
        assert response.request_id == "req123"
        assert len(response.buckets) == 2
        assert response.buckets[0].name == "bucket1"

    def test_bucket_list_response_with_aliases(self):
        """Test creating BucketListResponse with aliases"""
        buckets = [BucketInfo(name="bucket1", creation_date="2023-01-01T00:00:00Z")]
        response = BucketListResponse(requestID="req123", buckets=buckets)
        assert response.request_id == "req123"

    def test_bucket_list_response_empty_buckets(self):
        """Test BucketListResponse with empty bucket list"""
        response = BucketListResponse(request_id="req123", buckets=[])
        assert response.request_id == "req123"
        assert len(response.buckets) == 0


class TestDriveInfo:
    """Test DriveInfo model"""

    def test_drive_info_creation(self):
        """Test creating DriveInfo"""
        drive = DriveInfo(id="drive123", name="Test Drive", drive_type="business")
        assert drive.id == "drive123"
        assert drive.name == "Test Drive"
        assert drive.drive_type == "business"

    def test_drive_info_with_alias(self):
        """Test creating DriveInfo with alias"""
        drive = DriveInfo(id="drive123", name="Test Drive", driveType="business")
        assert drive.drive_type == "business"

    def test_drive_info_validation_error(self):
        """Test DriveInfo validation with missing fields"""
        with pytest.raises(ValidationError):
            DriveInfo(id="drive123", name="Test Drive")  # Missing drive_type


class TestDriveListResponse:
    """Test DriveListResponse model"""

    def test_drive_list_response_creation(self):
        """Test creating DriveListResponse"""
        drives = [
            DriveInfo(id="drive1", name="Drive 1", drive_type="business"),
            DriveInfo(id="drive2", name="Drive 2", drive_type="personal"),
        ]
        response = DriveListResponse(request_id="req123", drives=drives)
        assert response.request_id == "req123"
        assert len(response.drives) == 2

    def test_drive_list_response_with_alias(self):
        """Test creating DriveListResponse with alias"""
        drives = [DriveInfo(id="drive1", name="Drive 1", drive_type="business")]
        response = DriveListResponse(requestID="req123", drives=drives)
        assert response.request_id == "req123"


class TestFileInfo:
    """Test FileInfo model"""

    def test_file_info_creation(self):
        """Test creating FileInfo"""
        file_info = FileInfo(
            name="test.pdf", url="https://example.com/test.pdf", type="application/pdf"
        )
        assert file_info.name == "test.pdf"
        assert file_info.url == "https://example.com/test.pdf"
        assert file_info.type == "application/pdf"

    def test_file_info_validation_error(self):
        """Test FileInfo validation with missing fields"""
        with pytest.raises(ValidationError):
            FileInfo(
                name="test.pdf", url="https://example.com/test.pdf"
            )  # Missing type


class TestFolderInfo:
    """Test FolderInfo model"""

    def test_folder_info_creation_with_path(self):
        """Test creating FolderInfo with path"""
        folder = FolderInfo(id="folder123", name="Test Folder", path="/root/test")
        assert folder.id == "folder123"
        assert folder.name == "Test Folder"
        assert folder.path == "/root/test"

    def test_folder_info_creation_without_path(self):
        """Test creating FolderInfo without path (optional field)"""
        folder = FolderInfo(id="folder123", name="Test Folder")
        assert folder.id == "folder123"
        assert folder.name == "Test Folder"
        assert folder.path is None

    def test_folder_info_validation_error(self):
        """Test FolderInfo validation with missing required fields"""
        with pytest.raises(ValidationError):
            FolderInfo(id="folder123")  # Missing name


class TestFolderListResponse:
    """Test FolderListResponse model"""

    def test_folder_list_response_creation(self):
        """Test creating FolderListResponse"""
        folders = [
            FolderInfo(id="folder1", name="Folder 1", path="/root/folder1"),
            FolderInfo(id="folder2", name="Folder 2"),
        ]
        response = FolderListResponse(request_id="req123", folders=folders)
        assert response.request_id == "req123"
        assert len(response.folders) == 2

    def test_folder_list_response_with_alias(self):
        """Test creating FolderListResponse with alias"""
        folders = [FolderInfo(id="folder1", name="Folder 1")]
        response = FolderListResponse(requestID="req123", folders=folders)
        assert response.request_id == "req123"


class TestIngestionResult:
    """Test IngestionResult model"""

    def test_ingestion_result_minimal(self):
        """Test creating IngestionResult with minimal required fields"""
        result = IngestionResult(message="Success", request_id="req123")
        assert result.message == "Success"
        assert result.request_id == "req123"
        assert result.pages is None
        assert result.rejects is None
        assert result.uploads is None

    def test_ingestion_result_complete(self):
        """Test creating IngestionResult with all fields"""
        result = IngestionResult(
            message="Success",
            request_id="req123",
            pages=10,
            rejects=["bad_file.txt"],
            uploads=["good_file.pdf", "another_file.docx"],
        )
        assert result.message == "Success"
        assert result.request_id == "req123"
        assert result.pages == 10
        assert result.rejects == ["bad_file.txt"]
        assert result.uploads == ["good_file.pdf", "another_file.docx"]

    def test_ingestion_result_with_alias(self):
        """Test creating IngestionResult with alias"""
        result = IngestionResult(message="Success", requestID="req123")
        assert result.request_id == "req123"


class TestJobResponse:
    """Test JobResponse model"""

    def test_job_response_minimal(self):
        """Test creating JobResponse with minimal required fields"""
        job = JobResponse(status=JobStatus.PROCESSING, request_id="req123")
        assert job.status == JobStatus.PROCESSING
        assert job.request_id == "req123"
        assert job.age_seconds is None
        assert job.progress is None
        assert job.created_at is None
        assert job.completed_chunks is None
        assert job.failed_chunks is None
        assert job.processing_chunks is None
        assert job.total_chunks is None
        assert job.total_files is None
        assert job.completed_files is None
        assert job.failed_files is None
        assert job.processing_files is None
        assert job.files is None
        assert job.errors is None
        assert job.error_count is None
        assert job.message is None
        assert job.processed_files is None
        assert job.result is None
        assert job.results is None
        assert job.error is None

    def test_job_response_complete(self):
        """Test creating JobResponse with all fields"""
        job = JobResponse(
            status=JobStatus.COMPLETE,
            request_id="req123",
            progress=100,
            message="Job completed successfully",
            processed_files=5,
            total_files=5,
            result={"key": "value"},
            results=[{"file1": "result1"}, {"file2": "result2"}],
            error=None,
        )
        assert job.status == JobStatus.COMPLETE
        assert job.progress == 100
        assert job.message == "Job completed successfully"
        assert job.processed_files == 5
        assert job.total_files == 5
        assert job.result == {"key": "value"}
        assert len(job.results) == 2
        assert job.error is None

    def test_job_response_failed(self):
        """Test creating JobResponse with failed status and error"""
        job = JobResponse(
            status=JobStatus.FAILED,
            request_id="req123",
            progress=50,
            message="Job failed",
            error="Something went wrong",
        )
        assert job.status == JobStatus.FAILED
        assert job.error == "Something went wrong"

    def test_job_response_with_alias(self):
        """Test creating JobResponse with alias"""
        job = JobResponse(status=JobStatus.PROCESSING, requestID="req123")
        assert job.request_id == "req123"

    def test_job_response_all_statuses(self):
        """Test JobResponse with all possible status values"""
        for status in JobStatus:
            job = JobResponse(status=status, request_id="req123")
            assert job.status == status

    def test_job_response_validation_error(self):
        """Test JobResponse validation with missing required fields"""
        with pytest.raises(ValidationError):
            JobResponse(status=JobStatus.PROCESSING)  # Missing request_id


class TestSiteInfo:
    """Test SiteInfo model"""

    def test_site_info_creation(self):
        """Test creating SiteInfo"""
        site = SiteInfo(
            id="site123",
            name="Test Site",
            web_url="https://example.sharepoint.com/sites/test",
        )
        assert site.id == "site123"
        assert site.name == "Test Site"
        assert site.web_url == "https://example.sharepoint.com/sites/test"

    def test_site_info_with_alias(self):
        """Test creating SiteInfo with alias"""
        site = SiteInfo(
            id="site123",
            name="Test Site",
            webUrl="https://example.sharepoint.com/sites/test",
        )
        assert site.web_url == "https://example.sharepoint.com/sites/test"

    def test_site_info_validation_error(self):
        """Test SiteInfo validation with missing fields"""
        with pytest.raises(ValidationError):
            SiteInfo(id="site123", name="Test Site")  # Missing web_url


class TestSiteListResponse:
    """Test SiteListResponse model"""

    def test_site_list_response_creation(self):
        """Test creating SiteListResponse"""
        sites = [
            SiteInfo(id="site1", name="Site 1", web_url="https://example.com/site1"),
            SiteInfo(id="site2", name="Site 2", web_url="https://example.com/site2"),
        ]
        response = SiteListResponse(request_id="req123", sites=sites)
        assert response.request_id == "req123"
        assert len(response.sites) == 2

    def test_site_list_response_with_alias(self):
        """Test creating SiteListResponse with alias"""
        sites = [
            SiteInfo(id="site1", name="Site 1", web_url="https://example.com/site1")
        ]
        response = SiteListResponse(requestID="req123", sites=sites)
        assert response.request_id == "req123"

    def test_site_list_response_empty_sites(self):
        """Test SiteListResponse with empty sites list"""
        response = SiteListResponse(request_id="req123", sites=[])
        assert response.request_id == "req123"
        assert len(response.sites) == 0


class TestModelConfigPopulateByName:
    """Test that all models support populate_by_name configuration"""

    def test_all_models_populate_by_name(self):
        """Test that all models with aliases support populate_by_name"""
        # Test BucketInfo
        bucket_data = {"Name": "test", "CreationDate": "2023-01-01"}
        bucket = BucketInfo(**bucket_data)
        assert bucket.name == "test"

        # Test BucketListResponse
        bucket_list_data = {"requestID": "req123", "buckets": [bucket_data]}
        response = BucketListResponse(**bucket_list_data)
        assert response.request_id == "req123"

        # Test DriveInfo
        drive_data = {"id": "drive1", "name": "Drive", "driveType": "business"}
        drive = DriveInfo(**drive_data)
        assert drive.drive_type == "business"

        # Test other models with aliases
        folder_data = {"requestID": "req123", "folders": []}
        folder_response = FolderListResponse(**folder_data)
        assert folder_response.request_id == "req123"

        ingestion_data = {"message": "Success", "requestID": "req123"}
        ingestion = IngestionResult(**ingestion_data)
        assert ingestion.request_id == "req123"

        job_data = {"status": "processing", "requestID": "req123"}
        job = JobResponse(**job_data)
        assert job.request_id == "req123"

        site_data = {"id": "site1", "name": "Site", "webUrl": "https://example.com"}
        site = SiteInfo(**site_data)
        assert site.web_url == "https://example.com"


class TestTypeAliases:
    """Test type aliases are properly defined"""

    def test_file_input_types_exist(self):
        """Test that all file input type aliases exist"""
        # These should not raise NameError
        assert FileURLInput == str
        assert FilePathInput  # Union type
        assert FileContentInput  # Union type
        assert FileStreamInput  # Union type
        assert FileInput  # Union type

    def test_file_input_type_compatibility(self):
        """Test file input types accept expected values"""
        # FileURLInput (str)
        url: FileURLInput = "https://example.com/file.pdf"
        assert isinstance(url, str)

        # FilePathInput (Path or str)
        path_str: FilePathInput = "/path/to/file.pdf"
        path_obj: FilePathInput = Path("/path/to/file.pdf")
        assert isinstance(path_str, str)
        assert isinstance(path_obj, Path)

        # FileContentInput (bytes or bytearray)
        content_bytes: FileContentInput = b"file content"
        content_bytearray: FileContentInput = bytearray(b"file content")
        assert isinstance(content_bytes, bytes)
        assert isinstance(content_bytearray, bytearray)

        # FileStreamInput (various IO types)
        stream_bytes: FileStreamInput = BytesIO(b"content")
        stream_str: FileStreamInput = StringIO("content")
        assert hasattr(stream_bytes, "read")
        assert hasattr(stream_str, "read")


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_string_fields(self):
        """Test models with empty string values"""
        bucket = BucketInfo(name="", creation_date="")
        assert bucket.name == ""
        assert bucket.creation_date == ""

    def test_very_long_strings(self):
        """Test models with very long string values"""
        long_string = "a" * 1000
        bucket = BucketInfo(name=long_string, creation_date=long_string)
        assert len(bucket.name) == 1000
        assert len(bucket.creation_date) == 1000

    def test_special_characters_in_strings(self):
        """Test models with special characters"""
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        bucket = BucketInfo(name=special_chars, creation_date="2023-01-01")
        assert bucket.name == special_chars

    def test_unicode_characters(self):
        """Test models with unicode characters"""
        unicode_string = "测试文件夹 🚀 émojis"
        folder = FolderInfo(id="test", name=unicode_string)
        assert folder.name == unicode_string

    def test_large_numbers(self):
        """Test models with large numeric values"""
        job = JobResponse(
            status=JobStatus.PROCESSING,
            request_id="req123",
            progress=999999,
            processed_files=1000000,
            total_files=2000000,
        )
        assert job.progress == 999999
        assert job.processed_files == 1000000
        assert job.total_files == 2000000

    def test_negative_numbers(self):
        """Test models with negative numbers"""
        job = JobResponse(status=JobStatus.PROCESSING, request_id="req123", progress=-1)
        assert job.progress == -1

    def test_complex_nested_data(self):
        """Test models with complex nested data structures"""
        complex_result = {
            "nested": {
                "deeply": {"nested": {"data": ["item1", "item2", {"key": "value"}]}}
            },
            "list": [1, 2, 3, {"nested_in_list": True}],
        }

        job = JobResponse(
            status=JobStatus.COMPLETE, request_id="req123", result=complex_result
        )
        assert job.result["nested"]["deeply"]["nested"]["data"][2]["key"] == "value"
        assert job.result["list"][3]["nested_in_list"] is True
