"""
IDentix PDF ID Card Generator - YIBS Design (Optimized Layout)
Exact match to YIBS mockup with IDentix watermark.
Requires: reportlab, Pillow, qrcode
Install:  pip install reportlab Pillow qrcode
"""

import io
import os
import json
from datetime import datetime, timedelta

from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ── Brand colours ─────────────────────────────────────────────────────────────
DARK_NAVY     = HexColor("#0B1F4A")
MID_NAVY      = HexColor("#1A355C")
LIGHT_BLUE    = HexColor("#2A5298")
GOLD_ACCENT   = HexColor("#C8963E")
WHITE         = white
TEXT_DARK     = HexColor("#1A1A1A")
TEXT_NAVY     = HexColor("#0B1F4A")
BORDER_GRAY   = HexColor("#CCCCCC")
LIGHT_GRAY    = HexColor("#F5F5F5")

# ── Card dimensions (A4 portrait) ─────────────────────────────────────────────
PAGE_W = 210 * mm
PAGE_H = 297 * mm
MARGIN = 10 * mm
CARD_W = PAGE_W - (2 * MARGIN)
CARD_H = PAGE_H - (2 * MARGIN)

# Section heights
HEADER_H = 25 * mm
FRONT_INFO_H = 85 * mm
BACK_INFO_H = 120 * mm
FOOTER_H = 20 * mm

# ── Asset paths ───────────────────────────────────────────────────────────────
_HERE     = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(_HERE, "yibs_logo_official.png")
IDENTIX_WATERMARK_PATH = os.path.join(_HERE, "identix_logo.png")


# ─────────────────────────────────────────────────────────────────────────────
#  Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def _draw_watermark(c, center_x, center_y, max_w, max_h):
    """Draw IDentix watermark centered with very low opacity."""
    if os.path.exists(IDENTIX_WATERMARK_PATH):
        try:
            c.saveState()
            logo = ImageReader(IDENTIX_WATERMARK_PATH)
            img_w, img_h = logo.getSize()
            aspect = img_h / img_w if img_w > 0 else 0.5
            
            # Target size - 40% of page width
            target_w = max_w * 0.4
            target_h = target_w * aspect
            
            if target_h > max_h * 0.3:
                target_h = max_h * 0.3
                target_w = target_h / aspect
            
            # Position at exact center
            x = center_x - (target_w / 2)
            y = center_y - (target_h / 2)
            
            c.setFillAlpha(0.06)  # 6% opacity - very subtle
            c.drawImage(logo, x, y, target_w, target_h,
                       preserveAspectRatio=True, mask='auto')
            c.restoreState()
        except Exception as e:
            print(f"Watermark error: {e}")


def _draw_yibs_logo(c, x, y, size=20*mm):
    """Draw YIBS logo."""
    if os.path.exists(LOGO_PATH):
        try:
            c.drawImage(ImageReader(LOGO_PATH), x, y, size, size,
                       preserveAspectRatio=True, mask='auto')
            return size
        except Exception as e:
            print(f"Logo error: {e}")
    return size


def _draw_id_card_border(c, x, y, w, h):
    """Draw card border with rounded corners effect."""
    c.setStrokeColor(BORDER_GRAY)
    c.setLineWidth(0.5)
    c.rect(x, y, w, h, stroke=1, fill=0)
    
    # Inner border for premium look
    c.setStrokeColor(LIGHT_GRAY)
    c.setLineWidth(0.3)
    c.rect(x+1*mm, y+1*mm, w-2*mm, h-2*mm, stroke=1, fill=0)


def _make_qr(data: str) -> io.BytesIO:
    """Generate QR code."""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0B1F4A", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except ImportError:
        # Simple fallback
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (200, 200), "white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 190, 190], outline="#0B1F4A", width=2)
        draw.text((100, 100), "QR", fill="#0B1F4A")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf


# ─────────────────────────────────────────────────────────────────────────────
#  FRONT SECTION
# ─────────────────────────────────────────────────────────────────────────────

