from flask import Flask, render_template, request, send_file
import re, sqlite3, json, os
from datetime import datetime, timedelta
from fpdf import FPDF

from ollama_llm import ollama_generate_plan
from gemini_llm import gemini_generate_plan

app = Flask(__name__)

# ------------------ DATABASE ------------------
DB_FILE = "progress.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            goal TEXT,
            hours INTEGER,
            subjects TEXT,
            timetable TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ------------------ HELPERS ------------------
def extract_days(goal):
    match = re.search(r"(\d+)\s*days", goal.lower())
    return int(match.group(1)) if match else 7

def safe_text(text):
    """Clean Unicode for PDF"""
    if not text:
        return ""
    return str(text).replace("–", "-").replace("—", "-").replace("’", "'").replace("“", '"').replace("”", '"')

def generate_day_schedule(subjects, hours):
    start = datetime.strptime("06:00 AM", "%I:%M %p")
    remaining = hours * 60
    index = 0
    sessions = []

    while remaining > 0:
        study_minutes = min(110, remaining)
        end = start + timedelta(minutes=study_minutes)
        sessions.append({
            "subject": subjects[index % len(subjects)],
            "time": f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"
        })
        remaining -= study_minutes
        start = end

        if remaining > 0:
            # Add 10-min break
            break_end = start + timedelta(minutes=10)
            sessions.append({
                "subject": "Break",
                "time": f"{start.strftime('%I:%M %p')} - {break_end.strftime('%I:%M %p')}"
            })
            start = break_end
        index += 1
    return sessions

def generate_timetable(subjects, days, hours):
    timetable = []
    for d in range(1, days + 1):
        timetable.append({
            "day": f"Day {d}",
            "sessions": generate_day_schedule(subjects, hours)
        })
    return timetable

def clean_ai_text(text):
    lines = []
    for line in text.split("\n"):
        line = line.replace("**", "").strip()
        if line:
            lines.append(line)
    return lines

# ------------------ ROUTES ------------------

@app.route("/", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def index():
    timetable = ai_plan = user = None

    if request.method == "POST":
        name = request.form["name"]
        subjects = [s.strip() for s in request.form["subjects"].split(",")]
        hours = int(request.form["hours"])
        goal = request.form["goal"]
        mode = request.form["mode"]

        days = extract_days(goal)
        timetable = generate_timetable(subjects, days, hours)

        user = {
            "name": name,
            "goal": goal,
            "hours": hours,
            "subjects": ", ".join(subjects)
        }

        prompt = (
            f"Create a {days}-day study plan.\n"
            f"Subjects: {', '.join(subjects)}\n"
            f"Daily study hours: {hours}\n"
            f"Goal: {goal}\n"
            "Use weekday names only. Explain study, revision, and mock tests."
        )

        # ✅ PASTE AI LOGIC HERE
        ai_plan = []
        try:
            if mode == "online":
                ai_text = gemini_generate_plan(prompt)
                ai_plan = clean_ai_text(ai_text)
            else:
                ai_text = ollama_generate_plan(prompt)
                ai_plan = clean_ai_text(ai_text)
        except Exception:
            ai_text = ollama_generate_plan(prompt)
            ai_plan = clean_ai_text(ai_text)

    return render_template(
        "index.html",
        timetable=timetable,
        ai_plan=ai_plan,
        user=user
    )

# ------------------ SAVE PROGRESS ------------------
@app.route("/save", methods=["POST"])
def save_progress():
    data = request.get_json()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO progress (name, goal, hours, subjects, timetable)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["goal"],
        data["hours"],
        data["subjects"],
        json.dumps(data["timetable"])
    ))
    conn.commit()
    conn.close()

    db_path = os.path.abspath(DB_FILE)
    return f"Progress saved successfully at: {db_path}"

# ------------------ EXPORT PDF ------------------
@app.route("/export")
def export_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT name, goal, hours, subjects, timetable FROM progress ORDER BY id DESC LIMIT 1")
        row = c.fetchone()

    if not row:
        return "No data to export."

    name, goal, hours, subjects, timetable_json = row
    timetable = json.loads(timetable_json)

    pdf.cell(0, 10, "Time Management Agent - Study Plan", ln=True)
    pdf.ln(5)
    pdf.multi_cell(0, 8, safe_text(f"Name: {name}"))
    pdf.multi_cell(0, 8, safe_text(f"Goal: {goal}"))
    pdf.multi_cell(0, 8, safe_text(f"Daily Hours: {hours}"))
    pdf.multi_cell(0, 8, safe_text(f"Subjects: {subjects}"))
    pdf.ln(5)

    for day in timetable:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, safe_text(day["day"]), ln=True)
        pdf.set_font("Arial", size=11)
        for s in day["sessions"]:
            line = f"{s['subject']} : {s['time']}"
            pdf.cell(0, 7, safe_text(line), ln=True)
        pdf.ln(3)

    file_path = "Study_Timetable.pdf"
    pdf.output(file_path)
    return send_file(file_path, as_attachment=True)

# ------------------ REPLAN ------------------
@app.route("/replan", methods=["POST"])
def replan():
    name = request.form["name"]
    subjects = [s.strip() for s in request.form["subjects"].split(",")]
    hours = int(request.form["hours"])
    goal = request.form["goal"]
    mode = request.form["mode"]

    days = extract_days(goal)
    timetable = generate_timetable(subjects, days, hours)

    user = {
        "name": name,
        "goal": goal,
        "hours": hours,
        "subjects": ", ".join(subjects)
    }

    prompt = (
        f"Replan study for {days} days.\n"
        f"Subjects: {', '.join(subjects)}\n"
        f"Daily hours: {hours}\n"
        f"Goal: {goal}\n"
        "Use weekday names only. No stars."
    )

    ai_text = gemini_generate_plan(prompt) if mode == "online" else ollama_generate_plan(prompt)
    ai_plan = clean_ai_text(ai_text)

    return render_template("index.html", timetable=timetable, ai_plan=ai_plan, user=user)

# ------------------ RUN ------------------
if __name__ == "__main__":
    app.run(debug=True)
