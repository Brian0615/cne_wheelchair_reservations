import os
from unittest import TestCase
from unittest.mock import patch

import boto3
from moto import mock_aws

from api.src.s3_service import S3Service


@mock_aws
class TestS3Service(TestCase):
    """Tests for S3Service upload and download operations."""

    BUCKET = "test-bucket"

    def setUp(self):
        self.s3_client = boto3.client("s3", region_name="us-east-1")
        self.s3_client.create_bucket(Bucket=self.BUCKET)
        with patch.dict(os.environ, {
            "AWS_ACCESS_KEY_ID": "test",
            "AWS_SECRET_ACCESS_KEY": "test",
            "S3_BUCKET": self.BUCKET,
            "CNE_YEAR": "2025",
        }):
            self.service = S3Service()
            self.service.bucket = self.BUCKET

    def test_get_form_path_prod_mode(self):
        with patch.dict(os.environ, {"DEV_MODE": "false", "CNE_YEAR": "2025"}):
            path = S3Service._get_form_path("W0820001")
        self.assertEqual("completed_forms_2025/rental_form_W0820001.pdf", path)

    def test_get_form_path_dev_mode(self):
        with patch.dict(os.environ, {"DEV_MODE": "true", "CNE_YEAR": "2025"}):
            path = S3Service._get_form_path("W0820001")
        self.assertEqual("completed_forms_2025_test/rental_form_W0820001.pdf", path)

    def test_upload_and_download_rental_form(self):
        pdf_content = b"%PDF-test-content"
        with patch.dict(os.environ, {"DEV_MODE": "false", "CNE_YEAR": "2025"}):
            self.service.upload_rental_form(pdf_bytes=pdf_content, rental_id="W0820001")
            result = self.service.download_rental_form(rental_id="W0820001")
        self.assertEqual(pdf_content, result)

    def test_download_missing_form_raises_file_not_found(self):
        with patch.dict(os.environ, {"DEV_MODE": "false", "CNE_YEAR": "2025"}):
            with self.assertRaises(FileNotFoundError):
                self.service.download_rental_form(rental_id="W9999999")
