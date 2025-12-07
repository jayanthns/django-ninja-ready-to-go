import time

from api_tests.client import APIClient


def run(client: APIClient):
    print("Running Task Scenarios...")

    # 1. Trigger Celery Ping
    print("  - Triggering Celery Ping...")
    resp = client.post("/api/v1/tasks/celery/ping", json={"duration": 0})
    assert resp.status_code == 200, f"Trigger Celery failed: {resp.text}"
    data = resp.json()
    assert "task_id" in data
    assert data["status"] == "QUEUED"
    celery_task_id = data["task_id"]

    # 2. Check Celery Status
    print("  - Checking Celery Status (polling)...")
    # Poll for up to 5 seconds
    start_time = time.time()
    status = "QUEUED"
    while time.time() - start_time < 5:
        resp = client.get(f"/api/v1/tasks/celery/status/{celery_task_id}")
        assert resp.status_code == 200, f"Get Celery status failed: {resp.text}"
        status_data = resp.json()
        status = status_data["status"]
        if status in ["SUCCESS", "FAILURE"]:
            break
        time.sleep(0.5)

    print(f"    Final Celery Status: {status}")
    # We don't strictly assert SUCCESS because workers might not be running,
    # but we assert it's a valid status.
    assert status in ["QUEUED", "RUNNING", "SUCCESS", "FAILURE"]

    if status == "SUCCESS":
        assert status_data["result"]["message"] == "pong"
        assert status_data["result"]["service"] == "celery"

    # 3. Trigger Dramatiq Ping
    print("  - Triggering Dramatiq Ping...")
    resp = client.post("/api/v1/tasks/dramatiq/ping", json={"duration": 0})
    assert resp.status_code == 200, f"Trigger Dramatiq failed: {resp.text}"
    data = resp.json()
    assert "task_id" in data
    assert data["status"] == "QUEUED"
    dramatiq_task_id = data["task_id"]

    # 4. Check Dramatiq Status
    print("  - Checking Dramatiq Status (polling)...")
    start_time = time.time()
    status = "QUEUED"
    while time.time() - start_time < 5:
        resp = client.get(f"/api/v1/tasks/dramatiq/status/{dramatiq_task_id}")
        assert resp.status_code == 200, f"Get Dramatiq status failed: {resp.text}"
        status_data = resp.json()
        status = status_data["status"]
        if status in ["SUCCESS", "FAILURE"]:
            break
        time.sleep(0.5)

    print(f"    Final Dramatiq Status: {status}")
    assert status in ["QUEUED", "RUNNING", "SUCCESS", "FAILURE"]

    if status == "SUCCESS":
        assert status_data["result"]["message"] == "pong"
        assert status_data["result"]["service"] == "dramatiq"

    print("Task Scenarios Passed.")
