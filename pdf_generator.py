"""
IDentix PDF ID Card Generator
Matches the YIBS IDentix card design — Front + Back on one page.
Requires: reportlab, Pillow, qrcode
Install:  pip install reportlab Pillow qrcode
"""

import io
import os
import json
import hashlib
from datetime import datetime, timedelta

from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ── Brand colours ─────────────────────────────────────────────────────────────
DARK_BLUE   = HexColor("#1A2C6B")   # deep navy
MID_BLUE    = HexColor("#1E4DB7")   # main blue
LIGHT_BLUE  = HexColor("#4A90D9")   # accent blue
PURPLE      = HexColor("#4B3A9B")   # purple accent
WHITE       = white
BLACK       = black
GREY        = HexColor("#F5F7FA")   # card background
TEXT_DARK   = HexColor("#1A2C6B")
TEXT_BLUE   = HexColor("#1E4DB7")

# ── Card dimensions (slightly reduced from CR80) ──────────────────────────────
CARD_W = 80 * mm
CARD_H = 50 * mm
MARGIN = 12 * mm
RADIUS = 3.5 * mm
GAP    = 8 * mm   # gap between front and back

# ── Asset paths ───────────────────────────────────────────────────────────────
_HERE     = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(_HERE, "school_logo.png")
ICON_LOCATION = os.path.join(_HERE, "icon_location.png")
ICON_PHONE    = os.path.join(_HERE, "icon_phone.png")
ICON_GLOBE    = os.path.join(_HERE, "icon_globe.png")
ICON_EMAIL    = os.path.join(_HERE, "icon_email.png")
IDENTIX_WATERMARK_PATH = os.path.join(_HERE, "identix_logo.png")


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _rounded_rect(c, x, y, w, h, r, fill, stroke=None, stroke_w=0.5):
    c.saveState()
    c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(stroke_w)
    p = c.beginPath()
    p.moveTo(x+r, y)
    p.lineTo(x+w-r, y)
    p.arcTo(x+w-2*r, y, x+w, y+2*r, -90, 90)
    p.lineTo(x+w, y+h-r)
    p.arcTo(x+w-2*r, y+h-2*r, x+w, y+h, 0, 90)
    p.lineTo(x+r, y+h)
    p.arcTo(x, y+h-2*r, x+2*r, y+h, 90, 90)
    p.lineTo(x, y+r)
    p.arcTo(x, y, x+2*r, y+2*r, 180, 90)
    p.close()
    c.drawPath(p, fill=1, stroke=1 if stroke else 0)
    c.restoreState()


def _clip_round(c, x, y, w, h, r):
    p = c.beginPath()
    p.moveTo(x+r, y)
    p.lineTo(x+w-r, y)
    p.arcTo(x+w-2*r, y, x+w, y+2*r, -90, 90)
    p.lineTo(x+w, y+h-r)
    p.arcTo(x+w-2*r, y+h-2*r, x+w, y+h, 0, 90)
    p.lineTo(x+r, y+h)
    p.arcTo(x, y+h-2*r, x+2*r, y+h, 90, 90)
    p.lineTo(x, y+r)
    p.arcTo(x, y, x+2*r, y+2*r, 180, 90)
    p.close()
    c.clipPath(p, stroke=0)


def _gradient_h(c, x, y, w, h, col1, col2, steps=40):
    """Horizontal gradient (left→right)."""
    for i in range(steps):
        t = i / steps
        r = col1.red   + (col2.red   - col1.red)   * t
        g = col1.green + (col2.green - col1.green) * t
        b = col1.blue  + (col2.blue  - col1.blue)  * t
        c.setFillColor(HexColor((int(r*255)<<16)|(int(g*255)<<8)|int(b*255)))
        sw = w / steps
        c.rect(x + i*sw, y, sw+0.5, h, fill=1, stroke=0)


