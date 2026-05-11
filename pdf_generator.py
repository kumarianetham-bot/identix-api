"""
IDentix PDF ID Card Generator
Matches the YIBS IDentix card design — Front + Back on one page.
Requires: reportlab, Pillow, qrcode
Install:  pip install reportlab Pillow qrcode
"""


import io, os, json, hashlib
from datetime import datetime, timedelta
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

DARK_BLUE  = HexColor("#1A2C6B")
MID_BLUE   = HexColor("#1E4DB7")
PURPLE     = HexColor("#4B3A9B")
SCHOOL_BLUE= HexColor("#1B75BB")
GOLD       = HexColor("#C8963E")
WHITE      = white
GREY       = HexColor("#F5F7FA")
TEXT_DARK  = HexColor("#1A2C6B")
TEXT_BLUE  = HexColor("#1E4DB7")

CARD_W = 86 * mm
CARD_H = 54 * mm
MARGIN = 10 * mm
RADIUS = 3   * mm
GAP    = 8   * mm

_HERE     = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(_HERE, "school_logo.png")

ICON_LOCATION = os.path.join(_HERE, "icon_location.png")
ICON_PHONE    = os.path.join(_HERE, "icon_phone.png")
ICON_GLOBE    = os.path.join(_HERE, "icon_globe.png")
ICON_EMAIL    = os.path.join(_HERE, "icon_email.png")


def _rrect(c, x, y, w, h, r, fill, stroke=None, sw=0.5):
    c.saveState()
    c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke); c.setLineWidth(sw)
    p = c.beginPath()
    p.moveTo(x+r,y); p.lineTo(x+w-r,y)
    p.arcTo(x+w-2*r,y,x+w,y+2*r,-90,90)
    p.lineTo(x+w,y+h-r)
    p.arcTo(x+w-2*r,y+h-2*r,x+w,y+h,0,90)
    p.lineTo(x+r,y+h)
    p.arcTo(x,y+h-2*r,x+2*r,y+h,90,90)
    p.lineTo(x,y+r)
    p.arcTo(x,y,x+2*r,y+2*r,180,90)
    p.close()
    c.drawPath(p, fill=1, stroke=1 if stroke else 0)
    c.restoreState()


def _clip_rrect(c, x, y, w, h, r):
    p = c.beginPath()
    p.moveTo(x+r,y); p.lineTo(x+w-r,y)
    p.arcTo(x+w-2*r,y,x+w,y+2*r,-90,90)
    p.lineTo(x+w,y+h-r)
    p.arcTo(x+w-2*r,y+h-2*r,x+w,y+h,0,90)
    p.lineTo(x+r,y+h)
    p.arcTo(x,y+h-2*r,x+2*r,y+h,90,90)
    p.lineTo(x,y+r)
    p.arcTo(x,y,x+2*r,y+2*r,180,90)
    p.close()
    c.clipPath(p, stroke=0)


def _logo(c, x, y, w, h):
    if os.path.exists(LOGO_PATH):
        c.drawImage(ImageReader(LOGO_PATH), x, y, w, h,
                    preserveAspectRatio=True, anchor="c", mask="auto")


