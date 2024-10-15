"""
AWS Lambda function to decrypt files uploaded to an S3 bucket and upload them to another bucket.

This script defines a Lambda function that listens for EventBridge events indicating that a new
object has been uploaded to a source S3 bucket. It then downloads the encrypted file, decrypts it,
and uploads the decrypted file to a destination S3 bucket.

Environment Variables:
- SOURCE_BUCKET: str
    The name of the source S3 bucket containing encrypted files.
- DESTINATION_BUCKET: str
    The name of the destination S3 bucket where decrypted files will be uploaded.
"""

import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")


def lambda_handler(event, context):
    """
    AWS Lambda function to decrypt files uploaded to an S3 bucket.

    This function is triggered by an EventBridge event when a new object is created in the source S3 bucket.
    It downloads the encrypted file, decrypts it, and uploads the decrypted file to the destination S3 bucket.
    If the file no longer exists by the time the function runs, it handles the error gracefully.

    Parameters:
    - event (dict): Event data passed to this function by the lambda call
    - context (object): Additional runtime information

    Returns:
    - dict: Contains the status code and a message indicating the result.
    """
    logger.info(f"Received event: {event}")

    source_bucket = os.environ["SOURCE_BUCKET"]
    dest_bucket = os.environ["DESTINATION_BUCKET"]

    if not source_bucket or not dest_bucket:
        logger.error(
            "Environment variables SOURCE_BUCKET or DESTINATION_BUCKET are not set."
        )
        return {"statusCode": 500, "body": "Server configuration error."}

    s3_obj_key = event["detail"]["object"]["key"]
    encrypted_file = f"/tmp/{os.path.basename(s3_obj_key)}"

    try:
        s3.download_file(source_bucket, s3_obj_key, encrypted_file)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            logger.warning(
                f"File '{s3_obj_key}' does not exist. It may have been deleted before processing."
            )
            return {
                "statusCode": 404,
                "body": f"File '{s3_obj_key}' does not exist. It may have been deleted before processing.",
            }
        else:
            logger.error(f"Failed to download file '{s3_obj_key}': {e}")
            raise e

    decrypted_file = decrypt(encrypted_file)

    try:
        logger.info(f"Uploading decrypted file: {s3_obj_key}")
        s3.upload_file(decrypted_file, dest_bucket, s3_obj_key)
    except ClientError as e:
        logger.error(
            f"Failed to upload file '{s3_obj_key}' to bucket '{dest_bucket}': {e}"
        )
        raise e

    logger.info(f"Successfully processed file: {s3_obj_key}")
    return {
        "statusCode": 200,
        "body": f"File '{s3_obj_key}' decrypted and uploaded successfully.",
    }


def decrypt(file_path):
    """
    Placeholder function for decrypting a file.

    Parameters:
    - file_path (str): The path to the encrypted file.

    Returns:
    - str: The path to the decrypted file.
    """
    return file_path
