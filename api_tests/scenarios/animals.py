from api_tests.client import APIClient


def run(client: APIClient):
    print("Running Animal Scenarios...")

    from api_tests.assertions import assert_structure

    animal_obj_structure = {"id": str, "name": str, "species": str, "age": int}

    wrapped_animal_structure = {"data": animal_obj_structure, "trace_id": str, "error": (dict, type(None))}

    wrapped_list_structure = {"data": [animal_obj_structure], "trace_id": str, "error": (dict, type(None))}

    # 1. Create Animal
    print("  - Creating animal...")
    create_payload = {"name": "Simba", "species": "Lion", "age": 5}
    resp = client.post("/api/v1/animals/", json=create_payload)
    assert resp.status_code == 200, f"Create animal failed: {resp.text}"

    data = resp.json()
    assert_structure(data, wrapped_animal_structure, path="create_animal_response")
    animal_id = data["data"]["id"]

    # 2. List Animals
    print("  - Listing animals...")
    resp = client.get("/api/v1/animals/")
    assert resp.status_code == 200, f"List animals failed: {resp.text}"

    data = resp.json()
    assert_structure(data, wrapped_list_structure, path="list_animals_response")
    assert any(a["id"] == animal_id for a in data["data"])

    # 3. Get Animal
    print("  - Getting animal...")
    resp = client.get(f"/api/v1/animals/{animal_id}/")
    assert resp.status_code == 200, f"Get animal failed: {resp.text}"

    data = resp.json()
    # Get returns DIRECT object
    assert_structure(data, animal_obj_structure, path="get_animal_response")
    assert data["id"] == animal_id

    # 4. Update Animal
    print("  - Updating animal...")
    update_payload = {"name": "Simba", "species": "Lion", "age": 6}
    resp = client.put(f"/api/v1/animals/{animal_id}/", json=update_payload)
    assert resp.status_code == 200, f"Update animal failed: {resp.text}"

    data = resp.json()
    # Update returns DIRECT object
    assert_structure(data, animal_obj_structure, path="update_animal_response")
    assert data["age"] == 6

    # 5. Delete Animal
    print("  - Deleting animal...")
    resp = client.delete(f"/api/v1/animals/{animal_id}/")
    assert resp.status_code == 200, f"Delete animal failed: {resp.text}"

    data = resp.json()
    # Delete returns DIRECT message
    assert_structure(data, {"message": str}, path="delete_animal_response")
    assert data["message"] == "Animal deleted successfully"

    print("Animal Scenarios Passed.")
