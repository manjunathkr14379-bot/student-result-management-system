from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import schemas, models, auth
from app.database import get_db
from app.services import student_service

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("", response_model=schemas.StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(
    student_in: schemas.StudentCreate,
    db: Session = Depends(get_db),
    _=Depends(auth.require_role(models.RoleEnum.admin, models.RoleEnum.teacher)),
):
    return student_service.create_student(db, student_in)


@router.get("", response_model=schemas.PaginatedStudents)
def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    department: Optional[str] = None,
    search: Optional[str] = Query(None, description="Search by name or roll number"),
    db: Session = Depends(get_db),
    _=Depends(auth.get_current_user),
):
    total, items = student_service.list_students(db, page, page_size, department, search)
    return schemas.PaginatedStudents(total=total, page=page, page_size=page_size, items=items)


@router.get("/{student_id}", response_model=schemas.StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    return student_service.get_student(db, student_id)


@router.get("/{student_id}/transcript", response_model=schemas.StudentTranscript)
def get_transcript(student_id: int, db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    return student_service.get_transcript(db, student_id)


@router.patch("/{student_id}", response_model=schemas.StudentOut)
def update_student(
    student_id: int,
    student_in: schemas.StudentUpdate,
    db: Session = Depends(get_db),
    _=Depends(auth.require_role(models.RoleEnum.admin, models.RoleEnum.teacher)),
):
    return student_service.update_student(db, student_id, student_in)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    _=Depends(auth.require_role(models.RoleEnum.admin)),
):
    student_service.delete_student(db, student_id)
