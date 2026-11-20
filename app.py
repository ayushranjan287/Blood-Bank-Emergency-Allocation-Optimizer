from flask import Flask, render_template, request, redirect, flash
import sqlite3
from datetime import date

from algorithms.priority_queue import MaxHeap
from algorithms.greedy_allocation import allocate_blood

app = Flask(__name__)
app.secret_key = "blood_bank_project"


DATABASE = "blood_bank.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Initialize database
def initialize_database():

    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS blood_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id TEXT UNIQUE,
            blood_group TEXT,
            expiry_date TEXT,
            status TEXT DEFAULT 'Available'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE,
            blood_group TEXT,
            priority TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS allocation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT,
            unit_id TEXT,
            allocation_date TEXT
        )
    """)

    conn.commit()
    conn.close()


# Dashboard
@app.route("/")
def home():

    conn = get_db_connection()

    total_units = conn.execute(
        "SELECT COUNT(*) FROM blood_inventory WHERE status='Available' AND expiry_date >= ?",
        (date.today().isoformat(),)
    ).fetchone()[0]

    pending_requests = conn.execute(
        "SELECT COUNT(*) FROM patients WHERE status='Pending'"
    ).fetchone()[0]

    patients_served = conn.execute(
        "SELECT COUNT(*) FROM allocation_history"
    ).fetchone()[0]

    critical_requests = conn.execute(
        "SELECT COUNT(*) FROM patients WHERE priority='Critical' AND status='Pending'"
    ).fetchone()[0]

    inventory = conn.execute(
        "SELECT * FROM blood_inventory ORDER BY expiry_date"
    ).fetchall()

    patients = conn.execute(
        "SELECT * FROM patients ORDER BY id DESC"
    ).fetchall()

    history = conn.execute(
        "SELECT * FROM allocation_history ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
    "index.html",
    total_units=total_units,
    pending_requests=pending_requests,
    patients_served=patients_served,
    critical_requests=critical_requests,
    inventory=inventory,
    patients=patients,
    history=history,
    today=date.today().isoformat()
)


# Add blood stock
@app.route("/add_stock", methods=["POST"])
def add_stock():

    unit_id = request.form["unit_id"].strip().upper()
    blood_group = request.form["blood_group"]
    expiry_date = request.form["expiry_date"]

    if not unit_id or not expiry_date:
        flash("Please complete all blood stock fields.")
        return redirect("/")

    if blood_group not in [
        "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"
    ]:
        flash("Invalid blood group.")
        return redirect("/")

    try:
        if date.fromisoformat(expiry_date) < date.today():
            flash("Expiry date cannot be in the past.")
            return redirect("/")
    except ValueError:
        flash("Invalid expiry date.")
        return redirect("/")

    conn = get_db_connection()

    try:
        conn.execute("""
            INSERT INTO blood_inventory
            (unit_id, blood_group, expiry_date)
            VALUES (?, ?, ?)
        """, (unit_id, blood_group, expiry_date))

        conn.commit()
        flash("Blood stock added successfully!")

    except sqlite3.IntegrityError:
        flash("This Unit ID already exists.")

    finally:
        conn.close()

    return redirect("/")


# Register patient
@app.route("/add_patient", methods=["POST"])
def add_patient():

    patient_id = request.form["patient_id"].strip().upper()
    blood_group = request.form["blood_group"]
    priority = request.form["priority"]

    if not patient_id:
        flash("Please enter Patient ID.")
        return redirect("/")

    if blood_group not in [
        "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"
    ]:
        flash("Invalid blood group.")
        return redirect("/")

    if priority not in ["Critical", "High", "Normal"]:
        flash("Invalid priority.")
        return redirect("/")

    conn = get_db_connection()

    try:
        conn.execute("""
            INSERT INTO patients
            (patient_id, blood_group, priority)
            VALUES (?, ?, ?)
        """, (patient_id, blood_group, priority))

        conn.commit()
        flash("Patient registered successfully!")

    except sqlite3.IntegrityError:
        flash("This Patient ID already exists.")

    finally:
        conn.close()

    return redirect("/")

@app.route("/allocate", methods=["POST"])
def allocate():

    conn = get_db_connection()

    # Fetch pending patients
    patient_rows = conn.execute(
        "SELECT * FROM patients WHERE status='Pending'"
    ).fetchall()

    # Fetch available blood units
    unit_rows = conn.execute(
        "SELECT * FROM blood_inventory WHERE status='Available'"
    ).fetchall()

    patients = [dict(patient) for patient in patient_rows]
    units = [dict(unit) for unit in unit_rows]

    # Step 1: Create Max Heap
    patient_heap = MaxHeap()

    for patient in patients:
        patient_heap.insert(patient)

    allocated_count = 0
    unsuccessful_count = 0

    # Step 2: Process patients by priority
    while patient_heap.heap:

        patient = patient_heap.extract_max()

        # Step 3: Apply Greedy Allocation
        selected_unit = allocate_blood(patient, units)

        if selected_unit is None:
            unsuccessful_count += 1
            continue

        # Update inventory
        conn.execute(
            "UPDATE blood_inventory SET status='Allocated' WHERE id=?",
            (selected_unit["id"],)
        )

        # Update patient
        conn.execute(
            "UPDATE patients SET status='Allocated' WHERE id=?",
            (patient["id"],)
        )

        # Save allocation history
        conn.execute("""
            INSERT INTO allocation_history
            (patient_id, unit_id, allocation_date)
            VALUES (?, ?, ?)
        """, (
            patient["patient_id"],
            selected_unit["unit_id"],
            date.today().isoformat()
        ))

        # Prevent reuse of the same unit
        selected_unit["status"] = "Allocated"

        allocated_count += 1

    conn.commit()
    conn.close()

    flash(
        f"Allocation completed! {allocated_count} patient(s) allocated. "
        f"{unsuccessful_count} request(s) could not be fulfilled."
    )

    return redirect("/")
initialize_database()

if __name__ == "__main__":
    app.run(debug=True)
