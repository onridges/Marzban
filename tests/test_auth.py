import os
import tempfile
import json

import pytest

# set env vars BEFORE importing app so config picks them up

def _setup_env(tmp_path):
    dbfile = tmp_path / "test.db"
    os.environ["SQLALCHEMY_DATABASE_URL"] = f"sqlite:///{dbfile}"
    os.environ["XRAY_EXECUTABLE_PATH"] = "/bin/true"
    os.environ["XRAY_ASSETS_PATH"] = "/tmp"
    os.environ["DOCS"] = "False"


@pytest.fixture(scope="session")
def app_client(tmp_path_factory):
    # prepare environment and import app
    tmp_path = tmp_path_factory.mktemp("data")
    _setup_env(tmp_path)

    # import here so that config reads our env
    from app import app
    from app.db.base import Base, engine, SessionLocal
    from app.db.models import JWT

    # create tables
    Base.metadata.create_all(bind=engine)
    # ensure a JWT secret exists for tests
    db = SessionLocal()
    db.add(JWT())
    db.commit()
    db.close()

    from fastapi.testclient import TestClient

    client = TestClient(app)

    yield client


def test_register_login_refresh_logout(app_client):
    client = app_client
    username = "testuser"
    password = "s3cret"

    # Register
    r = client.post("/api/register", json={"username": username, "password": password})
    assert r.status_code == 200
    assert r.json().get("detail") == "User created"

    # Duplicate registration should fail
    r = client.post("/api/register", json={"username": username, "password": password})
    assert r.status_code == 409

    # Login (form-data)
    r = client.post("/api/token", data={"username": username, "password": password})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and body["access_token"]
    assert "refresh_token" in body and body["refresh_token"]
    refresh_token = body["refresh_token"]

    # Use refresh token to get new access token
    r = client.post("/api/token/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and body["access_token"]

    # Logout (revoke refresh token)
    r = client.post("/api/logout", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert r.json().get("detail") == "Logged out"

    # Using revoked refresh token should fail
    r = client.post("/api/token/refresh", json={"refresh_token": refresh_token})
    assert r.status_code in (401, 404)
