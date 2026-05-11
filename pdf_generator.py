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
DARK_BLUE   = HexColor("#1A2C6B")
MID_BLUE    = HexColor("#1E4DB7")
LIGHT_BLUE  = HexColor("#4A90D9")
PURPLE      = HexColor("#4B3A9B")
WHITE       = white
BLACK       = black
GREY        = HexColor("#F5F7FA")
TEXT_DARK   = HexColor("#1A2C6B")
TEXT_BLUE   = HexColor("#1E4DB7")

# ── Card dimensions ────────────────────────────────────────────────────────────
CARD_W = 80 * mm
CARD_H = 50 * mm
MARGIN = 12 * mm
RADIUS = 3.5 * mm
GAP    = 8 * mm

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
    for i in range(steps):
        t = i / steps
        r = col1.red   + (col2.red   - col1.red)   * t
        g = col1.green + (col2.green - col1.green) * t
        b = col1.blue  + (col2.blue  - col1.blue)  * t
        c.setFillColor(HexColor((int(r*255)<<16)|(int(g*255)<<8)|int(b*255)))
        sw = w / steps
        c.rect(x + i*sw, y, sw+0.5, h, fill=1, stroke=0)


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
    if os.path.exists(LOGO_PATH):
        c.drawImage(ImageReader(LOGO_PATH), x, y, w, h,
                    preserveAspectRatio=True, anchor="c", mask="auto")


def _draw_watermark(c, ox, oy, W, H):
    if os.path.exists(IDENTIX_WATERMARK_PATH):
        c.saveState()
        identix_logo = ImageReader(IDENTIX_WATERMARK_PATH)
        img_w, img_h = identix_logo.getSize()
        aspect = img_h / img_w
        watermark_w = W * 0.5
        watermark_h = watermark_w * aspect
        if watermark_h > H * 0.5:
            watermark_h = H * 0.5
            watermark_w = watermark_h / aspect
        wm_x = ox + (W - watermark_w) / 2
        wm_y = oy + (H - watermark_h) / 2
        c.translate(wm_x + watermark_w / 2, wm_y + watermark_h / 2)
        c.rotate(45)
        c.translate(-(wm_x + watermark_w / 2), -(wm_y + watermark_h / 2))
        c.setFillAlpha(0.1)
        c.drawImage(identix_logo, wm_x, wm_y, watermark_w, watermark_h,
                    preserveAspectRatio=True, mask='auto')
        c.restoreState()


def _identix_logo(c, x, y):
    box_w, box_h = 11*mm, 8*mm
    _rounded_rect(c, x, y, box_w, box_h, 1.5*mm, MID_BLUE)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 1.5*mm, y + 2.5*mm, "iD")
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(DARK_BLUE)
    c.drawString(x + box_w + 1.5*mm, y + 2.5*mm, "IDentix")
    c.setFont("Helvetica", 4)
    c.setFillColor(HexColor("#888888"))
    c.drawString(x + box_w + 1.5*mm, y + 0.5*mm, "Smart Identity for Smart Schools")


def _info_row(c, lx, rx, y, label, value, val_color=None):
    c.setFont("Helvetica", 6)
    c.setFillColor(TEXT_DARK)
    c.drawString(lx, y, label)
    c.setFont("Helvetica-Bold", 6)
    c.setFillColor(val_color or TEXT_BLUE)
    c.drawString(rx, y, str(value or "—"))


# ─────────────────────────────────────────────────────────────────────────────
#  Vector footer icons (no image files needed)
# ─────────────────────────────────────────────────────────────────────────────

def _icon_location(c, cx, cy, s, color):
    """Pin / location drop shape."""
    c.saveState()
    c.setFillColor(color)
    c.setStrokeColor(color)
    r = s * 0.38
    # circle head
    c.circle(cx, cy + s*0.22, r, fill=1, stroke=0)
    # teardrop tail
    p = c.beginPath()
    p.moveTo(cx - r*0.75, cy + s*0.22)
    p.curveTo(cx - r*0.75, cy - s*0.28, cx, cy - s*0.52, cx, cy - s*0.52)
    p.curveTo(cx, cy - s*0.52, cx + r*0.75, cy - s*0.28, cx + r*0.75, cy + s*0.22)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    # white inner dot
    c.setFillColor(WHITE)
    c.circle(cx, cy + s*0.22, r*0.38, fill=1, stroke=0)
    c.restoreState()