def _wave(c, ox, oy, w, h, color):
    """Draw decorative wave curves (right side of card)."""
    c.saveState()
    c.setFillColor(color)
    # outer wave
    p = c.beginPath()
    p.moveTo(ox + w, oy + h)
    p.curveTo(ox + w - 15*mm, oy + h,
              ox + w - 10*mm, oy + h * 0.6,
              ox + w,         oy + h * 0.4)
    p.lineTo(ox + w, oy + h)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def _make_qr(data: str) -> io.BytesIO:
    try:
        import qrcode
        qr = qrcode.QRCode(version=None,
                           error_correction=qrcode.constants.ERROR_CORRECT_M,
                           box_size=10, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1A2C6B", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except ImportError:
        # Pillow-only fallback
        try:
            from PIL import Image, ImageDraw
            sz = 200
            img = Image.new("RGB", (sz, sz), "white")
            draw = ImageDraw.Draw(img)
            draw.rectangle([2, 2, sz-2, sz-2], outline="#1A2C6B", width=3)
            for fx, fy in [(8,8),(sz-48,8),(8,sz-48)]:
                draw.rectangle([fx,fy,fx+38,fy+38], outline="#1A2C6B", width=3)
                draw.rectangle([fx+8,fy+8,fx+28,fy+28], fill="#1A2C6B")
            step=8
            for row in range(7, sz//step-3):
                for col in range(7, sz//step-3):
                    h2=hashlib.md5(f"{data}{row}{col}".encode()).hexdigest()
                    if int(h2[0],16)>7:
                        px,py=col*step,row*step
                        if not(px<50 and py<50) and not(px>sz-55 and py<50)\
                           and not(px<50 and py>sz-55):
                            draw.rectangle([px,py,px+5,py+5],fill="#1A2C6B")
            buf=io.BytesIO()
            img.save(buf,format="PNG")
            buf.seek(0)
            return buf
        except Exception:
            return None


def _draw_logo(c, x, y, w, h):
    """Draw school logo if file exists, else skip."""
    if os.path.exists(LOGO_PATH):
        c.drawImage(ImageReader(LOGO_PATH), x, y, w, h,
                    preserveAspectRatio=True, anchor="c", mask="auto")


def _draw_watermark(c, ox, oy, W, H):
    if os.path.exists(IDENTIX_WATERMARK_PATH):
        c.saveState()
        identix_logo = ImageReader(IDENTIX_WATERMARK_PATH)
        # Calculate size to fit within card, maintaining aspect ratio
        img_w, img_h = identix_logo.getSize()
        aspect = img_h / img_w
        
        # Target watermark size (e.g., 50% of card width)
        watermark_w = W * 0.5
        watermark_h = watermark_w * aspect

        # Ensure watermark doesn't exceed card height
        if watermark_h > H * 0.5:
            watermark_h = H * 0.5
            watermark_w = watermark_h / aspect

        # Center the watermark
        wm_x = ox + (W - watermark_w) / 2
        wm_y = oy + (H - watermark_h) / 2

        c.translate(wm_x + watermark_w / 2, wm_y + watermark_h / 2)
        c.rotate(45) # Rotate by 45 degrees
        c.translate(-(wm_x + watermark_w / 2), -(wm_y + watermark_h / 2))

        c.setFillAlpha(0.1) # Set transparency
        c.drawImage(identix_logo, wm_x, wm_y, watermark_w, watermark_h,
                    preserveAspectRatio=True, mask='auto')
        c.restoreState()

def _identix_logo(c, x, y):
    """Draw the IDentix brand mark (styled text)."""
    # iD box
    box_w, box_h = 11*mm, 8*mm
    _rounded_rect(c, x, y, box_w, box_h, 1.5*mm, MID_BLUE)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 1.5*mm, y + 2.5*mm, "iD")
    # IDentix text
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(DARK_BLUE)
    c.drawString(x + box_w + 1.5*mm, y + 2.5*mm, "IDentix")
    # tagline
    c.setFont("Helvetica", 4)
    c.setFillColor(HexColor("#888888"))
    c.drawString(x + box_w + 1.5*mm, y + 0.5*mm, "Smart Identity for Smart Schools")


def _info_row(c, lx, rx, y, label, value, val_color=None):
    """Draw a label + value row."""
    c.setFont("Helvetica", 6)
    c.setFillColor(TEXT_DARK)
    c.drawString(lx, y, label)
    c.setFont("Helvetica-Bold", 6)
    c.setFillColor(val_color or TEXT_BLUE)
    c.drawString(rx, y, str(value or "—"))


# ─────────────────────────────────────────────────────────────────────────────
#  FRONT
# ─────────────────────────────────────────────────────────────────────────────

def _draw_front(c, ox, oy, student, card):
    W, H = CARD_W, CARD_H

    # Card base (white with shadow border)
    _rounded_rect(c, ox, oy, W, H, RADIUS, WHITE,
                  stroke=HexColor("#CCCCCC"), stroke_w=0.5)

    # ── Right wave decoration ─────────────────────────────────────────────────
    c.saveState()
    _clip_round(c, ox, oy, W, H, RADIUS)

    # Dark blue wave
    c.setFillColor(DARK_BLUE)
    p = c.beginPath()
    p.moveTo(ox+W, oy+H)
    p.curveTo(ox+W-18*mm, oy+H, ox+W-12*mm, oy+H*0.55, ox+W, oy+H*0.38)
    p.lineTo(ox+W, oy+H)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # Purple wave (smaller, on top)
    c.setFillColor(PURPLE)
    p2 = c.beginPath()
    p2.moveTo(ox+W, oy+H)
    p2.curveTo(ox+W-10*mm, oy+H, ox+W-6*mm, oy+H*0.72, ox+W, oy+H*0.58)
    p2.lineTo(ox+W, oy+H)
    p2.close()
    c.drawPath(p2, fill=1, stroke=0)

    # Bottom blue bar
    c.setFillColor(MID_BLUE)
    c.rect(ox, oy, W, 8*mm, fill=1, stroke=0)

    # Bottom purple wave
    c.setFillColor(DARK_BLUE)
    p3 = c.beginPath()
    p3.moveTo(ox, oy)
    p3.curveTo(ox+15*mm, oy, ox+20*mm, oy+8*mm, ox+35*mm, oy+8*mm)
    p3.lineTo(ox, oy+8*mm)
    p3.close()
    c.drawPath(p3, fill=1, stroke=0)

    c.restoreState()

    # ── Header ────────────────────────────────────────────────────────────────
    # School logo
    logo_size = 16*mm
    _draw_logo(c, ox+3*mm, oy+H-logo_size-2*mm, logo_size, logo_size)

    
 # School name — color matches YIBS logo blue
    SCHOOL_BLUE = HexColor("#1B75BB")
    GOLD        = HexColor("#C8963E")

    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(SCHOOL_BLUE)
    c.drawString(ox+21*mm, oy+H-8*mm, "YAOUNDE INTERNATIONAL")
    c.drawString(ox+21*mm, oy+H-13*mm, "BUSINESS SCHOOL")

    # Gold accent line under school name
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    c.line(ox+21*mm, oy+H-14*mm, ox+W-5*mm, oy+H-14*mm)

    c.setFont("Helvetica-Oblique", 5.5)
    c.setFillColor(SCHOOL_BLUE)
    c.drawString(ox+21*mm, oy+H-17*mm, "Training Innovative Professionals")

    # Watermark
    _draw_watermark(c, ox, oy, W, H)

    # Divider line
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(0.5)
    c.line(ox+3*mm, oy+H-19*mm, ox+W-3*mm, oy+H-19*mm)

    # ── Photo ─────────────────────────────────────────────────────────────────
    ph_x = ox + 3*mm
    ph_y = oy + 9*mm
    ph_w = 16*mm
    ph_h = 20*mm

    _rounded_rect(c, ph_x-0.5*mm, ph_y-0.5*mm,
                  ph_w+1*mm, ph_h+1*mm, 1.5*mm, MID_BLUE)
    _rounded_rect(c, ph_x, ph_y, ph_w, ph_h, 1*mm, GREY)

    photo_url = student.get("photo_url", "")
    drawn = False
    if photo_url and photo_url.startswith("http"):
        try:
            import urllib.request
            req = urllib.request.Request(photo_url,
                  headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                img_data = io.BytesIO(resp.read())
            c.saveState()
            _clip_round(c, ph_x, ph_y, ph_w, ph_h, 1*mm)
            c.drawImage(ImageReader(img_data), ph_x, ph_y, ph_w, ph_h,
                        preserveAspectRatio=True, anchor="c", mask="auto")
            c.restoreState()
            drawn = True
        except Exception:
            pass
    if not drawn:
        c.setFont("Helvetica", 4)
        c.setFillColor(HexColor("#AAAAAA"))
        c.drawCentredString(ph_x+ph_w/2, ph_y+ph_h/2, "PHOTO")

    # STUDENT badge
    badge_y = ph_y + ph_h + 1.5*mm
    _rounded_rect(c, ph_x, badge_y, ph_w, 4*mm, 1*mm, MID_BLUE)
    c.setFont("Helvetica-Bold", 6)
    c.setFillColor(WHITE)
    c.drawCentredString(ph_x+ph_w/2, badge_y+1.2*mm, "STUDENT")

    # ── Student name ──────────────────────────────────────────────────────────
    nx = ph_x + ph_w + 3*mm 
    ny = oy + H - 22*mm
    ny = oy + H - 22*mm
    first = student.get("first_name", "")
    last  = student.get("last_name", "")
    GOLD  = HexColor("#C8963E")

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(DARK_BLUE)
    c.drawString(nx, ny, f"{first} {last}")

    # Gold underline under name
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    c.line(nx, ny-1.5*mm, ox+W-3*mm, ny-1.5*mm)

    # Academic year — small, fits in available space
    acad_year = f"Academic Year: {datetime.now().year} — {datetime.now().year + 1}"
    c.setFont("Helvetica", 4.5)
    c.setFillColor(HexColor("#888888"))
    c.drawRightString(ox+W-3*mm, ny-4*mm, acad_year)

    # ── Info grid (2 columns) ─────────────────────────────────────────────────
    col1_lbl = nx
    col1_val = nx + 14*mm
    col2_lbl = nx + (W - nx + ox) / 2 - ox + ox + 5*mm
    col2_val = col2_lbl + 13*mm

    # vertical divider between columns
    mid_x = (col1_lbl + col2_lbl) / 2 + 10*mm
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(0.4)
    c.line(mid_x, ny-3*mm, mid_x, oy+9.5*mm)

    rows_left = [
        ("Student ID",     student.get("student_id", ""),    TEXT_BLUE),
        ("Date of Birth",  student.get("date_of_birth", ""), TEXT_BLUE),
        ("Program",        student.get("speciality", student.get("department","")), TEXT_BLUE),
        ("Level",          student.get("level", ""),          TEXT_BLUE),
    ]
    
    rows_right = [
    ("Campus",      student.get("campus", ""),        TEXT_BLUE),
    ("Issue Date",  card.get("issued_date", ""),      TEXT_BLUE),
    ("Valid Until", card.get("expire_date", ""),      TEXT_BLUE),
    ]
    

    row_gap = 4.8*mm
    start_y = ny - 5*mm
    for i, (lbl, val, vcol) in enumerate(rows_left):
        ry = start_y - i * row_gap
        _info_row(c, col1_lbl, col1_val, ry, lbl, val, vcol)

    for i, (lbl, val, vcol) in enumerate(rows_right):
        ry = start_y - i * row_gap
        _info_row(c, col2_lbl, col2_val, ry, lbl, val, vcol)


# ─────────────────────────────────────────────────────────────────────────────
#  BACK
# ─────────────────────────────────────────────────────────────────────────────

def _draw_back(c, ox, oy, student, card):
    W, H = CARD_W, CARD_H

    # Card base
    _rounded_rect(c, ox, oy, W, H, RADIUS, WHITE,
                  stroke=HexColor("#CCCCCC"), stroke_w=0.5)

    c.saveState()
    _clip_round(c, ox, oy, W, H, RADIUS)

    # Blue header
    c.setFillColor(MID_BLUE)
    c.rect(ox, oy+H-18*mm, W, 18*mm, fill=1, stroke=0)

    # Right wave decorations
    c.setFillColor(DARK_BLUE)
    p = c.beginPath()
    p.moveTo(ox+W, oy+H)
    p.curveTo(ox+W-15*mm, oy+H, ox+W-10*mm, oy+H-10*mm, ox+W, oy+H-18*mm)
    p.lineTo(ox+W, oy+H)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    c.setFillColor(PURPLE)
    p2 = c.beginPath()
    p2.moveTo(ox+W, oy+H)
    p2.curveTo(ox+W-8*mm, oy+H, ox+W-5*mm, oy+H-7*mm, ox+W, oy+H-12*mm)
    p2.lineTo(ox+W, oy+H)
    p2.close()
    c.drawPath(p2, fill=1, stroke=0)

    # Bottom blue footer
    c.setFillColor(MID_BLUE)
    c.rect(ox, oy, W, 9*mm, fill=1, stroke=0)

    # Bottom left wave
    c.setFillColor(DARK_BLUE)
    p3 = c.beginPath()
    p3.moveTo(ox, oy)
    p3.curveTo(ox+12*mm, oy, ox+18*mm, oy+9*mm, ox+32*mm, oy+9*mm)
    p3.lineTo(ox, oy+9*mm)
    p3.close()
    c.drawPath(p3, fill=1, stroke=0)

    c.restoreState()

    # Watermark
    _draw_watermark(c, ox, oy, W, H)

    # ── Header: logo + school name ────────────────────────────────────────────
    logo_sz = 13*mm
    _draw_logo(c, ox+3*mm, oy+H-logo_sz-2.5*mm, logo_sz, logo_sz)

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(WHITE)
    c.drawString(ox+18*mm, oy+H-8*mm, "YAOUNDE INTERNATIONAL")
    c.drawString(ox+18*mm, oy+H-12.5*mm, "BUSINESS SCHOOL")
    c.setFont("Helvetica-Oblique", 5)
    c.setFillColor(HexColor("#C8E0FF"))
    c.drawString(ox+18*mm, oy+H-16.5*mm, "Developing Innovative Professionals")

    # Vertical divider
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(0.5)
    c.line(ox+W*0.52, oy+9.5*mm, ox+W*0.52, oy+H-19*mm)

    # ── Left body: disclaimer text ────────────────────────────────────────────
    txt_x = ox + 3*mm
    txt_y = oy + H - 22*mm
    c.setFont("Helvetica", 5.5)
    c.setFillColor(TEXT_DARK)
    lines = [
        "This card is the property of Yaounde International",
        "Business School and is issued for identification",
        "purposes only. If found, please return to the",
        "administration office.",
    ]
    for i, line in enumerate(lines):
        c.drawString(txt_x, txt_y - i*4.5*mm, line)

    # ── Right body: QR code ───────────────────────────────────────────────────
    qr_size = 20*mm
    qr_x = ox + W*0.52 + 3*mm
    qr_y = oy + H - 19*mm - qr_size - 1*mm

    qr_data = json.dumps({  
    "student_id":    student.get("student_id"),
    "name":          f"{student.get('first_name','')} {student.get('last_name','')}",
    "email":         student.get("email", ""),
    "department":    student.get("department", ""),
    "speciality":    student.get("speciality", ""),
    "level":         student.get("level", ""),
    "campus":        student.get("campus", ""),
    "nationality":   student.get("nationality", ""),
    "date_of_birth": student.get("date_of_birth", ""),
    "gender":        student.get("gender", ""),
    "contact":       student.get("contact", ""),
    "address":       student.get("address", ""),
    "city":          student.get("city", ""),
    "school":        student.get("school", ""),
    "photo_url":     student.get("photo_url", ""),
    "issued":        card.get("issued_date", ""),
    "expires":       card.get("expire_date", ""),
}, ensure_ascii=False)

    qr_buf = _make_qr(qr_data)
    if qr_buf:
        _rounded_rect(c, qr_x-0.5*mm, qr_y-0.5*mm,
                      qr_size+1*mm, qr_size+1*mm, 1*mm,
                      WHITE, stroke=MID_BLUE, stroke_w=1)
        c.drawImage(ImageReader(qr_buf), qr_x, qr_y, qr_size, qr_size,
                    preserveAspectRatio=True, mask='auto')

    # Student ID under QR
    sid = student.get("student_id", "")
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(MID_BLUE)
    c.drawCentredString(qr_x + qr_size/2, qr_y - 4*mm, sid)

    # ── Footer icons ──────────────────────────────────────────────────────────
    contact = student.get("contact", student.get("emergency_phone", ""))
    footer_y = oy + 2*mm

    items = [
        (ICON_LOCATION, "Yaounde, Cameroon"),
        (ICON_PHONE,    contact or "+237 6XX XXX XXX"),
        (ICON_GLOBE,    "www.yibs.cm"),
        (ICON_EMAIL,    "info@yibs.cm"),
    ]

    spacing = W / len(items)
    icon_size = 4*mm

    for i, (icon_path, text) in enumerate(items):
        fx = ox + i * spacing + spacing / 2

        # Draw icon if file exists
        if os.path.exists(icon_path):
            c.drawImage(
                ImageReader(icon_path),
                fx - icon_size / 2,
                footer_y + 3.5*mm,
                icon_size,
                icon_size,
                preserveAspectRatio=True,
                mask="auto"
            )

        # Text below icon
        c.setFont("Helvetica", 4.2)
        c.setFillColor(WHITE)
        c.drawCentredString(fx, footer_y + 1*mm, text)
# ─────────────────────────────────────────────────────────────────────────────
#  Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def generate_id_card(student_data: dict, output_path: str) -> str:
    try:
        issued = student_data.get("issued_date",
                                  datetime.now().strftime("%Y-%m-%d"))
        expire = student_data.get("expire_date",
                                  (datetime.now() + timedelta(days=365))
                                  .strftime("%Y-%m-%d"))
        card = {"issued_date": issued, "expire_date": expire}

        page_w = CARD_W * 2 + MARGIN * 3 + GAP
        page_h = CARD_H + MARGIN * 2

        cv = canvas.Canvas(output_path, pagesize=(page_w, page_h))
        cv.setTitle("IDentix — " + student_data.get("first_name", "") + " " + student_data.get("last_name", ""))

        _draw_front(cv, MARGIN, MARGIN, student_data, card)
        _draw_back(cv, MARGIN*2 + CARD_W + GAP, MARGIN, student_data, card)

        cv.save()
        return output_path

    except Exception as e:
        print(f"[pdf_generator] Error: {e}")
        import traceback; traceback.print_exc()
        return None