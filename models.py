from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Student(Base):
    __tablename__ = "students"

    student_id = Column(String, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    place_of_birth = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    department = Column(String, nullable=False)
    speciality = Column(String, nullable=False)
    parent_name = Column(String, nullable=False)
    contact = Column(String, nullable=False)
    email = Column(String, nullable=False)
    photo_url = Column(String, nullable=False)
    age = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    campus = Column(String, nullable=True)
    level = Column(String, nullable=True)
    address = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    city = Column(String, nullable=True)
    school = Column(String, nullable=True)
    emergency_phone = Column(String, nullable=True)
    created_at      = Column(String, nullable=True,   
                             default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


    idcards = relationship("IDCard", back_populates="student")

class IDCard(Base):
    __tablename__ = "idcards"

    card_id = Column(String, primary_key=True, index=True)
    student_id = Column(String, ForeignKey("students.student_id"))
    issued_date = Column(String, nullable=False)
    expire_date = Column(String, nullable=False)
    pdf_url     = Column(String, nullable=True)

    student = relationship("Student", back_populates="idcards")

class Admin(Base):
    __tablename__ = "admins"

    admin_id = Column(String, primary_key=True)
    admin_name = Column(String, nullable=False)
    contact = Column(String, nullable=False)
    school = Column(String, nullable=False)
    email = Column(String, nullable=False)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, index=True)
    message = Column(String, nullable=False)
    is_read = Column(String, default="false")
    created_at = Column(String, nullable=False)
