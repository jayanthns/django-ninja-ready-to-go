import os
import sys

from api_tests import utils
from api_tests.client import APIClient
from api_tests.scenarios import animals, audit, auth, files, users

TEST_DB_NAME = "test_db_api"
TEST_PORT = 8001
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"


def main():
    print("=== Starting API Test Suite ===")

    # Ensure we are in the project root
    project_root = os.getcwd()
    if not os.path.exists(os.path.join(project_root, "manage.py")):
        print("Error: manage.py not found. Please run from project root.")
        sys.exit(1)

    server_proc = None
    try:
        # 1. Setup Test DB
        utils.create_test_db(TEST_DB_NAME)

        # 2. Run Migrations
        utils.run_migrations(TEST_DB_NAME)

        # 3. Start Server
        server_proc = utils.start_server(TEST_DB_NAME, TEST_PORT)

        # 4. Initialize Client
        client = APIClient(BASE_URL)

        # 5. Run Scenarios
        auth.run(client)
        users.run(client)
        animals.run(client)
        files.run(client)
        audit.run(client)

        print("\n=== All Tests Passed Successfully! ===")

    except Exception as e:
        print(f"\n=== Test Failed: {e} ===")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        # 6. Cleanup
        if server_proc:
            utils.stop_server(server_proc)

        try:
            utils.drop_test_db(TEST_DB_NAME)
        except Exception as e:
            print(f"Warning: Failed to drop test db: {e}")


if __name__ == "__main__":
    main()
