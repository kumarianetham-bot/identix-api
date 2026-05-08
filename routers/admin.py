from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from datetime import datetime
import models

router = APIRouter()

class Admin(BaseModel):
    admin_id: str
    admin_name: str
    contact: str
    school: str
    email: str

@router.post("/admins")
def create_admin(admin: Admin, db: Session = Depends(get_db)):
    new_admin = models.Admin(**admin.dict())
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return {
        "message": "Admin created successfully",
        "admin": admin
    }

@router.get("/admins")
def get_admins(db: Session = Depends(get_db)):
    admins = db.query(models.Admin).all()
    return {"admins": admins}

@router.get("/admins/{admin_id}")
def get_admin(admin_id: str, db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(
        models.Admin.admin_id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return {"admin": admin}

@router.put("/admins/{admin_id}")
def update_admin(admin_id: str, admin: Admin,
                 db: Session = Depends(get_db)):
    existing_admin = db.query(models.Admin).filter(
        models.Admin.admin_id == admin_id).first()
    if not existing_admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    for key, value in admin.dict().items():
        setattr(existing_admin, key, value)
    db.commit()
    return {
        "message": "Admin updated successfully",
        "admin": admin
    }

@router.delete("/admins/{admin_id}")
def delete_admin(admin_id: str, db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(
        models.Admin.admin_id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    db.delete(admin)
    db.commit()
    return {"message": f"Admin {admin_id} deleted successfully"}


# ── Fix missing student dates ─────────────────────────────────────────────────
@router.post("/admin/fix-dates")
def fix_student_dates(db: Session = Depends(get_db)):
    students = db.query(models.Student).filter(
        models.Student.created_at == None
    ).all()

    count = 0
    for student in students:
        card = db.query(models.IDCard).filter(
            models.IDCard.student_id == student.student_id
        ).first()
        if card:
            student.created_at = card.issued_date + " 00:00:00"
        else:
            student.created_at = "2026-01-01 00:00:00"
        count += 1

    db.commit()
    return {"message": f"Fixed {count} students with missing dates"}