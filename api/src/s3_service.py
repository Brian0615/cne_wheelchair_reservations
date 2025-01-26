import os
from typing import Optional

import boto3


class S3Service:
    """Service class to interact with AWS S3"""

    def __init__(self):
        self.s3_client = boto3.client("s3")
        self.bucket = os.environ["S3_BUCKET"]

    def upload_rental_form(self, pdf_bytes: bytes, rental_id: str):
        """Upload a rental form to S3"""
        key = f'completed_forms_{os.environ["CNE_YEAR"]}/rental_form_{rental_id}.pdf'
        self.s3_client.put_object(Bucket=self.bucket, Key=key, Body=pdf_bytes)

    def download_rental_form(self, rental_id: str) -> Optional[bytes]:
        """Download a rental form from S3, raise Exception if not found"""
        key = f'completed_forms_{os.environ["CNE_YEAR"]}/rental_form_{rental_id}.pdf'
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except self.s3_client.exceptions.NoSuchKey as exc:
            raise FileNotFoundError(f"Rental form not found for rental ID {rental_id}") from exc
