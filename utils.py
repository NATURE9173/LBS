import csv
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

BOOKINGS_FILE = os.path.join(os.path.dirname(__file__), "bookings.csv")

FIELDNAMES = ["id","name","email","lab","location","date","timeslot","purpose","created_at"]

def ensure_file():
    if not os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

def read_bookings():
    ensure_file()
    with open(BOOKINGS_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_booking(data: dict):
    ensure_file()
    rows = read_bookings()
    new_id = str(max([int(r["id"]) for r in rows], default=0) + 1)
    data["id"] = new_id
    data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(BOOKINGS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow({k: data.get(k, "") for k in FIELDNAMES})
    return new_id

def delete_booking_by_id(booking_id: str):
    ensure_file()
    rows = read_bookings()
    new_rows = [r for r in rows if r["id"] != booking_id]
    with open(BOOKINGS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(new_rows)
    return len(rows) - len(new_rows)

def filter_bookings(date=None, location=None):
    rows = read_bookings()
    if date:
        rows = [r for r in rows if r["date"] == date]
    if location:
        rows = [r for r in rows if r["location"] == location]
    return rows

def is_conflict(date, location, lab, timeslot):
    rows = read_bookings()
    # prevent double-booking the same lab at the same location and timeslot
    for r in rows:
        if r["date"] == date and r["location"] == location and r["lab"] == lab and r["timeslot"] == timeslot:
            return True
    return False

def export_bookings_to_pdf(rows, out_path):
    c = canvas.Canvas(out_path, pagesize=landscape(A4))
    width, height = landscape(A4)
    title = "Lab Bookings Export"
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height-40, title)
    c.setFont("Helvetica", 10)
    y = height - 70
    headers = ["ID","Name","Email","Lab","Location","Date","Timeslot","Purpose","Created"]
    col_x = [40, 100, 220, 360, 420, 500, 560, 640, 780]
    for i, h in enumerate(headers):
        c.drawString(col_x[i], y, h)
    y -= 18
    for r in rows:
        if y < 40:
            c.showPage()
            y = height - 40
        vals = [r["id"], r["name"], r["email"], r["lab"], r["location"], r["date"], r["timeslot"], r["purpose"], r["created_at"]]
        for i, v in enumerate(vals):
            c.drawString(col_x[i], y, str(v)[:45])
        y -= 16
    c.save()
