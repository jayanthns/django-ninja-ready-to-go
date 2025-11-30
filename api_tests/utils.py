import os
import subprocess
import time

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# If running from host, DB_HOST might need to be localhost even if .env says 'django_ninja_db'
# But we assume the user has configured .env for docker.
# We will force localhost for the runner if we detect we are on host (simple heuristic or just force it)
# Actually, let's try to connect to localhost first.
try:
    conn = psycopg2.connect(user=DB_USER, password=DB_PASSWORD, host="localhost", port=DB_PORT)
    conn.close()
    DB_HOST = "localhost"
except:
    pass  # Keep what's in env


def get_db_connection(db_name=None):
    return psycopg2.connect(
        user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database=db_name or "postgres"
    )


def create_test_db(db_name):
    print(f"Creating test database: {db_name}...")
    conn = get_db_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    try:
        cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
        cur.execute(f"CREATE DATABASE {db_name}")
    finally:
        cur.close()
        conn.close()


def drop_test_db(db_name):
    print(f"Dropping test database: {db_name}...")
    conn = get_db_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    try:
        cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
    finally:
        cur.close()
        conn.close()


def run_migrations(db_name):
    print("Running migrations...")
    env = os.environ.copy()
    env["DB_NAME"] = db_name
    env["DB_HOST"] = DB_HOST  # Ensure we use the reachable host
    subprocess.run(["python", "manage.py", "migrate"], env=env, check=True)


def start_server(db_name, port):
    print(f"Starting test server on port {port}...")
    env = os.environ.copy()
    env["DB_NAME"] = db_name
    env["DB_HOST"] = DB_HOST

    # Use uvicorn directly
    proc = subprocess.Popen(
        ["uvicorn", "main.asgi:application", "--host", "127.0.0.1", "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    # Simple retry loop to check if port is open
    import socket

    start_time = time.time()
    while time.time() - start_time < 10:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                print("Server is ready.")
                return proc
        except (OSError, ConnectionRefusedError):
            time.sleep(0.5)

    proc.terminate()
    raise RuntimeError("Server failed to start")


def stop_server(proc):
    print("Stopping server...")
    proc.terminate()
    proc.wait()
