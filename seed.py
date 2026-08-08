"""
Populates the database with demo data so a reviewer (or interviewer) can
explore the API immediately after cloning, without manual data entry.

Usage:
    python seed.py
"""
from app.database import Base, engine, SessionLocal
from app import models, auth

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if not db.query(models.User).filter_by(email="admin@sms.com").first():
    admin = models.User(
        email="admin@sms.com",
        hashed_password=auth.hash_password("admin123"),
        role=models.RoleEnum.admin,
    )
    db.add(admin)

courses = [
    ("CS101", "Data Structures and Algorithms", 4, "CSE"),
    ("CS102", "Database Management Systems", 4, "CSE"),
    ("CS103", "Operating Systems", 3, "CSE"),
    ("CS104", "Computer Networks", 3, "CSE"),
]
for code, title, credits, dept in courses:
    if not db.query(models.Course).filter_by(code=code).first():
        db.add(models.Course(code=code, title=title, credits=credits, department=dept))

students = [
    ("SVIT001", "Manjunath", "K R", "manjunath@sms.com", "CSE", 3),
    ("SVIT002", "Aditi", "Sharma", "aditi@sms.com", "CSE", 2),
    ("SVIT003", "Rahul", "Verma", "rahul@sms.com", "ISE", 3),
]
for roll, fname, lname, email, dept, year in students:
    if not db.query(models.Student).filter_by(roll_number=roll).first():
        db.add(models.Student(
            roll_number=roll, first_name=fname, last_name=lname,
            email=email, department=dept, year_of_study=year,
        ))

db.commit()
db.close()

print("Seed data inserted.")
print("Admin login -> email: admin@sms.com | password: admin123")
