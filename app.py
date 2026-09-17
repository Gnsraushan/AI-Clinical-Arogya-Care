from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    send_file
)

import mysql.connector
from mysql.connector import Error

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from groq import Groq

import os
import uuid


# =========================================================
# APP SETUP
# =========================================================

app = Flask(__name__)

app.secret_key = "caresync-sih-secret-key-change-later"


# =========================================================
# GROQ
# =========================================================

client = Groq()


# =========================================================
# UPLOAD SETTINGS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

ALLOWED_EXTENSIONS = {
    "pdf",
    "jpg",
    "jpeg",
    "png"
}

MAX_FILE_SIZE = 10 * 1024 * 1024

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


# =========================================================
# DATABASE
# =========================================================

def get_db_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Raushan@2nd",
        database="arogyacare"
    )


# =========================================================
# SAFE CLOSE
# =========================================================

def safe_close(cursor=None, connection=None):

    try:
        if cursor:
            cursor.close()
    except Exception:
        pass

    try:
        if connection:
            connection.close()
    except Exception:
        pass


# =========================================================
# LOGIN HELPERS
# =========================================================

def patient_logged_in():

    return (
        session.get("logged_in") is True
        and session.get("role") == "patient"
        and session.get("user_id") is not None
    )


def doctor_logged_in():

    return (
        session.get("logged_in") is True
        and session.get("role") == "doctor"
        and session.get("user_id") is not None
    )


# =========================================================
# TEMPLATE ROUTES
# =========================================================

def get_template_routes():

    return set(
        app.view_functions.keys()
    )


# =========================================================
# FILE HELPER
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# RED FLAG DETECTION
# =========================================================

def check_red_flags(message):

    if not message:
        return False, None

    message_lower = message.lower()

    red_flag_patterns = {

        "Severe chest pain or pressure": [
            "severe chest pain",
            "very severe chest pain",
            "chest pressure",
            "pressure in chest",
            "bahut tez chest pain",
            "bahut tez seene me dard",
            "seene mein bahut tez dard",
            "seene me bahut tez dard",
            "सीने में बहुत तेज दर्द"
        ],

        "Severe difficulty breathing": [
            "difficulty breathing",
            "breathing difficulty",
            "severe breathlessness",
            "cannot breathe",
            "can't breathe",
            "cannot breath",
            "not able to breathe",
            "not able to breath",
            "saans lene me dikkat",
            "saans lene mein dikkat",
            "saans nahi aa rahi",
            "saans nahi le pa raha",
            "saans nahi le paa raha",
            "बहुत सांस फूल रही"
        ],

        "Loss of consciousness": [
            "unconscious",
            "loss of consciousness",
            "passed out",
            "fainted",
            "fainting",
            "behosh ho gaya",
            "behosh ho gayi",
            "behosh ho raha",
            "बेहोश"
        ],

        "Seizure": [
            "seizure",
            "fits",
            "convulsion",
            "daura pad raha",
            "daura pada",
            "दौरा"
        ],

        "Severe bleeding": [
            "severe bleeding",
            "heavy bleeding",
            "bleeding won't stop",
            "bleeding will not stop",
            "bahut zyada khoon",
            "khoon bahut zyada nikal raha",
            "khoon nahi ruk raha",
            "खून नहीं रुक रहा"
        ],

        "Sudden weakness or paralysis": [
            "sudden weakness",
            "suddenly weak",
            "paralysis",
            "one side is weak",
            "one side weakness",
            "ek side kamzor",
            "ek taraf kamzori",
            "achanak kamzori",
            "अचानक कमजोरी"
        ],

        "Sudden difficulty speaking": [
            "difficulty speaking",
            "unable to speak",
            "cannot speak",
            "can't speak",
            "speech problem",
            "bolne me dikkat",
            "bol nahi pa raha",
            "bol nahi paa raha",
            "बोलने में दिक्कत"
        ],

        "Severe allergic reaction": [
            "severe allergic reaction",
            "throat swelling",
            "face swelling with breathing",
            "tongue swelling with breathing",
            "gala sujan",
            "gale me sujan aur saans",
            "चेहरा सूज गया",
            "गला सूज गया"
        ]
    }

    for reason, patterns in red_flag_patterns.items():

        for pattern in patterns:

            if pattern in message_lower:
                return True, reason

    return False, None


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    role = request.args.get("role")

    if role in ["patient", "doctor"]:

        return redirect(
            url_for(
                "login_page",
                role=role
            )
        )

    return render_template(
        "index.html"
    )


# =========================================================
# INDEX ALIAS
# =========================================================

@app.route("/index.html")
def index():

    return redirect(
        url_for("home")
    )


# =========================================================
# LOGIN PAGE
# =========================================================

@app.route("/login")
def login_page():

    role = request.args.get(
        "role",
        "patient"
    )

    if role not in ["patient", "doctor"]:
        role = "patient"

    return render_template(
        "login.html",
        role=role
    )


# =========================================================
# REGISTER PAGE
# =========================================================

