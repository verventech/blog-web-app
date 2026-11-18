import os
import uuid

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.engine import make_url
from sqlmodel import SQLModel

database_url = os.getenv("DATABASE_URL")
if not database_url or make_url(database_url).database != "test_db":
    pytest.skip(
        "Integration tests require a disposable PostgreSQL database named test_db",
        allow_module_level=True,
    )


@pytest.fixture(scope="module", autouse=True)
def clean_database():
    from db import engine
    from main import app  # noqa: F401

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


def register(client: TestClient, username: str) -> dict:
    response = client.post(
        "/user",
        json={
            "name": username.title(),
            "username": username,
            "email": f"{username}@example.com",
            "password": "test-password-123",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, username: str) -> dict:
    response = client.post(
        "/login",
        data={"username": username, "password": "test-password-123"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_blog_and_feed_api_workflow():
    from main import app

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    reader_name = f"reader_{suffix}"
    author_name = f"author_{suffix}"

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    register(client, reader_name)
    author = register(client, author_name)
    reader_headers = login(client, reader_name)
    author_headers = login(client, author_name)

    follow = client.post(f"/user/{author['id']}/follow", headers=reader_headers)
    assert follow.status_code == 200
    assert follow.json()["following"] is True

    first_blog = client.post(
        "/blog",
        json={"title": "First post", "content": "First body"},
        headers=author_headers,
    )
    second_blog = client.post(
        "/blog",
        json={"title": "Second post", "content": "Second body"},
        headers=author_headers,
    )
    assert first_blog.status_code == 201
    assert second_blog.status_code == 201
    first_blog_id = first_blog.json()["id"]
    second_blog_id = second_blog.json()["id"]

    first_page = client.get("/blogs?limit=1")
    assert first_page.status_code == 200
    first_page_data = first_page.json()
    assert [blog["id"] for blog in first_page_data["items"]] == [second_blog_id]
    assert first_page_data["has_more"] is True

    second_page = client.get(
        f"/blogs?limit=1&cursor={first_page_data['next_cursor']}"
    )
    assert [blog["id"] for blog in second_page.json()["items"]] == [first_blog_id]
    assert second_page.json()["has_more"] is False

    feed = client.get("/feed", headers=reader_headers)
    assert feed.status_code == 200
    assert {blog["id"] for blog in feed.json()["items"]} == {
        first_blog_id,
        second_blog_id,
    }

    comment = client.post(
        f"/blog/{first_blog_id}/comment",
        json={"text": "Original response"},
        headers=reader_headers,
    )
    assert comment.status_code == 201
    comment_id = comment.json()["id"]

    updated_comment = client.patch(
        f"/blog/{first_blog_id}/comment/{comment_id}",
        json={"text": "Updated response"},
        headers=reader_headers,
    )
    assert updated_comment.status_code == 200
    assert updated_comment.json()["text"] == "Updated response"

    updated_blog = client.patch(
        f"/blog/{first_blog_id}",
        json={"title": "Updated title", "content": "Updated body"},
        headers=author_headers,
    )
    assert updated_blog.status_code == 200
    assert updated_blog.json()["title"] == "Updated title"
    assert updated_blog.json()["comments_count"] == 1

    unauthorized_update = client.patch(
        f"/blog/{first_blog_id}",
        json={"title": "Not allowed", "content": "No"},
        headers=reader_headers,
    )
    assert unauthorized_update.status_code == 403

    liked = client.post(f"/blog/{first_blog_id}/like", headers=reader_headers)
    assert liked.status_code == 200
    assert liked.json()["liked"] is True

    deleted = client.delete(f"/blog/{second_blog_id}", headers=author_headers)
    assert deleted.status_code == 200
    assert client.get(f"/blog/{second_blog_id}").status_code == 404