def _draw_front_section(c, x, y, w, h, student):
    """Draw front of ID card (top portion)."""
    
    # Card background
    c.setFillColor(WHITE)
    c.rect(x, y, w, h, fill=1, stroke=0)
    
    # Header with YIBS branding
    header_y = y + h - HEADER_H
    
    # Blue header background
    c.setFillColor(DARK_NAVY)
    c.rect(x, header_y, w, HEADER_H, fill=1, stroke=0)
    
    # Gold accent line at bottom of header
    c.setStrokeColor(GOLD_ACCENT)
    c.setLineWidth(1.5)
    c.line(x, header_y, x + w, header_y)
    
    # School name in header
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(WHITE)
    c.drawString(x + 8*mm, header_y + 18*mm, "YAOUNDE INTERNATIONAL")
    c.drawString(x + 8*mm, header_y + 13*mm, "BUSINESS SCHOOL")
    
    # YIBS logo in header
    logo_size = 18*mm
    _draw_yibs_logo(c, x + w - logo_size - 5*mm, header_y + 3*mm, logo_size)
    
    # --- Student Information Area ---
    info_y = header_y - 15*mm
    
    # Photo frame
    photo_x = x + 10*mm
    photo_y = info_y - 45*mm
    photo_w = 30*mm
    photo_h = 38*mm
    
    # Photo border
    c.setStrokeColor(GOLD_ACCENT)
    c.setLineWidth(1)
    c.rect(photo_x, photo_y, photo_w, photo_h, fill=0, stroke=1)
    
    # Load and draw photo
    photo_url = student.get("photo_url", "")
    drawn = False
    if photo_url:
        try:
            if photo_url.startswith("http"):
                import urllib.request
                req = urllib.request.Request(photo_url, 
                      headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    img_data = io.BytesIO(resp.read())
                c.drawImage(ImageReader(img_data), 
                          photo_x+1*mm, photo_y+1*mm,
                          photo_w-2*mm, photo_h-2*mm,
                          preserveAspectRatio=True, mask='auto')
                drawn = True
        except Exception:
            pass
    
    if not drawn:
        # Placeholder
        c.setFillColor(LIGHT_GRAY)
        c.rect(photo_x+1*mm, photo_y+1*mm, photo_w-2*mm, photo_h-2*mm, 
               fill=1, stroke=0)
        c.setFont("Helvetica", 7)
        c.setFillColor(BORDER_GRAY)
        c.drawCentredString(photo_x + photo_w/2, photo_y + photo_h/2, "PHOTO")
    
    # Student details (right of photo)
    detail_x = photo_x + photo_w + 8*mm
    detail_y = info_y
    
    # NAME
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(DARK_NAVY)
    c.drawString(detail_x, detail_y, "NAME")
    
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(DARK_NAVY)
    name = f"{student.get('first_name', '')} {student.get('last_name', '')}"
    c.drawString(detail_x, detail_y - 8*mm, name)
    
    # Gold underline
    c.setStrokeColor(GOLD_ACCENT)
    c.setLineWidth(1)
    c.line(detail_x, detail_y - 10*mm, detail_x + 70*mm, detail_y - 10*mm)
    
    # STUDENT ID
    info_start = detail_y - 20*mm
    c.setFont("Helvetica", 7)
    c.setFillColor(TEXT_NAVY)
    c.drawString(detail_x, info_start, "STUDENT ID")
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(DARK_NAVY)
    c.drawString(detail_x, info_start - 6*mm, student.get("student_id", ""))
    
    # SPECIALITY
    info_start -= 16*mm
    c.setFont("Helvetica", 7)
    c.setFillColor(TEXT_NAVY)
    c.drawString(detail_x, info_start, "SPECIALITY")
    
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(TEXT_DARK)
    speciality = student.get("speciality", student.get("department", ""))
    c.drawString(detail_x, info_start - 6*mm, speciality)
    
    # LEVEL
    info_start -= 14*mm
    c.setFont("Helvetica", 7)
    c.setFillColor(TEXT_NAVY)
    c.drawString(detail_x, info_start, "LEVEL")
    
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(TEXT_DARK)
    c.drawString(detail_x, info_start - 6*mm, student.get("level", ""))
    
    # Registrar Signature box
    sig_x = detail_x
    sig_y = photo_y + 2*mm
    sig_w = 40*mm
    sig_h = 12*mm
    
    c.setStrokeColor(BORDER_GRAY)
    c.setLineWidth(0.5)
    c.rect(sig_x, sig_y, sig_w, sig_h, fill=0, stroke=1)
    
    c.setFont("Helvetica", 5.5)
    c.setFillColor(BORDER_GRAY)
    c.drawCentredString(sig_x + sig_w/2, sig_y + sig_h/2 + 1*mm, "Registrar Signature")
    
    # Separator line between front and back
    c.setStrokeColor(BORDER_GRAY)
    c.setLineWidth(0.3)
    c.setDash(3, 3)
    c.line(x + 5*mm, y, x + w - 5*mm, y)
    c.setDash()


# ─────────────────────────────────────────────────────────────────────────────
#  BACK SECTION
# ─────────────────────────────────────────────────────────────────────────────

def _draw_back_section(c, x, y, w, h, student):
    """Draw back of ID card (bottom portion)."""
    
    # Card background
    c.setFillColor(WHITE)
    c.rect(x, y, w, h, fill=1, stroke=0)
    
    # --- Left Column: Rules & Regulations ---
    left_x = x + 8*mm
    left_y = y + h - 15*mm
    
    # Title
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(DARK_NAVY)
    c.drawString(left_x, left_y, "IDCARD RULES & REGULATIONS")
    
    # Gold underline
    c.setStrokeColor(GOLD_ACCENT)
    c.setLineWidth(1)
    c.line(left_x, left_y - 2*mm, left_x + 65*mm, left_y - 2*mm)
    
    # Rules
    rules = [
        "ID Card is the property of Yaounde International",
        "Business School (YIBS).",
        "This card is non-transferable and must be used",
        "only by the authorized student.",
        "The card must be presented upon request by",
        "school staff or security personnel.",
        "Loss or theft of this card must be reported",
        "immediately to the Registrar's Office.",
        "Misuse of this card may result in",
        "disciplinary action."
    ]
    
    rule_y = left_y - 8*mm
    c.setFont("Helvetica", 6.5)
    c.setFillColor(TEXT_DARK)
    
    for rule in rules:
        c.drawString(left_x, rule_y, rule)
        rule_y -= 4.5*mm
    
    # --- Vertical Divider ---
    divider_x = x + 95*mm
    c.setStrokeColor(BORDER_GRAY)
    c.setLineWidth(0.5)
    c.line(divider_x, y + 15*mm, divider_x, y + h - 15*mm)
    
    # --- Right Column: Contact Info ---
    right_x = divider_x + 5*mm
    right_y = left_y
    
    # CONTACT INFORMATION
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(DARK_NAVY)
    c.drawString(right_x, right_y, "CONTACT INFORMATION")
    
    # Gold underline
    c.setStrokeColor(GOLD_ACCENT)
    c.setLineWidth(1)
    c.line(right_x, right_y - 2*mm, right_x + 55*mm, right_y - 2*mm)
    
    # Contact details
    contact_y = right_y - 8*mm
    c.setFont("Helvetica", 6.5)
    c.setFillColor(TEXT_DARK)
    
    contacts = [
        "Nkolbisson, Yaoundé, Cameroon",
        "+237 222 23 45 67",
        "info@yibs.cm",
        "www.yibs.cm"
    ]
    
    for contact in contacts:
        c.drawString(right_x, contact_y, contact)
        contact_y -= 5*mm
    
    # OFFICE HOURS
    contact_y -= 5*mm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(DARK_NAVY)
    c.drawString(right_x, contact_y, "OFFICE HOURS")
    
    contact_y -= 6*mm
    c.setFont("Helvetica", 6.5)
    c.setFillColor(TEXT_DARK)
    c.drawString(right_x, contact_y, "Monday – Friday: 8:00 AM – 5:00 PM")
    contact_y -= 4.5*mm
    c.drawString(right_x, contact_y, "Saturday: 8:00 AM – 12:00 PM")
    
    # --- QR Code ---
    qr_size = 22*mm
    qr_x = x + (w/2) - (qr_size/2)
    qr_y = y + 10*mm
    
    # SCAN TO VERIFY
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(DARK_NAVY)
    c.drawCentredString(qr_x + qr_size/2, qr_y + qr_size + 4*mm, "SCAN TO VERIFY")
    
    # QR Code data
    qr_data = json.dumps({
        "student_id": student.get("student_id"),
        "name": f"{student.get('first_name','')} {student.get('last_name','')}",
        "speciality": student.get("speciality", ""),
        "level": student.get("level", ""),
        "school": "YIBS"
    }, ensure_ascii=False)
    
    qr_buf = _make_qr(qr_data)
    if qr_buf:
        # QR border
        c.setStrokeColor(DARK_NAVY)
        c.setLineWidth(1)
        c.rect(qr_x-1*mm, qr_y-1*mm, qr_size+2*mm, qr_size+2*mm, 
               stroke=1, fill=1)
        c.setFillColor(WHITE)
        c.rect(qr_x-1*mm, qr_y-1*mm, qr_size+2*mm, qr_size+2*mm, 
               fill=1, stroke=0)
        
        # Draw QR
        c.drawImage(ImageReader(qr_buf), qr_x, qr_y, qr_size, qr_size,
                    preserveAspectRatio=True, mask="auto")


# ─────────────────────────────────────────────────────────────────────────────
#  Main Generation Function
# ─────────────────────────────────────────────────────────────────────────────

def generate_id_card(student_data: dict, output_path: str) -> str:
    """Generate complete YIBS ID card with front and back on one page."""
    try:
        cv = canvas.Canvas(output_path, pagesize=(PAGE_W, PAGE_H))
        cv.setTitle(f"YIBS ID Card - {student_data.get('first_name','')} "
                    f"{student_data.get('last_name','')}")
        
        # Draw IDentix watermark in the center of the page
        _draw_watermark(cv, PAGE_W/2, PAGE_H/2, PAGE_W, PAGE_H)
        
        # Draw outer border
        cv.setStrokeColor(BORDER_GRAY)
        cv.setLineWidth(0.5)
        cv.rect(MARGIN, MARGIN, CARD_W, CARD_H, stroke=1, fill=0)
        
        # Calculate sections
        front_y = MARGIN + CARD_H - FRONT_INFO_H - HEADER_H
        back_y = MARGIN + 5*mm
        
        # Draw front section
        _draw_front_section(cv, MARGIN + 2*mm, front_y, 
                           CARD_W - 4*mm, FRONT_INFO_H + HEADER_H, 
                           student_data)
        
        # Draw back section
        _draw_back_section(cv, MARGIN + 2*mm, back_y, 
                          CARD_W - 4*mm, CARD_H - FRONT_INFO_H - HEADER_H - 10*mm, 
                          student_data)
        
        cv.save()
        return output_path
        
    except Exception as e:
        print(f"[pdf_generator] Error: {e}")
        import traceback
        traceback.print_exc()
        return None