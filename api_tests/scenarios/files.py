from api_tests.client import APIClient


def run(client: APIClient):
    print("Running File Scenarios...")

    # 1. Upload Linear File (CSV)
    print("  - Uploading CSV...")
    files = {"file": ("test.csv", "name,age\nAlice,30\nBob,25", "text/csv")}
    resp = client.post("/api/v1/files/upload/linear", files=files)
    assert resp.status_code == 200, f"Upload CSV failed: {resp.text}"
    data = resp.json()["data"]
    assert data["filename"] == "test.csv"
    assert data["total_rows"] == 2

    # 2. Upload Generic File
    print("  - Uploading Generic File...")
    files = {"file": ("test.txt", "Hello World", "text/plain")}
    resp = client.post("/api/v1/files/upload/generic", files=files)
    assert resp.status_code == 200, f"Upload generic failed: {resp.text}"

    # 3. Download File
    print("  - Downloading File...")
    resp = client.get("/api/v1/files/download/test_dl.txt")
    assert resp.status_code == 200, f"Download failed: {resp.status_code}"

    print("File Scenarios Passed.")
