import io
import os
import base64
from functools import wraps

import matplotlib
matplotlib.use("Agg")  # no GUI needed, works inside Flask
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import mysql.connector
from flask import Flask, render_template, request, redirect, session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "TEMPLATE")

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = "change-this-secret"

# Users allowed to log in -> "name": "password"
# To add a user, just add a new line below.
USERS = {
    "Mahi": "Mahi123",
    "hemalatha": "hemalatha123",
    "harshika": "harshika123",
    "babji": "babji123",
    "shanmukh": "shanmukh123",
}


def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="aimlb2",
        database="hospital_db"
    )


def query_df(sql):
    """Run a SELECT and return a pandas DataFrame."""
    db = get_db()
    cur = db.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [c for c in cur.column_names]
    cur.close()
    db.close()
    return pd.DataFrame(rows, columns=cols)


def make_chart(labels, values, title, kind="bar"):
    """Create a chart and return it as a base64 PNG string."""
    if len(labels) == 0:
        return None
    fig, ax = plt.subplots(figsize=(6, 3.5))
    if kind == "line":
        ax.plot(labels, values, marker="o")
    else:
        ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel("Visits")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if username in USERS and USERS[username] == password:
            session["logged_in"] = True
            session["username"] = username
            return redirect("/")
        error = "Invalid username or password"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
@login_required
def dashboard():
    dept = query_df("""
        SELECT d.department_name AS department, COUNT(v.visit_id) AS total
        FROM departments d
        LEFT JOIN visits v ON d.department_id = v.department_id
        GROUP BY d.department_id, d.department_name
        ORDER BY total DESC
    """)

    monthly = query_df("""
        SELECT DATE_FORMAT(visit_date, '%Y-%m') AS month, COUNT(*) AS total
        FROM visits
        GROUP BY DATE_FORMAT(visit_date, '%Y-%m')
        ORDER BY month
    """)

    daily = query_df("""
        SELECT visit_date AS day, COUNT(*) AS total
        FROM visits
        GROUP BY visit_date
        ORDER BY visit_date DESC
        LIMIT 14
    """)

    age = query_df("""
        SELECT p.age_band, COUNT(*) AS total
        FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        GROUP BY p.age_band
        ORDER BY p.age_band
    """)

    total_visits = int(dept["total"].sum()) if not dept.empty else 0

    total_patients = int(query_df("SELECT COUNT(*) AS total FROM patients")["total"][0])

    recent = query_df("""
        SELECT v.visit_date, p.patient_name, p.address,
               d.department_name, v.visit_type
        FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        JOIN departments d ON v.department_id = d.department_id
        ORDER BY v.visit_date DESC, v.visit_id DESC
        LIMIT 8
    """)

    # NumPy summary statistics on monthly visit counts
    stats = None
    if not monthly.empty:
        arr = monthly["total"].to_numpy(dtype=float)
        stats = {
            "mean": round(float(np.mean(arr)), 2),
            "median": round(float(np.median(arr)), 2),
            "max": int(np.max(arr)),
            "min": int(np.min(arr)),
            "std": round(float(np.std(arr)), 2),
        }

    charts = {
        "dept": make_chart(dept["department"].tolist(), dept["total"].tolist(),
                           "Department-wise Visits"),
        "monthly": make_chart(monthly["month"].tolist(), monthly["total"].tolist(),
                              "Monthly Visit Trend", kind="line"),
        "age": make_chart(age["age_band"].tolist(), age["total"].tolist(),
                          "Visits by Age Band"),
    }

    return render_template(
        "dashboard.html",
        total=total_visits,
        total_patients=total_patients,
        recent=recent.to_dict("records"),
        departments=dept.to_dict("records"),
        monthly=monthly.to_dict("records"),
        daily=daily.to_dict("records"),
        age=age.to_dict("records"),
        stats=stats,
        charts=charts
    )


@app.route("/patients", methods=["GET", "POST"])
@login_required
def patients():
    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["patient_name"].strip()
        address = request.form.get("address", "").strip()
        age = request.form["age_band"]
        gender = request.form.get("gender", "")
        cur.execute(
            "INSERT INTO patients (patient_name, address, age_band, gender) "
            "VALUES (%s, %s, %s, %s)",
            (name, address or None, age, gender or None)
        )
        db.commit()
        cur.close()
        db.close()
        return redirect("/patients")

    cur.execute("SELECT * FROM patients ORDER BY patient_id DESC")
    records = cur.fetchall()
    cur.close()
    db.close()
    return render_template("patients.html", patients=records)


@app.route("/visits", methods=["GET", "POST"])
@login_required
def visits():
    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        cur.execute("""
            INSERT INTO visits (patient_id, department_id, visit_date, visit_type)
            VALUES (%s, %s, %s, %s)
        """, (
            request.form["patient_id"],
            request.form["department_id"],
            request.form["visit_date"],
            request.form["visit_type"]
        ))
        db.commit()
        cur.close()
        db.close()
        return redirect("/visits")

    cur.execute("SELECT patient_id, patient_name, age_band FROM patients ORDER BY patient_name")
    patients_list = cur.fetchall()

    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()

    cur.execute("""
        SELECT v.visit_id, v.visit_date, v.visit_type,
               p.patient_name, p.address, p.age_band, d.department_name
        FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        JOIN departments d ON v.department_id = d.department_id
        ORDER BY v.visit_date DESC, v.visit_id DESC
    """)
    visits_list = cur.fetchall()

    cur.close()
    db.close()
    return render_template(
        "visits.html",
        patients=patients_list,
        departments=departments,
        visits=visits_list
    )


if __name__ == "__main__":
    print("Looking for TEMPLATE in:", TEMPLATE_DIR)
    if os.path.isdir(TEMPLATE_DIR):
        print("Files found:", os.listdir(TEMPLATE_DIR))
    else:
        print("ERROR: 'TEMPLATE' folder does not exist next to app.py")
    app.run(debug=True)
