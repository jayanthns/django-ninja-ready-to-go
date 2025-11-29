import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase


class FilesAppTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_upload_linear_csv(self):
        content = b"name,age\nAlice,30\nBob,25"
        file = SimpleUploadedFile("test.csv", content, content_type="text/csv")
        response = self.client.post("/api/v1/files/upload/linear", {"file": file})
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        data = json_response["data"]
        self.assertEqual(len(data["preview_rows"]), 2)
        self.assertEqual(data["preview_rows"][0]["name"], "Alice")

    def test_upload_linear_json(self):
        content = json.dumps([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]).encode("utf-8")
        file = SimpleUploadedFile("test.json", content, content_type="application/json")
        response = self.client.post("/api/v1/files/upload/linear", {"file": file})
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        data = json_response["data"]
        self.assertEqual(len(data["preview_rows"]), 2)

    def test_upload_too_large(self):
        # 26KB file (limit is 25KB)
        content = b"a" * (26 * 1024)
        file = SimpleUploadedFile("large.txt", content, content_type="text/plain")
        response = self.client.post("/api/v1/files/upload/generic", {"file": file})
        self.assertEqual(response.status_code, 400)

        # Verify standard error structure
        json_response = response.json()
        self.assertIsNone(json_response["data"])
        self.assertIn("error", json_response)
        self.assertIn("message", json_response["error"])
        self.assertIn("File size exceeds the limit", json_response["error"]["message"])

    def test_download_file(self):
        response = self.client.get("/api/v1/files/download/test.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="test.txt"')

    def test_stream_file(self):
        response = self.client.get("/api/v1/files/stream/test.txt")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
