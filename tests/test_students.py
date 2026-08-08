from tests.conftest import register_and_login


def make_student_payload(roll="CSE001", email="s1@test.com"):
    return {
        "roll_number": roll,
        "first_name": "Manjunath",
        "last_name": "KR",
        "email": email,
        "department": "CSE",
        "year_of_study": 2,
    }


def test_admin_can_create_student(client):
    headers = register_and_login(client)
    r = client.post("/students", json=make_student_payload(), headers=headers)
    assert r.status_code == 201
    assert r.json()["roll_number"] == "CSE001"


def test_student_role_cannot_create_student(client):
    headers = register_and_login(client, email="stud@test.com", role="student")
    r = client.post("/students", json=make_student_payload(), headers=headers)
    assert r.status_code == 403


def test_duplicate_roll_number_conflicts(client):
    headers = register_and_login(client)
    client.post("/students", json=make_student_payload(), headers=headers)
    r = client.post("/students", json=make_student_payload(email="different@test.com"), headers=headers)
    assert r.status_code == 409


def test_list_and_search_students(client):
    headers = register_and_login(client)
    client.post("/students", json=make_student_payload("CSE001", "a@test.com"), headers=headers)
    client.post("/students", json=make_student_payload("CSE002", "b@test.com"), headers=headers)

    r = client.get("/students", headers=headers)
    assert r.status_code == 200
    assert r.json()["total"] == 2

    r = client.get("/students?search=CSE002", headers=headers)
    assert r.json()["total"] == 1


def test_get_nonexistent_student_returns_404(client):
    headers = register_and_login(client)
    r = client.get("/students/999", headers=headers)
    assert r.status_code == 404


def test_update_and_delete_student(client):
    headers = register_and_login(client)
    created = client.post("/students", json=make_student_payload(), headers=headers).json()

    r = client.patch(f"/students/{created['id']}", json={"year_of_study": 3}, headers=headers)
    assert r.status_code == 200
    assert r.json()["year_of_study"] == 3

    r = client.delete(f"/students/{created['id']}", headers=headers)
    assert r.status_code == 204

    r = client.get(f"/students/{created['id']}", headers=headers)
    assert r.status_code == 404


def test_transcript_and_gpa_calculation(client):
    headers = register_and_login(client)
    student = client.post("/students", json=make_student_payload(), headers=headers).json()
    course = client.post("/courses", json={
        "code": "CS101", "title": "Data Structures", "credits": 4, "department": "CSE"
    }, headers=headers).json()

    enrollment = client.post("/enrollments", json={
        "student_id": student["id"], "course_id": course["id"]
    }, headers=headers).json()

    client.patch(f"/enrollments/{enrollment['id']}/grade", json={"grade": 88}, headers=headers)

    r = client.get(f"/students/{student['id']}/transcript", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_credits"] == 4
    assert data["gpa"] == round(88 / 25.0, 2)
