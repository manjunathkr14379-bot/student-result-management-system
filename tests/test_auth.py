def test_register_and_login(client):
    r = client.post("/auth/register", json={
        "email": "alice@test.com", "password": "secret123", "role": "student"
    })
    assert r.status_code == 201
    assert r.json()["email"] == "alice@test.com"

    r = client.post("/auth/login", data={"username": "alice@test.com", "password": "secret123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password_fails(client):
    client.post("/auth/register", json={
        "email": "bob@test.com", "password": "secret123", "role": "student"
    })
    r = client.post("/auth/login", data={"username": "bob@test.com", "password": "wrong"})
    assert r.status_code == 401


def test_duplicate_registration_conflicts(client):
    payload = {"email": "carl@test.com", "password": "secret123", "role": "student"}
    client.post("/auth/register", json=payload)
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 409


def test_protected_route_requires_token(client):
    r = client.get("/students")
    assert r.status_code == 401
