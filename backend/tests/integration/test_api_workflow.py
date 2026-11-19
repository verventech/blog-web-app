import os
import secrets

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url
from sqlmodel import SQLModel

database_url = os.getenv("DATABASE_URL")
if not database_url or make_url(database_url).database != "test_db":
    pytest.skip(
        "Integration tests require a disposable PostgreSQL database named test_db",
        allow_module_level=True,
    )


@pytest.fixture(scope="module")
def client():
    os.environ.setdefault("SECRET_KEY", secrets.token_urlsafe(32))
    os.environ.setdefault("ALGORITHM", "HS256")

    from db import engine
    from main import app

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with TestClient(app) as test_client:
        yield test_client

    SQLModel.metadata.drop_all(engine)


def test_health_endpoint_works(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_user_can_register_and_login(client):
    registration = client.post(
        "/user",
        json={
            "name": "Sara",
            "username": "sara1",
            "email": "sara@test.com",
            "password": "mypassword123",
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/login",
        data={"username": "sara1", "password": "mypassword123"},
    )
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_blogs_endpoint_returns_paginated_shape(client):
    response = client.get("/blogs?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "next_cursor" in data
