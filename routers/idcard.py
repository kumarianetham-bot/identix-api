from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
import models
from typing import Optional

router = APIRouter()

class IDCard(BaseModel):
    card_id: str
    student_id: str
    issued_date: str
    expire_date: str
    pdf_url: Optional[str] = None  

@router.post("/idcards")
def create_idcard(idcard: IDCard, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(
        models.Student.student_id == idcard.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    new_idcard = models.IDCard(**idcard.dict())
    db.add(new_idcard)
    db.commit()
    db.refresh(new_idcard)
    return {
        "message": "ID Card created successfully",
        "idcard": idcard
    }

@router.get("/idcards")
def get_idcards(db: Session = Depends(get_db)):
    results = (
        db.query(models.IDCard, models.Student)
        .join(models.Student, models.IDCard.student_id == models.Student.student_id, isouter=True)
        .all()
    )
    idcards = []
    for card, student in results:
        idcards.append({
            "card_id":     card.card_id,
            "student_id":  card.student_id,
            "issued_date": card.issued_date,
            "expire_date": card.expire_date,
            "pdf_url":     card.pdf_url or "",  
            "first_name":  student.first_name  if student else "",
            "last_name":   student.last_name   if student else "",
            "email":       student.email       if student else "",
            "department":  student.department  if student else "",
            "photo_url":   student.photo_url   if student else "",
            "speciality":  student.speciality  if student else "",
            "level":       student.level       if student else "",
        })
    return {"idcards": idcards}

@router.get("/idcards/{card_id}")
def get_idcard(card_id: str, db: Session = Depends(get_db)):
    idcard = db.query(models.IDCard).filter(
        models.IDCard.card_id == card_id).first()
    if not idcard:
        raise HTTPException(status_code=404, detail="ID Card not found")
    return {"idcard": idcard}

@router.delete("/idcards/{card_id}")
def delete_idcard(card_id: str, db: Session = Depends(get_db)):
    idcard = db.query(models.IDCard).filter(
        models.IDCard.card_id == card_id).first()
    if not idcard:
        raise HTTPException(status_code=404, detail="ID Card not found")
    db.delete(idcard)
    db.commit()
    return {"message": f"ID Card {card_id} deleted successfully"}