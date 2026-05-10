from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime, date
import models
import uuid
import os
import cloudinary
import cloudinary.uploader

# Age calculator
def calculate_age(dob_str: str) -> str:
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return str(age)
    except:
        return ""

cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key    = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET"),
    secure     = True
)

router = APIRouter()

async def upload_to_cloudinary(img: UploadFile, ref: str) -> str:
    try:
        contents = await img.read()
        result = cloudinary.uploader.upload(
            contents,
            folder         = "identix/students",
            public_id      = ref,
            overwrite      = True,
            resource_type  = "image",
            transformation = [
                {"width": 400, "height": 500, "crop": "fill", "gravity": "face"},
                {"quality": "auto"},
                {"fetch_format": "auto"},
            ]
        )
        return result["secure_url"]
    except Exception as e:
        print(f"Cloudinary upload failed for {ref}: {e}")
        return ""


@router.post("/students")
async def create_student(
    firstname:      str = Form(...),
    secondname:     str = Form(...),
    email:          str = Form(...),
    contact:        str = Form(...),
    date:           str = Form(...),
    place:          str = Form(...),
    gender:         str = Form(...),
    school:         str = Form(...),
    Department:     str = Form(...),
    campus:         str = Form(...),
    specialty:      str = Form(...),
    level:          str = Form(...),
    address:        str = Form(...),
    nationality:    str = Form(...),
    city:           str = Form(...),
    emergencyName:  str = Form(...),
    emergencyPhone: str = Form(...),
    img: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    ref = "IDX-" + uuid.uuid4().hex[:8].upper()

    photo_url = ""
    if img and img.filename:
        photo_url = await upload_to_cloudinary(img, ref)

 # Check for duplicate email
    existing_email = db.query(models.Student).filter(
        models.Student.email == email
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=409,
            detail=f"A student with email '{email}' is already registered with ID {existing_email.student_id}"
        )

    # Check for duplicate name
    existing_name = db.query(models.Student).filter(
        models.Student.first_name == firstname,
        models.Student.last_name  == secondname
    ).first()
    if existing_name:
        raise HTTPException(
            status_code=409,
            detail=f"A student named '{firstname} {secondname}' is already registered with ID {existing_name.student_id}"
        )

    new_student = models.Student(
        student_id      = ref,
        first_name      = firstname,
        last_name       = secondname,
        email           = email,
        contact         = contact,
        date_of_birth   = date,
        place_of_birth  = place,
        department      = Department,
        speciality      = specialty,
        parent_name     = emergencyName,
        emergency_phone = emergencyPhone,
        photo_url       = photo_url,
        age             = calculate_age(date),
        gender          = gender,
        school          = school,
        campus          = campus,
        level           = level,
        address         = address,
        nationality     = nationality,
        city            = city,
        created_at      = datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    notification = models.Notification(
        id         = str(uuid.uuid4()),
        message    = (
            f"New student registered: {firstname} {secondname} "
            f"from {Department} — Ref: {ref}"
        ),
        is_read    = "false",
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.add(notification)
    db.commit()

    return JSONResponse(
        status_code=201,
        content={
            "message":    "Student registered successfully",
            "ref_number": ref,
            "photo_url":  photo_url,
            "student": {
                "name":   f"{firstname} {secondname}",
                "email":  email,
                "school": school,
                "ref":    ref,
            }
        }
    )


@router.get("/students")
def get_students(db: Session = Depends(get_db)):
    students = db.query(models.Student).all()
    result = []
    for s in students:
        # Check if student has a generated ID card
        card = db.query(models.IDCard).filter(
            models.IDCard.student_id == s.student_id
        ).first()
        id_status = "generated" if card else "pending"

        created_at = s.created_at or (card.issued_date if card else datetime.now().strftime("%Y-%m-%d"))


        result.append({
            "student_id":    s.student_id,
            "first_name":    s.first_name,
            "last_name":     s.last_name,
            "name":          f"{s.first_name} {s.last_name}",
            "email":         s.email or "",
            "department":    s.department or "",
            "speciality":    s.speciality or "",
            "level":         s.level or "",
            "campus":        s.campus or "",
            "photo_url":     s.photo_url or "",
            "contact":       s.contact or "",
            "gender":        s.gender or "",
            "date_of_birth": s.date_of_birth or "",
            "nationality":   s.nationality or "",
            "address":       s.address or "",
            "school":        s.school or "",
            "age":           s.age or "",
            "city":          s.city or "",
            "place_of_birth":s.place_of_birth or "",
            "parent_name":   s.parent_name or "",
            "emergency_phone":s.emergency_phone or "",
            # ← Key fields the frontend needs for status
            "idStatus":      id_status,
            "status":        id_status,
            "cardStatus":    id_status,
            "created_at":        created_at,
            "createdAt":         created_at,
            "registeredAt":      created_at,
            "enrolledAt":        created_at,
            "registration_date": created_at,
            "date":              created_at,

        })
    return {"students": result, "data": result, "total": len(result)}


@router.get("/students/{student_id}")
def get_student(student_id: str, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(
        models.Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"student": student}


@router.put("/students/{student_id}")
def update_student(student_id: str,
                   first_name: str = Form(...),
                   last_name:  str = Form(...),
                   db: Session = Depends(get_db)):
    existing = db.query(models.Student).filter(
        models.Student.student_id == student_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Student not found")
    existing.first_name = first_name
    existing.last_name  = last_name
    db.commit()
    return {"message": "Student updated successfully"}


@router.delete("/students/{student_id}")
def delete_student(student_id: str, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(
        models.Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"message": f"Student {student_id} deleted successfully"}