import os
from typing import Optional

import boto3
import botocore

from common.logger import initialize_logger
from common.utils import read_secret

logger = initialize_logger()


class S3Service:
    """Service class to interact with AWS S3"""

    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=read_secret(os.environ["AWS_ACCESS_KEY_ID"]),
            aws_secret_access_key=read_secret(os.environ["AWS_SECRET_ACCESS_KEY"]),
        )
        self.bucket = os.environ["S3_BUCKET"]

    @staticmethod
    def _get_form_path(rental_id: str) -> str:
        """Get the S3 key for a rental form based on rental ID"""
        form_folder = f"completed_forms_{os.environ['CNE_YEAR']}"
        if os.getenv("DEV_MODE", "False").lower() == "true":
            form_folder += "_test"

        return os.path.join(form_folder, f"rental_form_{rental_id}.pdf")

    def upload_rental_form(self, pdf_bytes: bytes, rental_id: str):
        """Upload a rental form to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket, Key=self._get_form_path(rental_id=rental_id), Body=pdf_bytes
            )
        except botocore.exceptions.ClientError:
            logger.exception("Failed to upload rental form to S3", extra={"rental_id": rental_id})
            raise
        logger.info("Rental form uploaded", extra={"rental_id": rental_id})

    def download_rental_form(self, rental_id: str) -> Optional[bytes]:
        """Download a rental form from S3, raise Exception if not found"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=self._get_form_path(rental_id=rental_id))
            return response["Body"].read()
        except self.s3_client.exceptions.NoSuchKey as exc:
            logger.warning("Rental form not found in S3", extra={"rental_id": rental_id})
            raise FileNotFoundError(f"Rental form not found for rental ID {rental_id}") from exc
        except botocore.exceptions.ClientError:
            logger.exception("Failed to download rental form from S3", extra={"rental_id": rental_id})
            raise