@app.route("/register")
def register():

    role = request.args.get(
        "role",
        "patient"
    )

    if role not in ["patient", "doctor"]:
        role = "patient"

    return render_template(
        "register.html",
        role=role
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["POST"])
def register_user():

    role = request.form.get(
        "role",
        ""
    ).strip().lower()

    if role not in ["patient", "doctor"]:

        if request.form.get("email"):
            role = "doctor"
        else:
            role = "patient"

    full_name = request.form.get(
        "fullName",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    ).strip()

    if not full_name or not password:

        return (
            "Name and password are required.",
            400
        )

    if len(password) < 6:

        return (
            "Password must be at least 6 characters.",
            400
        )

    password_hash = generate_password_hash(
        password
    )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        # =================================================
        # PATIENT REGISTRATION
        # =================================================

        if role == "patient":

            age = request.form.get(
                "age",
                ""
            ).strip()

            gender = request.form.get(
                "gender",
                ""
            ).strip()

            phone = request.form.get(
                "phone",
                ""
            ).strip()

            abha_id = request.form.get(
                "patientId",
                ""
            ).strip()

            if not age or not gender or not phone:

                return (
                    "Patient details are incomplete.",
                    400
                )

            cursor.execute(
                """
                SELECT id
                FROM patients
                WHERE phone = %s
                LIMIT 1
                """,
                (phone,)
            )

            if cursor.fetchone():

                return (
                    "A patient with this phone number already exists.",
                    409
                )

            if abha_id:

                cursor.execute(
                    """
                    SELECT id
                    FROM patients
                    WHERE abha_id = %s
                    LIMIT 1
                    """,
                    (abha_id,)
                )

                if cursor.fetchone():

                    return (
                        "This ABHA / Patient ID is already registered.",
                        409
                    )

            cursor.execute(
                """
                INSERT INTO patients
                (
                    full_name,
                    age,
                    gender,
                    phone,
                    abha_id,
                    password_hash
                )
                VALUES
                (%s, %s, %s, %s, %s, %s)
                """,
                (
                    full_name,
                    age,
                    gender,
                    phone,
                    abha_id if abha_id else None,
                    password_hash
                )
            )

            connection.commit()

            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        # =================================================
        # DOCTOR / STAFF REGISTRATION
        # =================================================

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        staff_role = request.form.get(
            "staffRole",
            ""
        ).strip()

        department = request.form.get(
            "department",
            ""
        ).strip()

        hospital = request.form.get(
            "hospital",
            ""
        ).strip()

        if (
            not email
            or not staff_role
            or not department
            or not hospital
        ):

            return (
                "Staff details are incomplete.",
                400
            )

        cursor.execute(
            """
            SELECT id
            FROM staff
            WHERE email = %s
            LIMIT 1
            """,
            (email,)
        )

        if cursor.fetchone():

            return (
                "An account with this email already exists.",
                409
            )

        cursor.execute(
            """
            INSERT INTO staff
            (
                full_name,
                email,
                staff_role,
                department,
                hospital,
                password_hash
            )
            VALUES
            (%s, %s, %s, %s, %s, %s)
            """,
            (
                full_name,
                email,
                staff_role,
                department,
                hospital,
                password_hash
            )
        )

        connection.commit()

        return redirect(
            url_for(
                "login_page",
                role="doctor"
            )
        )

    except Error as e:

        if connection:
            connection.rollback()

        print(
            "REGISTER ERROR:",
            e
        )

        return (
            "Registration failed. Check terminal for database error.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["POST"])
def login_user():

    role = request.form.get(
        "role",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    ).strip()

    if role not in ["patient", "doctor"]:
        role = "patient"

    if not password:

        return (
            "Password is required.",
            400
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # =================================================
        # PATIENT LOGIN
        # =================================================

        if role == "patient":

            identifier = request.form.get(
                "patientIdentifier",
                ""
            ).strip()

            if not identifier:

                identifier = request.form.get(
                    "email",
                    ""
                ).strip()

            if not identifier:

                return (
                    "Patient ID / ABHA / Phone is required.",
                    400
                )

            cursor.execute(
                """
                SELECT *
                FROM patients
                WHERE phone = %s
                   OR abha_id = %s
                LIMIT 1
                """,
                (
                    identifier,
                    identifier
                )
            )

            user = cursor.fetchone()

            if not user:

                return (
                    "Patient account not found.",
                    401
                )

            if not check_password_hash(
                user["password_hash"],
                password
            ):

                return (
                    "Incorrect password.",
                    401
                )

            session.clear()

            session["logged_in"] = True
            session["role"] = "patient"
            session["user_id"] = user["id"]
            session["full_name"] = user["full_name"]

            return redirect(
                url_for(
                    "patient_dashboard"
                )
            )

        # =================================================
        # DOCTOR LOGIN
        # =================================================

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        if not email:

            email = request.form.get(
                "patientIdentifier",
                ""
            ).strip().lower()

        if not email:

            return (
                "Email is required.",
                400
            )

        cursor.execute(
            """
            SELECT *
            FROM staff
            WHERE email = %s
            LIMIT 1
            """,
            (email,)
        )

        user = cursor.fetchone()

        if not user:

            return (
                "Staff account not found.",
                401
            )

        if not check_password_hash(
            user["password_hash"],
            password
        ):

            return (
                "Incorrect password.",
                401
            )

        session.clear()

        session["logged_in"] = True
        session["role"] = "doctor"
        session["user_id"] = user["id"]
        session["full_name"] = user["full_name"]
        session["email"] = user["email"]
        session["staff_role"] = user["staff_role"]
        session["department"] = user["department"]
        session["hospital"] = user["hospital"]

        return redirect(
            url_for("dashboard")
        )

    except Error as e:

        print(
            "LOGIN ERROR:",
            e
        )

        return (
            "Login failed. Check terminal.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# PATIENT DASHBOARD
# =========================================================

@app.route("/patient-dashboard")
def patient_dashboard():

    if not patient_logged_in():

        return redirect(
            url_for(
                "login_page",
                role="patient"
            )
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        patient_id = session["user_id"]

        cursor.execute(
            """
            SELECT *
            FROM patients
            WHERE id = %s
            LIMIT 1
            """,
            (patient_id,)
        )

        patient = cursor.fetchone()

        if not patient:

            session.clear()

            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        cursor.execute(
            """
            SELECT *
            FROM patient_histories
            WHERE patient_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (patient_id,)
        )

        patient_history = cursor.fetchone()

        cursor.execute(
            """
            SELECT
                message,
                sender,
                created_at
            FROM clinical_conversations
            WHERE patient_id = %s
            ORDER BY id DESC
            LIMIT 5
            """,
            (patient_id,)
        )

        recent_activity = cursor.fetchall()

        recent_activity.reverse()

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM documents
            WHERE patient_id = %s
            """,
            (patient_id,)
        )

        document_result = cursor.fetchone()

        document_count = (
            document_result["total"]
            if document_result
            else 0
        )

        return render_template(
            "patient_dashboard.html",
            patient=patient,
            patient_history=patient_history,
            recent_activity=recent_activity,
            document_count=document_count,
            user_name=patient["full_name"],
            patient_details_url=url_for("patient_details"),
            ai_conversation_url=url_for("ai_conversation"),
            patient_history_url=url_for("patient_history"),
            physician_review_url=url_for("physician_review"),
            documents_url=url_for("patient_documents"),
            settings_url=url_for("patient_settings"),
            routes=get_template_routes(),
            endpoints=get_template_routes()
        )

    except Error as e:

        print(
            "PATIENT DASHBOARD ERROR:",
            e
        )

        return (
            "Something went wrong while loading patient dashboard.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# PATIENT HOME
# =========================================================

@app.route("/patient-home")
def patient_home():

    return redirect(
        url_for(
            "patient_dashboard"
        )
    )


# =========================================================
# PATIENT DETAILS
# =========================================================

@app.route("/patient-details")
def patient_details():

    if not patient_logged_in():

        return redirect(
            url_for(
                "login_page",
                role="patient"
            )
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        patient_id = session["user_id"]

        cursor.execute(
            """
            SELECT *
            FROM patients
            WHERE id = %s
            LIMIT 1
            """,
            (patient_id,)
        )

        patient = cursor.fetchone()

        if not patient:

            session.clear()

            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        cursor.execute(
            """
            SELECT *
            FROM patient_histories
            WHERE patient_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (patient_id,)
        )

        history = cursor.fetchone()

        return render_template(
            "patient_details.html",
            patient=patient,
            history=history,
            user_name=patient["full_name"],
            created_at=patient.get("created_at"),
            account_status="Active",
            routes=get_template_routes(),
            endpoints=get_template_routes()
        )

    except Error as e:

        print(
            "PATIENT DETAILS ERROR:",
            e
        )

        return (
            "Something went wrong while loading patient details.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# AI CONVERSATION PAGE
# =========================================================

@app.route("/ai-conversation")
def ai_conversation():

    if not patient_logged_in():

        return redirect(
            url_for(
                "login_page",
                role="patient"
            )
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        patient_id = session["user_id"]

        cursor.execute(
            """
            SELECT *
            FROM patients
            WHERE id = %s
            LIMIT 1
            """,
            (patient_id,)
        )

        patient = cursor.fetchone()

        if not patient:

            session.clear()

            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        cursor.execute(
            """
            SELECT
                id,
                message,
                sender,
                created_at
            FROM clinical_conversations
            WHERE patient_id = %s
            ORDER BY id ASC
            """,
            (patient_id,)
        )

        conversations = cursor.fetchall()

        cursor.execute(
            """
            SELECT *
            FROM patient_histories
            WHERE patient_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (patient_id,)
        )

        history = cursor.fetchone()

        return render_template(
            "ai_conversation.html",
            patient=patient,
            conversations=conversations,
            patient_history=history,
            history=history,
            summary=history.get("summary") if history else None,
            user_name=patient["full_name"],
            allow_message_input=True,
            routes=get_template_routes(),
            endpoints=get_template_routes()
        )

    except Error as e:

        print(
            "AI CONVERSATION PAGE ERROR:",
            e
        )

        return (
            "Could not load AI conversation. Check terminal.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# AI MESSAGE PROCESSOR
# =========================================================

def process_ai_message(message):

    patient_id = session.get("user_id")

    if not patient_id:

        return {
            "success": False,
            "message": "Please login first."
        }

    red_flag, red_flag_reason = check_red_flags(
        message
    )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                message,
                sender
            FROM clinical_conversations
            WHERE patient_id = %s
            ORDER BY id ASC
            """,
            (patient_id,)
        )

        previous_messages = cursor.fetchall()

        cursor.execute(
            """
            INSERT INTO clinical_conversations
            (
                patient_id,
                message,
                sender
            )
            VALUES
            (%s, %s, %s)
            """,
            (
                patient_id,
                message,
                "patient"
            )
        )

        connection.commit()

        groq_messages = [

            {
                "role": "system",
                "content": """
You are an AI Clinical Intake Assistant for an Indian hospital.

Your job is ONLY to collect and organize information from the patient.

You are NOT a doctor.

NEVER diagnose diseases.
NEVER prescribe medicines.
NEVER recommend dosage or treatment.
NEVER invent patient information.

The doctor is the final decision-maker.

Rules:

- Ask ONE relevant question at a time.
- Do not repeat information already provided.
- Keep responses short.
- Use simple Hindi, Hinglish or English.
- Avoid unnecessary medical terminology.
- Collect main complaint, duration, symptoms, severity,
  relevant medical history, medicines and allergies when appropriate.
- Do not force questions that are not relevant.

If serious symptoms are reported, tell the patient that
the symptoms may require urgent attention and advise them
to immediately alert hospital staff or seek urgent medical attention.

Do not claim that a doctor reviewed anything unless that actually happened.
Do not claim that an emergency alert was sent unless the system actually sent one.

You are an intake assistant, NOT a diagnostic system.
"""
            }
        ]

        for item in previous_messages:

            if item["sender"] == "patient":

                groq_messages.append({
                    "role": "user",
                    "content": item["message"]
                })

            else:

                groq_messages.append({
                    "role": "assistant",
                    "content": item["message"]
                })

        groq_messages.append({
            "role": "user",
            "content": message
        })

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=groq_messages,
            include_reasoning=False
        )

        ai_message = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        cursor.execute(
            """
            INSERT INTO clinical_conversations
            (
                patient_id,
                message,
                sender
            )
            VALUES
            (%s, %s, %s)
            """,
            (
                patient_id,
                ai_message,
                "ai"
            )
        )

        connection.commit()

        return {
            "success": True,
            "reply": ai_message,
            "red_flag": red_flag,
            "red_flag_reason": red_flag_reason
        }

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "AI PROCESSING ERROR:",
            e
        )

        return {
            "success": False,
            "message": "AI response generate nahi ho paya. Check terminal."
        }

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# SEND INTAKE MESSAGE
# =========================================================

@app.route(
    "/send-intake-message",
    methods=["POST"]
)
def send_intake_message():

    if not patient_logged_in():

        return redirect(
            url_for(
                "login_page",
                role="patient"
            )
        )

    message = request.form.get(
        "message",
        ""
    ).strip()

    if not message:

        return redirect(
            url_for(
                "ai_conversation"
            )
        )

    result = process_ai_message(
        message
    )

    if result["success"]:

        return redirect(
            url_for(
                "ai_conversation"
            )
        )

    return (
        result.get(
            "message",
            "AI response generate nahi ho paya."
        ),
        500
    )


# =========================================================
# CHAT API
# =========================================================

@app.route(
    "/api/chat",
    methods=["POST"]
)
def api_chat():

    if not patient_logged_in():

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    message = data.get(
        "message",
        ""
    ).strip()

    if not message:

        return jsonify({
            "success": False,
            "message": "Message is empty."
        }), 400

    result = process_ai_message(
        message
    )

    if not result["success"]:

        return jsonify(
            result
        ), 500

    return jsonify(
        result
    )


# =========================================================
# CHAT HISTORY API
# =========================================================

@app.route(
    "/api/chat/history",
    methods=["GET"]
)
def chat_history():

    if not patient_logged_in():

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                id,
                message,
                sender,
                created_at
            FROM clinical_conversations
            WHERE patient_id = %s
            ORDER BY id ASC
            """,
            (session["user_id"],)
        )

        conversations = cursor.fetchall()

        return jsonify({
            "success": True,
            "conversations": conversations
        })

    except Error as e:

        print(
            "CHAT HISTORY ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Could not load chat history."
        }), 500

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# GENERATE CLINICAL HISTORY
# =========================================================

@app.route(
    "/api/history/generate",
    methods=["POST"]
)
def generate_history():

    if not patient_logged_in():

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    patient_id = session["user_id"]

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                message,
                sender
            FROM clinical_conversations
            WHERE patient_id = %s
            ORDER BY id ASC
            """,
            (patient_id,)
        )

        conversations = cursor.fetchall()

        if not conversations:

            return jsonify({
                "success": False,
                "message": "No conversation found."
            }), 400

        conversation_text = ""

        for item in conversations:

            sender = (
                "Patient"
                if item["sender"] == "patient"
                else "AI Assistant"
            )

            conversation_text += (
                sender
                + ": "
                + item["message"]
                + "\n"
            )

        response = client.chat.completions.create(

            model="openai/gpt-oss-120b",

            messages=[

                {
                    "role": "system",
                    "content": """
Create a structured clinical intake history from a patient-AI conversation.

Rules:

- Do NOT diagnose.
- Do NOT prescribe treatment.
- Do NOT invent information.
- Use ONLY information provided by the patient.
- If unavailable write "Not reported".
- Keep it short and clear.

Return EXACTLY:

MAIN PROBLEM:
...

DURATION:
...

SYMPTOMS:
...

MEDICAL HISTORY:
...

MEDICINES:
...

ALLERGIES:
...

SUMMARY:
...
"""
                },

                {
                    "role": "user",
                    "content":
                        "Create the structured clinical history:\n\n"
                        + conversation_text
                }
            ],

            include_reasoning=False
        )

        history_text = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        def get_section(
            text,
            start_marker,
            end_marker=None
        ):

            start = text.find(
                start_marker
            )

            if start == -1:
                return "Not reported"

            start += len(
                start_marker
            )

            if end_marker:

                end = text.find(
                    end_marker,
                    start
                )

                if end != -1:

                    value = text[
                        start:end
                    ].strip()

                    return (
                        value
                        if value
                        else "Not reported"
                    )

            value = text[
                start:
            ].strip()

            return (
                value
                if value
                else "Not reported"
            )

        main_problem = get_section(
            history_text,
            "MAIN PROBLEM:",
            "DURATION:"
        )

        duration = get_section(
            history_text,
            "DURATION:",
            "SYMPTOMS:"
        )

        symptoms = get_section(
            history_text,
            "SYMPTOMS:",
            "MEDICAL HISTORY:"
        )

        medical_history = get_section(
            history_text,
            "MEDICAL HISTORY:",
            "MEDICINES:"
        )

        medicines = get_section(
            history_text,
            "MEDICINES:",
            "ALLERGIES:"
        )

        allergies = get_section(
            history_text,
            "ALLERGIES:",
            "SUMMARY:"
        )

        summary = get_section(
            history_text,
            "SUMMARY:"
        )

        cursor.execute(
            """
            INSERT INTO patient_histories
            (
                patient_id,
                main_problem,
                duration,
                symptoms,
                medical_history,
                medicines,
                allergies,
                summary
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                patient_id,
                main_problem,
                duration,
                symptoms,
                medical_history,
                medicines,
                allergies,
                summary
            )
        )

        connection.commit()

        return jsonify({

            "success": True,

            "message":
                "Clinical history generated successfully.",

            "history": {

                "main_problem": main_problem,
                "duration": duration,
                "symptoms": symptoms,
                "medical_history": medical_history,
                "medicines": medicines,
                "allergies": allergies,
                "summary": summary
            }
        })

    except Exception as e:

        if connection:
            connection.rollback()

        print(
            "HISTORY GENERATION ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Clinical history generate nahi ho payi."
        }), 500

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# PATIENT HISTORY PAGE
# =========================================================

@app.route("/patient-history")
def patient_history():

    if not patient_logged_in():

        return redirect(
            url_for(
                "login_page",
                role="patient"
            )
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM patient_histories
            WHERE patient_id = %s
            ORDER BY id DESC
            """,
            (session["user_id"],)
        )

        histories = cursor.fetchall()

        return render_template(
            "patient_history.html",
            patient_histories=histories,
            user_name=session.get(
                "full_name",
                "Patient"
            ),
            routes=get_template_routes(),
            endpoints=get_template_routes()
        )

    except Error as e:

        print(
            "PATIENT HISTORY ERROR:",
            e
        )

        return (
            "Could not load patient history.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# PATIENT DOCUMENTS
# =========================================================

@app.route("/patient-documents")
def patient_documents():

    if not patient_logged_in():

        return redirect(
            url_for(
                "login_page",
                role="patient"
            )
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                id,
                document_name,
                document_type,
                file_path,
                file_size,
                uploaded_at
            FROM documents
            WHERE patient_id = %s
            ORDER BY id DESC
            """,
            (session["user_id"],)
        )

        documents = cursor.fetchall()

        for document in documents:

            document["url"] = url_for(
                "view_document",
                document_id=document["id"]
            )

            document["file_url"] = document["url"]

            document["download_url"] = url_for(
                "download_document",
                document_id=document["id"]
            )

            document["delete_url"] = url_for(
                "delete_document",
                document_id=document["id"]
            )

            document["name"] = document[
                "document_name"
            ]

            document["type"] = document[
                "document_type"
            ]

            document["created_at"] = document[
                "uploaded_at"
            ]

            document["size"] = document[
                "file_size"
            ]

        return render_template(
            "patient_documents.html",
            documents=documents,
            patient_documents=documents,
            user_name=session.get(
                "full_name",
                "Patient"
            ),
            routes=get_template_routes(),
            endpoints=get_template_routes()
        )

    except Error as e:

        print(
            "PATIENT DOCUMENTS ERROR:",
            e
        )

        return (
            "Could not load documents.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# UPLOAD DOCUMENT
# =========================================================

@app.route(
    "/upload-document",
    methods=["POST"]
)
def upload_document():

    if not patient_logged_in():

        return redirect(
            url_for(
                "login_page",
                role="patient"
            )
        )

    if "document" not in request.files:

        return (
            "No document selected.",
            400
        )

    file = request.files["document"]

    if not file or not file.filename:

        return (
            "No document selected.",
            400
        )

    if not allowed_file(
        file.filename
    ):

        return (
            "Invalid file type.",
            400
        )

    file.seek(
        0,
        os.SEEK_END
    )

    file_size = file.tell()

    file.seek(0)

    if file_size > MAX_FILE_SIZE:

        return (
            "File size cannot exceed 10 MB.",
            400
        )

    original_filename = secure_filename(
        file.filename
    )

    if not original_filename:

        return (
            "Invalid filename.",
            400
        )

    extension = original_filename.rsplit(
        ".",
        1
    )[1].lower()

    patient_id = session["user_id"]

    patient_folder = os.path.join(
        UPLOAD_FOLDER,
        str(patient_id)
    )

    os.makedirs(
        patient_folder,
        exist_ok=True
    )

    stored_filename = (
        str(uuid.uuid4())
        + "."
        + extension
    )

    file_path = os.path.join(
        patient_folder,
        stored_filename
    )

    try:

        file.save(
            file_path
        )

    except Exception as e:

        print(
            "FILE SAVE ERROR:",
            e
        )

        return (
            "Could not save document.",
            500
        )

    document_type = (
        "PDF"
        if extension == "pdf"
        else "IMAGE"
    )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO documents
            (
                patient_id,
                document_name,
                document_type,
                file_path,
                file_size
            )
            VALUES
            (%s, %s, %s, %s, %s)
            """,
            (
                patient_id,
                original_filename,
                document_type,
                file_path,
                file_size
            )
        )

        connection.commit()

        return redirect(
            url_for(
                "patient_documents"
            )
        )

    except Error as e:

        if connection:
            connection.rollback()

        if os.path.exists(file_path):

            try:
                os.remove(file_path)
            except Exception:
                pass

        print(
            "DOCUMENT DB ERROR:",
            e
        )

        return (
            "Document upload failed.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# VIEW DOCUMENT
# =========================================================

@app.route(
    "/view-document/<int:document_id>"
)
def view_document(document_id):

    if not patient_logged_in():

        return (
            "Unauthorized",
            401
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM documents
            WHERE id = %s
              AND patient_id = %s
            LIMIT 1
            """,
            (
                document_id,
                session["user_id"]
            )
        )

        document = cursor.fetchone()

        if not document:

            return (
                "Document not found.",
                404
            )

        file_path = document["file_path"]

        if not os.path.exists(file_path):

            return (
                "File not found on server.",
                404
            )

        return send_file(
            file_path,
            as_attachment=False,
            download_name=document["document_name"]
        )

    except Error as e:

        print(
            "VIEW DOCUMENT ERROR:",
            e
        )

        return (
            "Could not open document.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# DOWNLOAD DOCUMENT
# =========================================================

@app.route(
    "/download-document/<int:document_id>"
)
def download_document(document_id):

    if not patient_logged_in():

        return (
            "Unauthorized",
            401
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM documents
            WHERE id = %s
              AND patient_id = %s
            LIMIT 1
            """,
            (
                document_id,
                session["user_id"]
            )
        )

        document = cursor.fetchone()

        if not document:

            return (
                "Document not found.",
                404
            )

        file_path = document["file_path"]

        if not os.path.exists(file_path):

            return (
                "File not found on server.",
                404
            )

        return send_file(
            file_path,
            as_attachment=True,
            download_name=document["document_name"]
        )

    except Error as e:

        print(
            "DOWNLOAD DOCUMENT ERROR:",
            e
        )

        return (
            "Could not download document.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# DELETE DOCUMENT
# =========================================================

@app.route(
    "/delete-document/<int:document_id>",
    methods=["POST"]
)
def delete_document(document_id):

    if not patient_logged_in():

        return (
            "Unauthorized",
            401
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM documents
            WHERE id = %s
              AND patient_id = %s
            LIMIT 1
            """,
            (
                document_id,
                session["user_id"]
            )
        )

        document = cursor.fetchone()

        if not document:

            return (
                "Document not found.",
                404
            )

        file_path = document["file_path"]

        cursor.execute(
            """
            DELETE FROM documents
            WHERE id = %s
              AND patient_id = %s
            """,
            (
                document_id,
                session["user_id"]
            )
        )

        connection.commit()

        if os.path.exists(file_path):

            try:
                os.remove(file_path)
            except Exception:
                pass

        return redirect(
            url_for(
                "patient_documents"
            )
        )

    except Error as e:

        if connection:
            connection.rollback()

        print(
            "DELETE DOCUMENT ERROR:",
            e
        )

        return (
            "Could not delete document.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# PHYSICIAN REVIEW
# =========================================================

@app.route("/physician-review")
def physician_review():

    if not patient_logged_in():

        return redirect(
            url_for(
                "login_page",
                role="patient"
            )
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        patient_id = session["user_id"]

        cursor.execute(
            """
            SELECT *
            FROM patients
            WHERE id = %s
            LIMIT 1
            """,
            (patient_id,)
        )

        patient = cursor.fetchone()

        cursor.execute(
            """
            SELECT *
            FROM patient_histories
            WHERE patient_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (patient_id,)
        )

        history = cursor.fetchone()

        cursor.execute(
            """
            SELECT *
            FROM physician_reviews
            WHERE patient_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (patient_id,)
        )

        physician_review_data = cursor.fetchone()

        review_status = None

        if physician_review_data:

            review_status = physician_review_data.get(
                "status"
            )

        return render_template(
            "physician_review.html",
            patient=patient,
            history=history,
            patient_history=history,
            physician_review=physician_review_data,
            review_status=review_status,
            user_name=session.get(
                "full_name",
                "Patient"
            ),
            routes=get_template_routes(),
            endpoints=get_template_routes()
        )

    except Error as e:

        print(
            "PHYSICIAN REVIEW ERROR:",
            e
        )

        return (
            "Could not load physician review.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# PATIENT SETTINGS
# =========================================================

@app.route("/settings")
def patient_settings():

    if not patient_logged_in():

        return redirect(
            url_for(
                "login_page",
                role="patient"
            )
        )

    return render_template(
        "patient_settings.html",
        user_name=session.get(
            "full_name",
            "Patient"
        ),
        routes=get_template_routes(),
        endpoints=get_template_routes()
    )


# =========================================================
# SETTINGS ALIAS
# =========================================================

@app.route("/patient-settings")
def settings():

    return redirect(
        url_for(
            "patient_settings"
        )
    )


# =========================================================
# DOCTOR DASHBOARD PAGE
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not doctor_logged_in():

        return redirect(
            url_for(
                "login_page",
                role="doctor"
            )
        )

    doctor = {

        "full_name": session.get(
            "full_name",
            "Doctor"
        ),

        "email": session.get(
            "email",
            ""
        ),

        "staff_role": session.get(
            "staff_role",
            "Physician"
        ),

        "department": session.get(
            "department",
            ""
        ),

        "hospital": session.get(
            "hospital",
            ""
        )
    }

    return render_template(
        "doctor_dashboard.html",
        doctor=doctor,
        user_name=session.get(
            "full_name",
            "Doctor"
        ),
        routes=get_template_routes(),
        endpoints=get_template_routes()
    )


# =========================================================
# DOCTOR - SEARCH PATIENTS
# =========================================================

@app.route(
    "/api/doctor/patients/search",
    methods=["GET"]
)
def doctor_search_patients():

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "message": "Doctor login required."
        }), 401

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return jsonify({
            "success": True,
            "patients": []
        })

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        search_value = f"%{query}%"

        cursor.execute(
            """
            SELECT
                p.id,
                p.full_name,
                p.age,
                p.gender,
                p.phone,
                p.abha_id,

                (
                    SELECT ph.created_at
                    FROM patient_histories ph
                    WHERE ph.patient_id = p.id
                    ORDER BY ph.id DESC
                    LIMIT 1
                ) AS last_case_date

            FROM patients p

            WHERE
                p.full_name LIKE %s
                OR p.phone LIKE %s
                OR p.abha_id LIKE %s

            ORDER BY p.full_name ASC

            LIMIT 20
            """,
            (
                search_value,
                search_value,
                search_value
            )
        )

        patients = cursor.fetchall()

        result = []

        for patient in patients:

            red_flag = False

            cursor.execute(
                """
                SELECT message
                FROM clinical_conversations
                WHERE patient_id = %s
                ORDER BY id DESC
                LIMIT 30
                """,
                (patient["id"],)
            )

            messages = cursor.fetchall()

            for item in messages:

                message = item.get(
                    "message",
                    ""
                )

                detected, reason = check_red_flags(
                    message
                )

                if detected:

                    red_flag = True
                    break

            result.append({

                "id": patient["id"],

                "name": patient["full_name"],

                "age": patient["age"],

                "gender": patient["gender"],

                "mobile": patient["phone"],

                "abha_id": patient["abha_id"],

                "last_case_date": (
                    str(patient["last_case_date"])
                    if patient["last_case_date"]
                    else None
                ),

                "red_flag": red_flag
            })

        return jsonify({
            "success": True,
            "patients": result
        })

    except Exception as e:

        print(
            "DOCTOR PATIENT SEARCH ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# DOCTOR - PATIENT CASE
# =========================================================

@app.route(
    "/api/doctor/patient/<int:patient_id>",
    methods=["GET"]
)
def doctor_patient_case(patient_id):

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "message": "Doctor login required."
        }), 401

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # -------------------------------------------------
        # PATIENT
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                full_name,
                age,
                gender,
                phone,
                abha_id
            FROM patients
            WHERE id = %s
            LIMIT 1
            """,
            (patient_id,)
        )

        patient = cursor.fetchone()

        if not patient:

            return jsonify({
                "success": False,
                "message": "Patient not found."
            }), 404

        # -------------------------------------------------
        # HISTORY
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                patient_id,
                main_problem,
                duration,
                symptoms,
                medical_history,
                medicines,
                allergies,
                summary,
                created_at
            FROM patient_histories
            WHERE patient_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (patient_id,)
        )

        history = cursor.fetchone()

        # -------------------------------------------------
        # CONVERSATION
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                message,
                sender,
                created_at
            FROM clinical_conversations
            WHERE patient_id = %s
            ORDER BY id ASC
            """,
            (patient_id,)
        )

        conversation = cursor.fetchall()

        # -------------------------------------------------
        # RED FLAGS
        # -------------------------------------------------

        red_flag = False
        red_flag_reason = None

        for message in conversation:

            detected, reason = check_red_flags(
                message.get(
                    "message",
                    ""
                )
            )

            if detected:

                red_flag = True
                red_flag_reason = reason
                break

        if history:

            history["red_flag"] = red_flag

            history["red_flag_reason"] = (
                red_flag_reason
            )

            if history.get("created_at"):

                history["created_at"] = str(
                    history["created_at"]
                )

        else:

            history = {
                "main_problem": "",
                "duration": "",
                "symptoms": "",
                "medical_history": "",
                "medicines": "",
                "allergies": "",
                "summary": "",
                "red_flag": red_flag,
                "red_flag_reason": red_flag_reason
            }

        # -------------------------------------------------
        # CONVERSATION DATES
        # -------------------------------------------------

        for message in conversation:

            if message.get("created_at"):

                message["created_at"] = str(
                    message["created_at"]
                )

        # -------------------------------------------------
        # DOCUMENTS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                document_name,
                document_type,
                file_path,
                file_size,
                uploaded_at
            FROM documents
            WHERE patient_id = %s
            ORDER BY id DESC
            """,
            (patient_id,)
        )

        documents = cursor.fetchall()

        for document in documents:

            if document.get("uploaded_at"):

                document["uploaded_at"] = str(
                    document["uploaded_at"]
                )

            document["view_url"] = url_for(
                "doctor_view_document",
                document_id=document["id"]
            )

            document["download_url"] = url_for(
                "doctor_download_document",
                document_id=document["id"]
            )

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "patient": {

                "id": patient["id"],

                "name": patient["full_name"],

                "age": patient["age"],

                "gender": patient["gender"],

                "mobile": patient["phone"],

                "abha_id": patient["abha_id"]
            },

            "history": history,

            "conversation": conversation,

            "documents": documents,

            "red_flag": red_flag,

            "red_flag_reason": red_flag_reason
        })

    except Exception as e:

        print(
            "DOCTOR PATIENT CASE ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# DOCTOR - VIEW DOCUMENT
# =========================================================

@app.route(
    "/api/doctor/document/<int:document_id>/view"
)
def doctor_view_document(document_id):

    if not doctor_logged_in():

        return (
            "Unauthorized",
            401
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                file_path,
                document_name
            FROM documents
            WHERE id = %s
            LIMIT 1
            """,
            (document_id,)
        )

        document = cursor.fetchone()

        if not document:

            return (
                "Document not found.",
                404
            )

        file_path = document["file_path"]

        if not os.path.exists(file_path):

            return (
                "File not found on server.",
                404
            )

        return send_file(
            file_path,
            as_attachment=False,
            download_name=document["document_name"]
        )

    except Error as e:

        print(
            "DOCTOR VIEW DOCUMENT ERROR:",
            e
        )

        return (
            "Could not open document.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# DOCTOR - DOWNLOAD DOCUMENT
# =========================================================

@app.route(
    "/api/doctor/document/<int:document_id>/download"
)
def doctor_download_document(document_id):

    if not doctor_logged_in():

        return (
            "Unauthorized",
            401
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                file_path,
                document_name
            FROM documents
            WHERE id = %s
            LIMIT 1
            """,
            (document_id,)
        )

        document = cursor.fetchone()

        if not document:

            return (
                "Document not found.",
                404
            )

        file_path = document["file_path"]

        if not os.path.exists(file_path):

            return (
                "File not found on server.",
                404
            )

        return send_file(
            file_path,
            as_attachment=True,
            download_name=document["document_name"]
        )

    except Error as e:

        print(
            "DOCTOR DOWNLOAD DOCUMENT ERROR:",
            e
        )

        return (
            "Could not download document.",
            500
        )

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# DOCTOR - VERIFY CASE
# =========================================================

@app.route(
    "/api/doctor/patient/<int:patient_id>/verify",
    methods=["POST"]
)
def doctor_verify_case(patient_id):

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "message": "Doctor login required."
        }), 401

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT id
            FROM patients
            WHERE id = %s
            LIMIT 1
            """,
            (patient_id,)
        )

        patient = cursor.fetchone()

        if not patient:

            return jsonify({
                "success": False,
                "message": "Patient not found."
            }), 404

        return jsonify({
            "success": True,
            "message": "Patient case verified successfully."
        })

    except Error as e:

        print(
            "DOCTOR VERIFY ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Could not verify case."
        }), 500

    finally:

        safe_close(
            cursor,
            connection
        )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# FILE TOO LARGE
# =========================================================

@app.errorhandler(413)
def request_entity_too_large(error):

    return (
        "File is too large. Maximum allowed size is 10 MB.",
        413
    )


# =========================================================
# 404
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return (
        "Page not found.",
        404
    )


# =========================================================
# 500
# =========================================================

@app.errorhandler(500)
def internal_server_error(error):

    print(
        "INTERNAL SERVER ERROR:",
        error
    )

    return (
        "Internal server error. Check Flask terminal.",
        500
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    print(
        "=============================================="
    )

    print(
        "Starting ArogyaCare Flask server..."
    )

    print(
        "Database: arogyacare"
    )

    print(
        "Documents folder:",
        UPLOAD_FOLDER
    )

    print(
        "=============================================="
    )

    app.run(
        debug=True
    )