def _icon_phone(c, cx, cy, s, color):
    """Simplified handset shape."""
    c.saveState()
    c.setFillColor(color)
    c.setStrokeColor(color)
    c.setLineWidth(s * 0.18)
    c.setLineCap(1)
    # draw as a rounded rectangle representing a mobile phone
    pw, ph = s*0.55, s*0.85
    px, py = cx - pw/2, cy - ph/2
    p = c.beginPath()
    rr = s * 0.1
    p.moveTo(px+rr, py)
    p.lineTo(px+pw-rr, py)
    p.arcTo(px+pw-2*rr, py, px+pw, py+2*rr, -90, 90)
    p.lineTo(px+pw, py+ph-rr)
    p.arcTo(px+pw-2*rr, py+ph-2*rr, px+pw, py+ph, 0, 90)
    p.lineTo(px+rr, py+ph)
    p.arcTo(px, py+ph-2*rr, px+2*rr, py+ph, 90, 90)
    p.lineTo(px, py+rr)
    p.arcTo(px, py, px+2*rr, py+2*rr, 180, 90)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    # white screen area
    c.setFillColor(WHITE)
    margin = s * 0.08
    c.rect(px+margin, py+ph*0.18, pw-margin*2, ph*0.58, fill=1, stroke=0)
    # white home button dot
    c.circle(cx, py + ph*0.08, s*0.07, fill=1, stroke=0)
    c.restoreState()


def _icon_globe(c, cx, cy, s, color):
    """Simple globe — circle with latitude/longitude lines."""
    c.saveState()
    r = s * 0.42
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(s * 0.12)
    # outer circle filled
    c.circle(cx, cy, r, fill=1, stroke=0)
    # white meridian lines
    c.setStrokeColor(WHITE)
    c.setLineWidth(s * 0.09)
    # vertical centre line
    c.line(cx, cy - r, cx, cy + r)
    # horizontal equator
    c.line(cx - r, cy, cx + r, cy)
    # oval curves for longitude
    c.arc(cx - r*0.5, cy - r, cx + r*0.5, cy + r, 0, 360)
    c.restoreState()


def _icon_email(c, cx, cy, s, color):
    """Envelope shape."""
    c.saveState()
    ew, eh = s*0.9, s*0.65
    ex, ey = cx - ew/2, cy - eh/2
    c.setFillColor(color)
    # envelope body
    c.rect(ex, ey, ew, eh, fill=1, stroke=0)
    # white flap (V shape)
    c.setFillColor(WHITE)
    p = c.beginPath()
    p.moveTo(ex, ey + eh)
    p.lineTo(cx, ey + eh*0.42)
    p.lineTo(ex + ew, ey + eh)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    # white bottom triangle to create open envelope look
    p2 = c.beginPath()
    p2.moveTo(ex, ey)
    p2.lineTo(cx, ey + eh*0.48)
    p2.lineTo(ex + ew, ey)
    p2.close()
    c.drawPath(p2, fill=1, stroke=0)
    c.restoreState()


_VECTOR_ICONS = {
    "location": _icon_location,
    "phone":    _icon_phone,
    "globe":    _icon_globe,
    "email":    _icon_email,
}


# ─────────────────────────────────────────────────────────────────────────────
#  FRONT
# ─────────────────────────────────────────────────────────────────────────────

