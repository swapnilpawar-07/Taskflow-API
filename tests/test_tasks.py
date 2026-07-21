def create_sample_task(client, headers, **overrides):
    payload = {"title": "Write project README", "priority": "high"}
    payload.update(overrides)
    return client.post("/tasks", json=payload, headers=headers)


def test_create_task(client, auth_headers):
    resp = create_sample_task(client, auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Write project README"
    assert body["status"] == "todo"  # default
    assert body["priority"] == "high"
    assert "id" in body


def test_create_task_requires_auth(client):
    resp = client.post("/tasks", json={"title": "No auth"})
    assert resp.status_code == 401


def test_create_task_rejects_empty_title(client, auth_headers):
    resp = client.post("/tasks", json={"title": ""}, headers=auth_headers)
    assert resp.status_code == 422


def test_get_task_by_id(client, auth_headers):
    created = create_sample_task(client, auth_headers).json()
    resp = client.get(f"/tasks/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_nonexistent_task_returns_404(client, auth_headers):
    resp = client.get("/tasks/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_update_task(client, auth_headers):
    created = create_sample_task(client, auth_headers).json()
    resp = client.put(
        f"/tasks/{created['id']}",
        json={"status": "in_progress"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "in_progress"
    assert body["title"] == created["title"]  # untouched fields preserved


def test_delete_task(client, auth_headers):
    created = create_sample_task(client, auth_headers).json()
    resp = client.delete(f"/tasks/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get(f"/tasks/{created['id']}", headers=auth_headers)
    assert resp.status_code == 404


def test_list_tasks_pagination(client, auth_headers):
    for i in range(5):
        create_sample_task(client, auth_headers, title=f"Task {i}")

    resp = client.get("/tasks?skip=0&limit=2", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert body["limit"] == 2
    assert len(body["items"]) == 2

    resp = client.get("/tasks?skip=4&limit=2", headers=auth_headers)
    assert len(resp.json()["items"]) == 1  # only 1 left after skipping 4 of 5


def test_list_tasks_filter_by_status(client, auth_headers):
    create_sample_task(client, auth_headers, title="Todo task")
    done = create_sample_task(client, auth_headers, title="Done task").json()
    client.put(f"/tasks/{done['id']}", json={"status": "done"}, headers=auth_headers)

    resp = client.get("/tasks?status=done", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Done task"


def test_users_cannot_see_each_others_tasks(client):
    # User A
    client.post("/auth/register", json={"email": "a@example.com", "password": "passwordA123"})
    token_a = client.post(
        "/auth/login", data={"username": "a@example.com", "password": "passwordA123"}
    ).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B
    client.post("/auth/register", json={"email": "b@example.com", "password": "passwordB123"})
    token_b = client.post(
        "/auth/login", data={"username": "b@example.com", "password": "passwordB123"}
    ).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    task_a = create_sample_task(client, headers_a, title="A's private task").json()

    # B cannot fetch A's task directly
    resp = client.get(f"/tasks/{task_a['id']}", headers=headers_b)
    assert resp.status_code == 404

    # B's task list doesn't include A's task
    resp = client.get("/tasks", headers=headers_b)
    assert resp.json()["total"] == 0
