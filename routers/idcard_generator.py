from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from pdf_generator import generate_id_card
from cloudinary_config import upload_pdf
import models
import os
import uuid
import tempfile
from datetime import datetime, timedelta

router = APIRouter()

PDF_DIR = "/tmp/idcards"
os.makedirs(PDF_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  GET /idcards/generate-card/{student_id}
#  View or Download a single student's ID card PDF
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/idcards/generate-card/{student_id}")
def generate_card_get(student_id: str, db: Session = Depends(get_db)):
    student = _get_student_or_404(student_id, db)
    card = db.query(models.IDCard).filter(
        models.IDCard.student_id == student_id
    ).first()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()

    student_data = {
        "student_id":    student.student_id,
        "first_name":    student.first_name,
        "last_name":     student.last_name,
        "department":    student.department,
        "speciality":    student.speciality,
        "photo_url":     student.photo_url,
        "level":         student.level,
        "campus":        student.campus,
        "gender":        student.gender,
        "school":        student.school,
        "date_of_birth": getattr(student, "date_of_birth", ""),
        "nationality":   getattr(student, "nationality", ""),
        "contact":       getattr(student, "contact", ""),
        "issued_date":   card.issued_date if card else datetime.now().strftime("%Y-%m-%d"),
        "expire_date":   card.expire_date if card else (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
    }

    result = generate_id_card(student_data, tmp.name)
    if not result:
        raise HTTPException(status_code=500, detail="PDF generation failed")

    return FileResponse(
        path=tmp.name,
        media_type="application/pdf",
        filename=f"id_card_{student_id}.pdf"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  POST /idcards/generate
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/idcards/generate")
def generate_cards_post(payload: dict, db: Session = Depends(get_db)):
    student_ids = payload.get("studentIds", [])
    if not student_ids:
        raise HTTPException(status_code=422, detail="No studentIds provided")

    generated = []
    failed = []

    for sid in student_ids:
        try:
            student = _get_student_or_404(sid, db)
            pdf_url = _make_pdf(student)
            card = _save_card_record(sid, pdf_url, db)

            generated.append({
                "id":             card.card_id,
                "card_id":        card.card_id,
                "studentId":      student.student_id,
                "student_id":     student.student_id,
                "name":           f"{student.first_name} {student.last_name}",
                "first_name":     student.first_name,
                "last_name":      student.last_name,
                "department":     student.department or "",
                "speciality":     student.speciality or "",
                "level":          student.level or "",
                "campus":         student.campus or "",
                "school":         student.school or "",
                "photo":          student.photo_url or "",
                "photo_url":      student.photo_url or "",
                "email":          student.email or "",
                "issued_date":    card.issued_date,
                "expire_date":    card.expire_date,
                "issuedAt":       card.issued_date,
                "expiryDate":     card.expire_date,
                "validUntil":     card.expire_date,
                "generationDate": card.issued_date,
                "enrolledAt":     None,
                "cardStatus":     "active",
                "status":         "generated",
                "idNumber":       student.student_id,
                "pdf_url":        pdf_url,
            })

        except HTTPException as e:
            failed.append({"student_id": sid, "reason": e.detail})
        except Exception as e:
            failed.append({"student_id": sid, "reason": str(e)})

    if not generated:
        raise HTTPException(
            status_code=500,
            detail=f"No cards could be generated. Details: {failed}"
        )

    return {
        "success":  True,
        "generated": generated,
        "failed":    failed,
        "total":     len(generated),
        "pdf_urls":  [c["pdf_url"] for c in generated],
    }


# ══════════════════════════════════════════════════════════════════════════════
#  GET /idcards/{student_id}/download
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/idcards/{student_id}/download")
def download_idcard(student_id: str, db: Session = Depends(get_db)):
    student = _get_student_or_404(student_id, db)
    card = db.query(models.IDCard).filter(
        models.IDCard.student_id == student_id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="No card found for this student")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()

    student_data = {
        "student_id":    student.student_id,
        "first_name":    student.first_name,
        "last_name":     student.last_name,
        "department":    student.department,
        "speciality":    student.speciality,
        "photo_url":     student.photo_url,
        "level":         student.level,
        "campus":        student.campus,
        "gender":        student.gender,
        "school":        student.school,
        "date_of_birth": getattr(student, "date_of_birth", ""),
        "nationality":   getattr(student, "nationality", ""),
        "contact":       getattr(student, "contact", ""),
        "issued_date":   card.issued_date,
        "expire_date":   card.expire_date,
    }

    result = generate_id_card(student_data, tmp.name)
    if not result:
        raise HTTPException(status_code=500, detail="PDF generation failed")

    return FileResponse(
        path=tmp.name,
        media_type="application/pdf",
        filename=f"id_card_{student.student_id}.pdf"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _get_student_or_404(student_id: str, db: Session) -> models.Student:
    student = db.query(models.Student).filter(
        models.Student.student_id == student_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    return student


def _make_pdf(student: models.Student) -> str:
    student_data = {
        "student_id":    student.student_id,
        "first_name":    student.first_name,
        "last_name":     student.last_name,
        "department":    student.department,
        "speciality":    student.speciality,
        "photo_url":     student.photo_url,
        "level":         student.level,
        "campus":        student.campus,
        "gender":        student.gender,
        "school":        student.school,
        "date_of_birth": getattr(student, "date_of_birth", ""),
        "nationality":   getattr(student, "nationality", ""),
        "contact":       getattr(student, "contact", ""),
    }

    filename = f"id_card_{student.student_id}.pdf"
    output_path = os.path.join(PDF_DIR, filename)

    result = generate_id_card(student_data, output_path)
    if not result:
        raise Exception(f"PDF generation failed for {student.student_id}")

    # Upload to Cloudinary and return permanent URL
    cloudinary_url = upload_pdf(
        output_path,
        public_id=f"id_card_{student.student_id}"
    )
    return cloudinary_url


def _save_card_record(student_id: str, pdf_url: str, db: Session) -> models.IDCard:
    issued = datetime.now().strftime("%Y-%m-%d")
    expire = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    existing = db.query(models.IDCard).filter(
        models.IDCard.student_id == student_id
    ).first()
    if existing:
        existing.issued_date = issued
        existing.expire_date = expire
        existing.pdf_url     = pdf_url
        db.commit()
        db.refresh(existing)
        return existing
    card = models.IDCard(
        card_id     = str(uuid.uuid4()),
        student_id  = student_id,
        issued_date = issued,
        expire_date = expire,
        pdf_url     = pdf_url,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card