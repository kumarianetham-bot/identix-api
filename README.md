# IDentix API 🪪

> **Smart Identity for Smart Schools**  
> A production grade REST API for managing student ID cards at Yaounde International Business School (YIBS).

---

## 🚀 Live Deployment

| Service | URL |
|---|---|
| **API** | https://identix-api-production.up.railway.app |
| **Interactive Docs** | https://identix-api-production.up.railway.app/docs |
| **Database** | PostgreSQL (Railway) |
| **File Storage** | Cloudinary |

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Features](#features)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Installation](#installation)
- [Deployment](#deployment)

---

## Overview

IDentix is a student ID card management system built for YIBS. It allows administrators to:

- Register and manage students
- Generate professional PDF ID cards with QR codes
- Store student photos and ID card PDFs on Cloudinary
- Track card status (pending / generated / active / expired)
- Manage admin accounts with secure authentication

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | FastAPI (Python) |
| **Database** | PostgreSQL + SQLAlchemy |
| **PDF Generation** | ReportLab + Pillow |
| **QR Code** | qrcode library |
| **File Storage** | Cloudinary |
| **Server** | Uvicorn |
| **Deployment** | Railway |
| **Auth** | SHA-256 password hashing |

---

## 📁 Project Structure

```
Identix API 1/
├── main.py                  # FastAPI app entry point
├── database.py              # Database connection
├── models.py                # SQLAlchemy models
├── pdf_generator.py         # ID card PDF design engine
├── cloudinary_config.py     # Cloudinary upload helpers
├── school_logo.png          # YIBS school logo
├── icon_location.png        # Footer location icon
├── icon_phone.png           # Footer phone icon
├── icon_globe.png           # Footer website icon
├── icon_email.png           # Footer email icon
├── identix_logo.png         # IDentix watermark
├── requirements.txt         # Python dependencies
├── routers/
│   ├── __init__.py
│   ├── auth.py              # Login & registration
│   ├── admin.py             # Admin management
│   ├── students.py          # Student CRUD
│   ├── idcard.py            # ID card CRUD
│   ├── idcard_generator.py  # PDF generation & download
│   ├── notifications.py     # Notifications
│   ├── upload.py            # File uploads
│   └── stats.py             # Dashboard statistics
└── static/
    └── idcards/             # Temporary PDF storage
```

---

## ✨ Features

- 🔐 **Secure Authentication**  Admin login with SHA-256 hashed passwords, case insensitive email/username
- 👨‍🎓 **Student Management**  Full CRUD with duplicate prevention by email and name
- 🪪 **ID Card Generation**  Beautiful professional PDF cards with:
  - School logo and branding
  - Student photo (fetched from Cloudinary)
  - QR code containing full student information
  - Gold accent lines and wave decorations
  - Academic year display
  - Front and back sides
- ☁️ **Cloudinary Storage**: Permanent storage for student photos and generated PDFs
- 📊 **Dashboard Stats** : Total students, generated cards, pending requests
- 🔔 **Notifications** : Activity log for student registrations
- 📥 **PDF Download**: Direct PDF download/view via API endpoint

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new admin |
| POST | `/auth/login` | Login with email/username |

### Students
| Method | Endpoint | Description |
|---|---|---|
| GET | `/students` | Get all students with ID status |
| POST | `/students` | Register a new student |
| GET | `/students/{student_id}` | Get a single student |
| PUT | `/students/{student_id}` | Update student |
| DELETE | `/students/{student_id}` | Delete student |

### ID Cards
| Method | Endpoint | Description |
|---|---|---|
| GET | `/idcards` | Get all generated ID cards |
| POST | `/idcards/generate` | Generate cards for list of students |
| GET | `/idcards/generate-card/{student_id}` | View/download a student's card |
| GET | `/idcards/{student_id}/download` | Download PDF card |
| DELETE | `/idcards/{card_id}` | Delete an ID card |

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| GET | `/stats` | Dashboard statistics |
| GET | `/activity` | Recent activity log |
| GET | `/requests` | Students without ID cards |
| GET | `/enrollments` | All enrolled students |

### Admin
| Method | Endpoint | Description |
|---|---|---|
| GET | `/admins` | Get all admins |
| POST | `/admins` | Create admin |
| PUT | `/admins/{admin_id}` | Update admin |
| DELETE | `/admins/{admin_id}` | Delete admin |
| POST | `/admin/fix-expiry` | Fix card expiry dates |

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

On Railway set these in the **Variables** tab of your service.

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/kumarianetham-bot/identix-api.git
cd identix-api

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn main:app --reload
```

API will be available at `http://127.0.0.1:8000`  
Interactive docs at `http://127.0.0.1:8000/docs`

---

## 🚢 Deployment

The API is deployed on **Railway** and connected to a **Railway PostgreSQL** database.

```bash
# Push to deploy
git add .
git commit -m "your message"
git push mirepo api-development
```

Railway auto-deploys on every push to the `api-development` branch.

---

## 📄 ID Card Design

The generated PDF ID card includes:

**Front:**
- YIBS shield logo
- School name and slogan
- Student photo with blue border
- Student name with gold underline
- Student ID, Date of Birth, Program, Level
- Campus, Issue Date, Valid Until
- Academic year in footer

**Back:**
- YIBS logo and school name
- Disclaimer text
- QR code (contains full student info)
- Student ID number
- Footer with location, phone, website, email icons

---

## 👨‍💻 Built With ❤️ for YIBS

**IDentix** — Smart Identity for Smart Schools  
Yaounde International Business School  
*Developing Innovative Professionals*
