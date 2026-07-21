def test_register_new_user(client):
    resp = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert "hashed_password" not in body  # never leak password hash in responses
    assert "id" in body


def test_register_duplicate_email_rejected(client, registered_user):
    resp = client.post("/auth/register", json=registered_user)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_register_rejects_short_password(client):
    resp = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "short"},
    )
    assert resp.status_code == 422  # fails Pydantic min_length validation


def test_register_rejects_invalid_email(client):
    resp = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "password123"},
    )
    assert resp.status_code == 422


def test_login_success(client, registered_user):
    resp = client.post(
        "/auth/login",
        data={"username": registered_user["email"], "password": registered_user["password"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_rejected(client, registered_user):
    resp = client.post(
        "/auth/login",
        data={"username": registered_user["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_login_nonexistent_user_rejected(client):
    resp = client.post(
        "/auth/login",
        data={"username": "ghost@example.com", "password": "whatever123"},
    )
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_protected_route_rejects_bad_token(client):
    resp = client.get("/users/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert resp.status_code == 401


def test_me_returns_current_user(client, auth_headers, registered_user):
    resp = client.get("/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == registered_user["email"]
