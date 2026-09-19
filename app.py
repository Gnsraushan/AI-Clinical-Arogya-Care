from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request
)

import os

from routes.auth import register_auth_routes
from routes.patient import register_patient_routes
from routes.doctor import register_doctor_routes
from routes.ai import register_ai_routes
from routes.appointment import register_appointment_routes

load_dotenv()
# =========================================================
# APP SETUP
# =========================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "caresync-sih-secret-key-change-later"
)


# =========================================================
# UPLOAD CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

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
# REGISTER ALL ROUTES
# =========================================================
#
# IMPORTANT:
# We are using route-registration functions instead of
# Flask Blueprints.
#
# This keeps existing endpoint names such as:
# url_for("patient_dashboard")
# url_for("dashboard")
# url_for("ai_conversation")
# etc. working.
# =========================================================

register_auth_routes(app)

register_patient_routes(app)

register_doctor_routes(app)

register_ai_routes(app)

register_appointment_routes(app)


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    return (
        "File too large. Maximum allowed size is 10 MB.",
        413
    )


@app.errorhandler(404)
def page_not_found(error):

    return (
        render_template(
            "404.html"
        ),
        404
    )


@app.errorhandler(500)
def internal_server_error(error):

    print(
        "INTERNAL SERVER ERROR:",
        error
    )

    return (
        render_template(
            "500.html"
        ),
        500
    )


# =========================================================
# ROOT SAFETY ROUTE
# =========================================================
#
# / is already registered inside auth.py.
# This section intentionally does not define another /
# route because that would create a duplicate endpoint.
# =========================================================


# =========================================================
# PRINT ROUTES
# =========================================================

print("\n==============================================")
print("        AROGYACARE FLASK APPLICATION")
print("==============================================")
print("Registered routes:")

for rule in app.url_map.iter_rules():

    print(
        f"{rule.methods} -> {rule}"
    )

print("==============================================\n")


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    print(
        "Starting ArogyaCare Flask server..."
    )

    app.run(
        debug=True
    )

