import logging
import os
import unittest
from unittest.mock import patch

from botocore.exceptions import ClientError

from app.main import lambda_handler

logging.basicConfig(level=logging.INFO)


class TestLambdaHandler(unittest.TestCase):
    def setUp(self):
        os.environ["SOURCE_BUCKET"] = "source-bucket"
        os.environ["DESTINATION_BUCKET"] = "destination-bucket"

    @patch("app.main.s3")
    def test_file_exists_and_processed_successfully(self, mock_s3):
        event = {"detail": {"object": {"key": "test_file.txt"}}}
        mock_s3.download_file.return_value = None
        mock_s3.upload_file.return_value = None

        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("decrypted and uploaded successfully", response["body"])
        mock_s3.download_file.assert_called_once_with(
            "source-bucket", "test_file.txt", "/tmp/test_file.txt"
        )
        mock_s3.upload_file.assert_called_once_with(
            "/tmp/test_file.txt", "destination-bucket", "test_file.txt"
        )

    @patch("app.main.s3")
    def test_file_no_longer_exists(self, mock_s3):
        event = {"detail": {"object": {"key": "non_existent_file.txt"}}}
        error_response = {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist.",
            }
        }
        mock_s3.download_file.side_effect = ClientError(error_response, "DownloadFile")

        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 404)
        self.assertIn("does not exist", response["body"])
        mock_s3.download_file.assert_called_once()

    @patch("app.main.s3")
    def test_unexpected_error_during_download(self, mock_s3):
        event = {"detail": {"object": {"key": "test_file.txt"}}}
        error_response = {
            "Error": {"Code": "UnhandledException", "Message": "UnhandledException"}
        }
        mock_s3.download_file.side_effect = ClientError(error_response, "DownloadFile")

        with self.assertRaises(ClientError):
            lambda_handler(event, None)

        mock_s3.download_file.assert_called_once()


if __name__ == "__main__":
    unittest.main()