def _make_qr(data):
    try:
        import qrcode
        qr = qrcode.QRCode(version=None,
                           error_correction=qrcode.constants.ERROR_CORRECT_M,
                           box_size=10, border=2)
        qr.add_data(data); qr.make(fit=True)
        img = qr.make_image(fill_color="#1A2C6B", back_color="white")
        buf = io.BytesIO(); img.save(buf, "PNG"); buf.seek(0)
        return buf
    except ImportError:
        try:
            from PIL import Image, ImageDraw
            sz=200; img=Image.new("RGB",(sz,sz),"white")
            draw=ImageDraw.Draw(img)
            draw.rectangle([2,2,sz-2,sz-2],outline="#1A2C6B",width=3)
            for fx,fy in [(8,8),(sz-48,8),(8,sz-48)]:
                draw.rectangle([fx,fy,fx+38,fy+38],outline="#1A2C6B",width=3)
                draw.rectangle([fx+8,fy+8,fx+28,fy+28],fill="#1A2C6B")
            for row in range(7,sz//8-3):
                for col in range(7,sz//8-3):
                    h2=hashlib.md5(f"{data}{row}{col}".encode()).hexdigest()
                    if int(h2[0],16)>7:
                        px2,py2=col*8,row*8
                        if not(px2<50 and py2<50) and not(px2>sz-55 and py2<50)\
                           and not(px2<50 and py2>sz-55):
                            draw.rectangle([px2,py2,px2+5,py2+5],fill="#1A2C6B")
            buf=io.BytesIO(); img.save(buf,"PNG"); buf.seek(0); return buf
        except: return None


def _front(c, ox, oy, student, card):
    W, H = CARD_W, CARD_H

    _rrect(c, ox, oy, W, H, RADIUS, WHITE, stroke=HexColor("#CCCCCC"), sw=0.4)

    c.saveState()
    _clip_rrect(c, ox, oy, W, H, RADIUS)

    # Right waves
    c.setFillColor(DARK_BLUE)
    p = c.beginPath()
    p.moveTo(ox+W, oy+H)
    p.curveTo(ox+W-22*mm, oy+H, ox+W-14*mm, oy+H*0.50, ox+W, oy+H*0.33)
    p.lineTo(ox+W, oy+H); p.close()
    c.drawPath(p, fill=1, stroke=0)

    c.setFillColor(PURPLE)
    p2 = c.beginPath()
    p2.moveTo(ox+W, oy+H)
    p2.curveTo(ox+W-12*mm, oy+H, ox+W-7*mm, oy+H*0.70, ox+W, oy+H*0.55)
    p2.lineTo(ox+W, oy+H); p2.close()
    c.drawPath(p2, fill=1, stroke=0)

    # Bottom bar
    c.setFillColor(MID_BLUE)
    c.rect(ox, oy, W, 7.5*mm, fill=1, stroke=0)

    c.setFillColor(DARK_BLUE)
    p3 = c.beginPath()
    p3.moveTo(ox, oy)
    p3.curveTo(ox+14*mm, oy, ox+20*mm, oy+7.5*mm, ox+36*mm, oy+7.5*mm)
    p3.lineTo(ox, oy+7.5*mm); p3.close()
    c.drawPath(p3, fill=1, stroke=0)

    c.restoreState()

    # ✅ Academic year in bottom blue footer
    acad_year = f"Academic Year:  {datetime.now().year} — {datetime.now().year + 1}"
    c.setFont("Helvetica-Bold", 5.5)
    c.setFillColor(WHITE)
    c.drawCentredString(ox + W/2, oy + 2.5*mm, acad_year)

    # Logo
    lsz = 15*mm
    _logo(c, ox+3*mm, oy+H-lsz-2*mm, lsz, lsz)

    # School name in SCHOOL_BLUE
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(SCHOOL_BLUE)
    c.drawString(ox+20*mm, oy+H-8*mm,  "YAOUNDE INTERNATIONAL")
    c.drawString(ox+20*mm, oy+H-13*mm, "BUSINESS SCHOOL")

    c.setFont("Helvetica-Oblique", 5.5)
    c.setFillColor(SCHOOL_BLUE)
    c.drawString(ox+20*mm, oy+H-16.5*mm, "Developing Innovative Professionals")

    # Photo
    ph_x=ox+3*mm; ph_y=oy+8.5*mm; ph_w=17*mm; ph_h=22*mm
    _rrect(c, ph_x-0.8*mm, ph_y-0.8*mm, ph_w+1.6*mm, ph_h+1.6*mm, 2*mm, MID_BLUE)
    _rrect(c, ph_x, ph_y, ph_w, ph_h, 1.5*mm, GREY)

    drawn = False
    photo_url = student.get("photo_url","")
    if photo_url and photo_url.startswith("http"):
        try:
            import urllib.request
            req = urllib.request.Request(photo_url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                img_data = io.BytesIO(r.read())
            c.saveState()
            _clip_rrect(c, ph_x, ph_y, ph_w, ph_h, 1.5*mm)
            c.drawImage(ImageReader(img_data), ph_x, ph_y, ph_w, ph_h,
                        preserveAspectRatio=True, anchor="c", mask="auto")
            c.restoreState(); drawn=True
        except: pass
    if not drawn:
        c.setFont("Helvetica",4); c.setFillColor(HexColor("#AAAAAA"))
        c.drawCentredString(ph_x+ph_w/2, ph_y+ph_h/2, "PHOTO")

    # STUDENT badge
    badge_y = ph_y + ph_h + 1.5*mm
    _rrect(c, ph_x, badge_y, ph_w, 4*mm, 1*mm, MID_BLUE)
    c.setFont("Helvetica-Bold", 6); c.setFillColor(WHITE)
    c.drawCentredString(ph_x+ph_w/2, badge_y+1.2*mm, "STUDENT")

    # Student name — auto shrink if too long
    nx = ph_x + ph_w + 3*mm
    ny = oy + H - 22*mm
    first = student.get("first_name","")
    last  = student.get("last_name","")
    full_name = f"{first} {last}"

    # Available width for name
    name_avail_w = W - (nx - ox) - 4*mm

    # Auto shrink font to fit
    font_size = 11
    c.setFont("Helvetica-Bold", font_size)
    while c.stringWidth(full_name, "Helvetica-Bold", font_size) > name_avail_w and font_size > 6:
        font_size -= 0.5

    c.setFont("Helvetica-Bold", font_size)
    c.setFillColor(DARK_BLUE)
    c.drawString(nx, ny, full_name)

    # ✅ GOLD underline under student name
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    c.line(nx, ny-1.5*mm, ox+W-3*mm, ny-1.5*mm)

    # Info grid
    avail_w = W - (nx - ox) - 4*mm
    mid = nx + avail_w/2

    c1l=nx; c1v=nx+17*mm
    c2l=mid+2*mm; c2v=mid+18*mm

    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(0.4)
    c.line(mid, ny-6*mm, mid, oy+9*mm)

    rows_l = [
        ("Student ID",    student.get("student_id","")),
        ("Date of Birth", student.get("date_of_birth","")),
        ("Program",       student.get("speciality", student.get("department",""))),
        ("Level",         student.get("level","")),
    ]
    rows_r = [
        ("Campus",      student.get("campus","")),
        ("Issue Date",  card.get("issued_date","")),
        ("Valid Until", card.get("expire_date","")),
    ]

    sy = ny - 7*mm
    rg = 4.5*mm

    for i,(lbl,val) in enumerate(rows_l):
        ry = sy - i*rg
        c.setFont("Helvetica",5.8); c.setFillColor(TEXT_DARK)
        c.drawString(c1l, ry, lbl)
        c.setFont("Helvetica-Bold",5.8); c.setFillColor(TEXT_BLUE)
        c.drawString(c1v, ry, str(val or "—"))

    for i,(lbl,val) in enumerate(rows_r):
        ry = sy - i*rg
        c.setFont("Helvetica",5.8); c.setFillColor(TEXT_DARK)
        c.drawString(c2l, ry, lbl)
        c.setFont("Helvetica-Bold",5.8); c.setFillColor(TEXT_BLUE)
        c.drawString(c2v, ry, str(val or "—"))


def _back(c, ox, oy, student, card):
    W, H = CARD_W, CARD_H

    _rrect(c, ox, oy, W, H, RADIUS, WHITE, stroke=HexColor("#CCCCCC"), sw=0.4)

    c.saveState()
    _clip_rrect(c, ox, oy, W, H, RADIUS)

    c.setFillColor(MID_BLUE)
    c.rect(ox, oy+H-19*mm, W, 19*mm, fill=1, stroke=0)

    c.setFillColor(DARK_BLUE)
    p = c.beginPath()
    p.moveTo(ox+W, oy+H)
    p.curveTo(ox+W-18*mm, oy+H, ox+W-11*mm, oy+H-10*mm, ox+W, oy+H-19*mm)
    p.lineTo(ox+W, oy+H); p.close()
    c.drawPath(p, fill=1, stroke=0)

    c.setFillColor(PURPLE)
    p2 = c.beginPath()
    p2.moveTo(ox+W, oy+H)
    p2.curveTo(ox+W-9*mm, oy+H, ox+W-5*mm, oy+H-7*mm, ox+W, oy+H-13*mm)
    p2.lineTo(ox+W, oy+H); p2.close()
    c.drawPath(p2, fill=1, stroke=0)

    c.setFillColor(MID_BLUE)
    c.rect(ox, oy, W, 10*mm, fill=1, stroke=0)

    c.setFillColor(DARK_BLUE)
    p3 = c.beginPath()
    p3.moveTo(ox, oy)
    p3.curveTo(ox+13*mm, oy, ox+19*mm, oy+10*mm, ox+33*mm, oy+10*mm)
    p3.lineTo(ox, oy+10*mm); p3.close()
    c.drawPath(p3, fill=1, stroke=0)

    c.restoreState()

    # Header logo + name
    lsz = 13*mm
    _logo(c, ox+3*mm, oy+H-lsz-2.5*mm, lsz, lsz)

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(WHITE)
    c.drawString(ox+18*mm, oy+H-8*mm,    "YAOUNDE INTERNATIONAL")
    c.drawString(ox+18*mm, oy+H-12.5*mm, "BUSINESS SCHOOL")

    # ✅ GOLD ACCENT LINE under school name on back
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.7)
    c.line(ox+18*mm, oy+H-13.5*mm, ox+W-3*mm, oy+H-13.5*mm)

    c.setFont("Helvetica-Oblique", 5)
    c.setFillColor(HexColor("#C8E0FF"))
    c.drawString(ox+18*mm, oy+H-16.5*mm, "Developing Innovative Professionals")

    # Body divider
    c.setStrokeColor(HexColor("#CCCCCC"))
    c.setLineWidth(0.5)
    div_x = ox + W * 0.48
    c.line(div_x, oy+10.5*mm, div_x, oy+H-20*mm)

    # Disclaimer
    tx = ox+3*mm; ty = oy+H-23*mm
    c.setFont("Helvetica", 5.8); c.setFillColor(TEXT_DARK)
    for i, line in enumerate([
        "This card is the property of Yaounde",
        "International Business School and is",
        "issued for identification purposes only.",
        "If found, please return to the",
        "administration office.",
    ]):
        c.drawString(tx, ty - i*4.3*mm, line)

    # QR code — shifted more to the right
    qr_size = 22*mm
    qr_x = div_x + 7*mm
    qr_y  = oy + H - 19*mm - qr_size - 2*mm

    qr_data = json.dumps({
        "student_id":    student.get("student_id"),
        "name":          f"{student.get('first_name','')} {student.get('last_name','')}",
        "email":         student.get("email",""),
        "department":    student.get("department",""),
        "speciality":    student.get("speciality",""),
        "level":         student.get("level",""),
        "campus":        student.get("campus",""),
        "nationality":   student.get("nationality",""),
        "date_of_birth": student.get("date_of_birth",""),
        "gender":        student.get("gender",""),
        "contact":       student.get("contact",""),
        "address":       student.get("address",""),
        "city":          student.get("city",""),
        "school":        student.get("school",""),
        "photo_url":     student.get("photo_url",""),
        "issued":        card.get("issued_date",""),
        "expires":       card.get("expire_date",""),
    }, ensure_ascii=False)

    qr_buf = _make_qr(qr_data)
    if qr_buf:
        _rrect(c, qr_x-1*mm, qr_y-1*mm, qr_size+2*mm, qr_size+2*mm,
               1*mm, WHITE, stroke=MID_BLUE, sw=1.2)
        c.drawImage(ImageReader(qr_buf), qr_x, qr_y, qr_size, qr_size,
                    preserveAspectRatio=True, mask="auto")

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(MID_BLUE)
    c.drawCentredString(qr_x+qr_size/2, qr_y-5*mm, student.get("student_id",""))

    # Footer icons
    contact = student.get("contact", student.get("emergency_phone",""))
    items = [
        (ICON_LOCATION, "Yaounde, Cameroon"),
        (ICON_PHONE,    contact or "+237 6XX XXX XXX"),
        (ICON_GLOBE,    "www.yibs.cm"),
        (ICON_EMAIL,    "info@yibs.cm"),
    ]
    slot = W / 4
    fy_icon = oy + 6.5*mm
    fy_text = oy + 2.5*mm
    icon_size = 4*mm

    for i, (icon_path, text) in enumerate(items):
        cx2 = ox + i*slot + slot/2
        if os.path.exists(icon_path):
            c.drawImage(ImageReader(icon_path),
                        cx2 - icon_size/2, fy_icon,
                        icon_size, icon_size,
                        preserveAspectRatio=True, mask="auto")
        else:
            c.setFont("Helvetica-Bold", 4.5)
            c.setFillColor(WHITE)
            c.drawCentredString(cx2, fy_icon+1.5*mm, ["LOC","TEL","WEB","MAIL"][i])
        c.setFont("Helvetica", 4.2)
        c.setFillColor(WHITE)
        c.drawCentredString(cx2, fy_text, text)


def generate_id_card(student_data: dict, output_path: str) -> str:
    try:
        issued = student_data.get("issued_date", datetime.now().strftime("%Y-%m-%d"))
        expire = student_data.get("expire_date",
                  (datetime.now()+timedelta(days=365)).strftime("%Y-%m-%d"))
        card = {"issued_date": issued, "expire_date": expire}

        page_w = CARD_W*2 + MARGIN*3 + GAP
        page_h = CARD_H + MARGIN*2

        cv = canvas.Canvas(output_path, pagesize=(page_w, page_h))
        cv.setTitle(f"IDentix — {student_data.get('first_name','')} "
                    f"{student_data.get('last_name','')}")

        _front(cv, MARGIN, MARGIN, student_data, card)
        _back(cv, MARGIN*2+CARD_W+GAP, MARGIN, student_data, card)

        cv.save()
        return output_path
    except Exception as e:
        print(f"[pdf_generator] Error: {e}")
        import traceback; traceback.print_exc()
        return None