def _draw_front(c, ox, oy, student, card):
    W, H = CARD_W, CARD_H

    _rounded_rect(c, ox, oy, W, H, RADIUS, WHITE,
                  stroke=HexColor("#CCCCCC"), stroke_w=0.5)

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

    # Purple wave
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
    logo_size = 16*mm
    _draw_logo(c, ox+3*mm, oy+H-logo_size-2*mm, logo_size, logo_size)

    SCHOOL_BLUE = HexColor("#1B75BB")
    GOLD        = HexColor("#C8963E")

    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(SCHOOL_BLUE)
    c.drawString(ox+21*mm, oy+H-8*mm, "YAOUNDE INTERNATIONAL")
    c.drawString(ox+21*mm, oy+H-13*mm, "BUSINESS SCHOOL")

    # CHANGE 1: Slogan updated to "Developing Innovative Professionals"
    c.setFont("Helvetica-Oblique", 5.5)
    c.setFillColor(SCHOOL_BLUE)
    c.drawString(ox+21*mm, oy+H-17*mm, "Developing Innovative Professionals")

    # REMOVED: gold accent line and divider line under header

    # Watermark
    _draw_watermark(c, ox, oy, W, H)

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
    first = student.get("first_name", "")
    last  = student.get("last_name", "")

    # CHANGE 2: Academic year displayed in the blue bottom banner (white text)
    acad_year = f"{datetime.now().year} — {datetime.now().year + 1}"
    c.setFont("Helvetica-Bold", 6.5)
    c.setFillColor(WHITE)
    c.drawRightString(ox + W - 3*mm, oy + 2.5*mm, f"Academic Year:  {acad_year}")

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(DARK_BLUE)
    c.drawString(nx, ny, f"{first} {last}")

    # CHANGE 3: Only the gold underline beneath the name is kept
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    c.line(nx, ny - 1.5*mm, ox + W - 3*mm, ny - 1.5*mm)

    # ── Info grid ─────────────────────────────────────────────────────────────
    col1_lbl = nx
    col1_val = nx + 14*mm
    col2_lbl = nx + (W - nx + ox) / 2 - ox + ox + 5*mm
    col2_val = col2_lbl + 13*mm

    mid_x = (col1_lbl + col2_lbl) / 2 + 10*mm
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(0.4)
    c.line(mid_x, ny-3*mm, mid_x, oy+9.5*mm)

    rows_left = [
        ("Student ID",    student.get("student_id", ""),                              TEXT_BLUE),
        ("Date of Birth", student.get("date_of_birth", ""),                           TEXT_BLUE),
        ("Program",       student.get("speciality", student.get("department", "")),   TEXT_BLUE),
        ("Level",         student.get("level", ""),                                   TEXT_BLUE),
    ]

    rows_right = [
        ("Campus",      student.get("campus", ""),       TEXT_BLUE),
        ("Issue Date",  card.get("issued_date", ""),     TEXT_BLUE),
        ("Valid Until", card.get("expire_date", ""),     TEXT_BLUE),
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

    # ── Header ────────────────────────────────────────────────────────────────
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

    # ── Right body: QR code — CHANGE 4: shifted further right ────────────────
    qr_size = 20*mm
    qr_x = ox + W*0.52 + 6*mm   # shifted right by extra 3 mm
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

    # ── Footer icons (vector-drawn, no image files needed) ───────────────────
    contact  = student.get("contact", student.get("emergency_phone", ""))
    email    = student.get("email", "")
    website  = student.get("website", "www.yibs.cm")

    # Footer sits inside the blue bar (oy to oy+9mm). Centre icons vertically.
    footer_mid_y = oy + 4.5*mm   # vertical centre of the 9 mm bar

    # Four evenly spaced items across the full card width
    items = [
        ("location", "Yaounde, Cameroon"),
        ("phone",    contact if contact else "+237 000 000 000"),
        ("globe",    website),
        ("email",    email if email else "info@yibs.cm"),
    ]

    icon_s   = 3.5 * mm          # icon size
    n        = len(items)
    slot_w   = CARD_W / n        # width allocated per item

    for idx, (icon_key, text) in enumerate(items):
        slot_cx = ox + slot_w * idx + slot_w / 2   # horizontal centre of slot

        # Draw vector icon centred in slot, vertically centred in footer bar
        icon_fn = _VECTOR_ICONS.get(icon_key)
        if icon_fn:
            icon_fn(c, slot_cx, footer_mid_y + icon_s * 0.15, icon_s, WHITE)

        # Label text below the icon
        c.setFont("Helvetica", 4)
        c.setFillColor(WHITE)
        c.drawCentredString(slot_cx, footer_mid_y - icon_s * 0.72, text)


# ─────────────────────────────────────────────────────────────────────────────
#  Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def generate_id_card(student: dict, card: dict, output_path: str) -> str:
    """
    Generate a PDF ID card (front + back side by side) and save to *output_path*.

    Parameters
    ----------
    student : dict
        Keys: first_name, last_name, student_id, date_of_birth, department,
              speciality, level, campus, nationality, gender, contact, email,
              address, city, school, photo_url, website
    card : dict
        Keys: issued_date, expire_date
    output_path : str
        Destination file path, e.g. "YIBS_StudentID_JS001.pdf"

    Returns
    -------
    str  — the resolved absolute path of the saved PDF
    """
    # ── Page size: two cards side by side with margins ────────────────────────
    page_w = CARD_W * 2 + GAP + MARGIN * 2
    page_h = CARD_H + MARGIN * 2

    c = canvas.Canvas(output_path, pagesize=(page_w, page_h))

    front_ox = MARGIN
    front_oy = MARGIN
    back_ox  = MARGIN + CARD_W + GAP
    back_oy  = MARGIN

    _draw_front(c, front_ox, front_oy, student, card)
    _draw_back (c, back_ox,  back_oy,  student, card)

    c.save()
    return os.path.abspath(output_path)


