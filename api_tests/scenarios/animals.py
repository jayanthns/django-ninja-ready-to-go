from api_tests.client import APIClient


def run(client: APIClient):
    print("Running Animal Scenarios...")

    # 1. Create Animal
    print("  - Creating animal...")
    create_payload = {"name": "Simba", "species": "Lion", "age": 5}
    resp = client.post("/api/v1/animals/", json=create_payload)
    assert resp.status_code == 200, f"Create animal failed: {resp.text}"
    # Create returns wrapped response
    animal_id = resp.json()["data"]["id"]

    # 2. List Animals
    print("  - Listing animals...")
    resp = client.get("/api/v1/animals/")
    assert resp.status_code == 200, f"List animals failed: {resp.text}"
    # List returns wrapped response
    data = resp.json()["data"]
    assert any(a["id"] == animal_id for a in data)

    # 3. Get Animal
    print("  - Getting animal...")
    resp = client.get(f"/api/v1/animals/{animal_id}/")
    assert resp.status_code == 200, f"Get animal failed: {resp.text}"
    # Get returns DIRECT object (no data wrapper) based on views.py analysis
    data = resp.json()
    assert data["id"] == animal_id

    # 4. Update Animal
    print("  - Updating animal...")
    update_payload = {"name": "Simba", "species": "Lion", "age": 6}
    resp = client.put(f"/api/v1/animals/{animal_id}/", json=update_payload)
    assert resp.status_code == 200, f"Update animal failed: {resp.text}"
    # Update returns DIRECT object
    data = resp.json()
    assert data["age"] == 6

    # 5. Delete Animal
    print("  - Deleting animal...")
    resp = client.delete(f"/api/v1/animals/{animal_id}/")
    assert resp.status_code == 200, f"Delete animal failed: {resp.text}"
    # Delete returns DIRECT message
    assert resp.json()["message"] == "Animal deleted successfully"

    print("Animal Scenarios Passed.")
