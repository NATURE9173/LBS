from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from datetime import datetime
import os
from utils import read_bookings, write_booking, delete_booking_by_id, filter_bookings, is_conflict, export_bookings_to_pdf

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "change_me"

LABS = ["CS018", "CC898", "AI201", "NET404"]
LOCATIONS = ["Pune", "Bangalore"]
TIMESLOTS = ["09:00-11:00", "11:30-13:30", "14:00-16:00", "16:30-18:30"]

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

@app.context_processor
def inject_today():
    return {"today": datetime.now().strftime("%Y-%m-%d")}

@app.route("/")
def index():
    return render_template("index.html", labs=LABS, locations=LOCATIONS, timeslots=TIMESLOTS)

@app.route("/availability")
def availability():
    date = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
    location = request.args.get("location") or LOCATIONS[0]
    bookings = filter_bookings(date=date, location=location)
    taken = {(b["lab"], b["timeslot"]) for b in bookings}
    return render_template("availability.html",
                           labs=LABS, locations=LOCATIONS, timeslots=TIMESLOTS,
                           date=date, location=location, taken=taken, bookings=bookings)

@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        data = {
            "name": request.form["name"],
            "email": request.form["email"],
            "lab": request.form["lab"],
            "location": request.form["location"],
            "date": request.form["date"],
            "timeslot": request.form["timeslot"],
            "purpose": request.form.get("purpose","")
        }
        if is_conflict(data["date"], data["location"], data["lab"], data["timeslot"]):
            flash("That lab and timeslot are already booked at this location.", "danger")
            return redirect(url_for("availability", date=data["date"], location=data["location"]))
        write_booking(data)
        flash("Booking confirmed!", "success")
        return redirect(url_for("availability", date=data["date"], location=data["location"]))
    # GET prefill
    prefill = {
        "lab": request.args.get("lab", LABS[0]),
        "location": request.args.get("location", LOCATIONS[0]),
        "date": request.args.get("date", datetime.now().strftime("%Y-%m-%d")),
        "timeslot": request.args.get("timeslot", TIMESLOTS[0])
    }
    return render_template("book.html", labs=LABS, locations=LOCATIONS, timeslots=TIMESLOTS, **prefill)

# ----- Admin -----
@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        u = request.form.get("username","")
        p = request.form.get("password","")
        if u == ADMIN_USER and p == ADMIN_PASS:
            session["admin"] = True
            flash("Logged in", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    flash("Logged out", "info")
    return redirect(url_for("admin_login"))

def admin_required():
    if not session.get("admin"):
        return False
    return True

@app.route("/admin")
@app.route("/admin/dashboard")
def admin_dashboard():
    if not admin_required():
        return redirect(url_for("admin_login"))
    rows = read_bookings()
    return render_template("admin_dashboard.html", rows=rows)

@app.route("/admin/delete/<booking_id>", methods=["POST"])
def admin_delete(booking_id):
    if not admin_required():
        return redirect(url_for("admin_login"))
    deleted = delete_booking_by_id(booking_id)
    if deleted:
        flash("Booking deleted", "info")
    else:
        flash("Booking not found", "warning")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/export/csv")
def export_csv():
    if not admin_required():
        return redirect(url_for("admin_login"))
    rows = read_bookings()
    # build CSV in memory
    import csv, io
    si = io.StringIO()
    cw = csv.DictWriter(si, fieldnames=["id","name","email","lab","location","date","timeslot","purpose","created_at"])
    cw.writeheader()
    cw.writerows(rows)
    mem = io.BytesIO(si.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name="bookings.csv", mimetype="text/csv")

@app.route("/admin/export/pdf")
def export_pdf():
    if not admin_required():
        return redirect(url_for("admin_login"))
    rows = read_bookings()
    out_path = os.path.join(os.path.dirname(__file__), "bookings.pdf")
    export_bookings_to_pdf(rows, out_path)
    return send_file(out_path, as_attachment=True, download_name="bookings.pdf")

if __name__ == "__main__":
    app.run(debug=True)
