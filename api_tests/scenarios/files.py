from api_tests.client import APIClient


def run(client: APIClient):
    print("Running File Scenarios...")

    from api_tests.assertions import assert_structure

    linear_response_structure = {
        "data": {"message": str, "filename": str, "total_rows": int, "preview_rows": list},
        "trace_id": str,
        "error": (dict, type(None)),
    }

    generic_response_structure = {
        "data": {"message": str, "filename": str, "size": int, "human_readable_size": str},
        "trace_id": str,
        "error": (dict, type(None)),
    }

    # 1. Upload Linear File (CSV)
    print("  - Uploading CSV...")
    files = {"file": ("test.csv", "name,age\nAlice,30\nBob,25", "text/csv")}
    resp = client.post("/api/v1/files/upload/linear", files=files)
    assert resp.status_code == 200, f"Upload CSV failed: {resp.text}"

    data = resp.json()
    assert_structure(data, linear_response_structure, path="upload_linear_response")
    assert data["data"]["filename"] == "test.csv"
    assert data["data"]["total_rows"] == 2

    # 2. Upload Generic File
    print("  - Uploading Generic File...")
    files = {"file": ("test.txt", "Hello World", "text/plain")}
    resp = client.post("/api/v1/files/upload/generic", files=files)
    assert resp.status_code == 200, f"Upload generic failed: {resp.text}"

    data = resp.json()
    assert_structure(data, generic_response_structure, path="upload_generic_response")

    # 3. Download File
    print("  - Downloading File...")
    resp = client.get("/api/v1/files/download/test_dl.txt")
    assert resp.status_code == 200, f"Download failed: {resp.status_code}"
    # Download returns raw content, so no structure check needed for JSON.

    print("File Scenarios Passed.")
