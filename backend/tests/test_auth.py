"""認証テスト。"""
import os

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret-key")
    monkeypatch.setenv("AUTH_USERNAME", "admin")
    monkeypatch.setenv("AUTH_PASSWORD", "pass123")
    # Settings は import 時に読み込まれるため、テスト用に直接上書き
    from src import config

    config.settings.jwt_secret = "test-secret-key"
    config.settings.auth_username = "admin"
    config.settings.auth_password = "pass123"
    return TestClient(app)


def test_auth_status(client):
    res = client.get("/auth/status")
    assert res.status_code == 200
    data = res.json()
    assert data["auth_enabled"] is True


def test_login_and_access(client):
    login = client.post("/auth/login", json={"username": "admin", "password": "pass123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    protected = client.get("/records/stats", headers={"Authorization": f"Bearer {token}"})
    assert protected.status_code == 200

    no_auth = client.get("/records/stats")
    assert no_auth.status_code == 401
