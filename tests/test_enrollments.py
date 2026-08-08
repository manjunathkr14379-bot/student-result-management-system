from tests.conftest import register_and_login


def setup_student_and_course(client, headers):
    student = client.post("/students", json={
        "roll_number": "CSE010", "first_name": "Test", "last_name": "User",
        "email": "test@test.com", "department": "CSE", "year_of_study": 1,
    }, headers=headers).json()
    course = client.post("/courses", json={
        "code": "CS201", "title": "Algorithms", "credits": 3, "department": "CSE"
    }, headers=headers).json()
    return student, course


def test_duplicate_enrollment_conflicts(client):
    headers = register_and_login(client)
    student, course = setup_student_and_course(client, headers)

    payload = {"student_id": student["id"], "course_id": course["id"]}
    r1 = client.post("/enrollments", json=payload, headers=headers)
    r2 = client.post("/enrollments", json=payload, headers=headers)

    assert r1.status_code == 201
    assert r2.status_code == 409


def test_enroll_nonexistent_student_404s(client):
    headers = register_and_login(client)
    _, course = setup_student_and_course(client, headers)
    r = client.post("/enrollments", json={"student_id": 999, "course_id": course["id"]}, headers=headers)
    assert r.status_code == 404


def test_invalid_grade_rejected(client):
    headers = register_and_login(client)
    student, course = setup_student_and_course(client, headers)
    enrollment = client.post("/enrollments", json={
        "student_id": student["id"], "course_id": course["id"]
    }, headers=headers).json()

    r = client.patch(f"/enrollments/{enrollment['id']}/grade", json={"grade": 150}, headers=headers)
    assert r.status_code == 422  # fails Pydantic's le=100 validation
