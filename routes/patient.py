from flask import (
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    send_from_directory
)

from services.database import (
    get_db_connection,
    safe_close
)

from werkzeug.utils import secure_filename

import os
import uuid


# =========================================================
# PATIENT SESSION HELPERS
# =========================================================

def get_logged_in_patient_id():
    """
    Current patient ID.

    New login system uses:
        session["user_id"]

    Older parts of the application may use:
        session["patient_id"]

    Both are supported.
    """

    patient_id = session.get("user_id")

    if patient_id is None:
        patient_id = session.get("patient_id")

    return patient_id


def patient_logged_in():
    return (
        session.get("logged_in") is True
        and session.get("role") == "patient"
        and get_logged_in_patient_id() is not None
    )


# =========================================================
# DOCUMENT SETTINGS
# =========================================================

ALLOWED_DOCUMENT_EXTENSIONS = {
    "pdf",
    "jpg",
    "jpeg",
    "png"
}


def allowed_document(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_DOCUMENT_EXTENSIONS
    )


# =========================================================
# PATIENT ROUTES
# =========================================================

def register_patient_routes(app):

    # =====================================================
    # PATIENT DASHBOARD
    # =====================================================

    @app.route("/patient/dashboard")
    def patient_dashboard():

        if not patient_logged_in():
            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        patient_id = get_logged_in_patient_id()

        return render_template(
            "patient_dashboard.html",

            patient_name=session.get(
                "full_name",
                "Patient"
            ),

            patient_email=session.get(
                "email",
                ""
            ),

            patient_id=patient_id,

            abha_id=session.get(
                "abha_id",
                ""
            )
        )


    # =====================================================
    # PATIENT HOME — COMPATIBILITY
    # =====================================================

    @app.route("/patient/home")
    def patient_home():

        if not patient_logged_in():
            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        return redirect(
            url_for("patient_dashboard")
        )


    # =====================================================
    # PATIENT MY DETAILS
    # =====================================================

    @app.route("/patient/details")
    def patient_details():

        if not patient_logged_in():
            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        patient_id = get_logged_in_patient_id()

        connection = None
        cursor = None

        patient = None
        history = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            # =================================================
            # LOAD LOGGED-IN PATIENT
            # =================================================

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
                (
                    patient_id,
                )
            )

            patient = cursor.fetchone()

            # =================================================
            # LOAD LATEST HEALTH HISTORY
            # =================================================

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
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (
                    patient_id,
                )
            )

            history = cursor.fetchone()

            # =================================================
            # PATIENT NOT FOUND
            # =================================================

            if not patient:

                return render_template(
                    "patient_details.html",

                    user_name=session.get(
                        "full_name",
                        "Patient"
                    ),

                    patient=None,

                    history=history,

                    created_at=(
                        history.get("created_at")
                        if history
                        else None
                    ),

                    account_status="Active"
                )

            # =================================================
            # RENDER DATABASE DATA
            # =================================================

            return render_template(
                "patient_details.html",

                user_name=(
                    patient.get("full_name")
                    or session.get(
                        "full_name",
                        "Patient"
                    )
                ),

                patient=patient,

                history=history,

                created_at=(
                    history.get("created_at")
                    if history
                    else None
                ),

                account_status="Active"
            )

        except Exception as error:

            print(
                "PATIENT DETAILS PAGE ERROR:",
                error
            )

            return render_template(
                "patient_details.html",

                user_name=session.get(
                    "full_name",
                    "Patient"
                ),

                patient=None,

                history=None,

                created_at=None,

                account_status="Active"
            )

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # PATIENT SETTINGS — COMPATIBILITY
    # =====================================================

    @app.route("/patient/settings")
    def patient_settings():

        if not patient_logged_in():
            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        return redirect(
            url_for("patient_details")
        )


    # =====================================================
    # SETTINGS — OLD TEMPLATE COMPATIBILITY
    # =====================================================

    @app.route("/settings")
    def settings():

        if not patient_logged_in():
            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        return redirect(
            url_for("patient_settings")
        )


    # =====================================================
    # PATIENT HISTORY PAGE
    # =====================================================

    @app.route("/patient/history")
    def patient_history():

        if not patient_logged_in():
            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        patient_id = get_logged_in_patient_id()

        connection = None
        cursor = None

        histories = []

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

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
                ORDER BY created_at DESC, id DESC
                """,
                (
                    patient_id,
                )
            )

            histories = cursor.fetchall()

            print(
                "PATIENT HISTORY PAGE:",
                len(histories),
                "records loaded for patient",
                patient_id
            )

            return render_template(
                "patient_history.html",

                patient_histories=histories,

                histories=histories,

                user_name=session.get(
                    "full_name",
                    "Patient"
                )
            )

        except Exception as error:

            print(
                "PATIENT HISTORY PAGE ERROR:",
                error
            )

            return render_template(
                "patient_history.html",

                patient_histories=[],

                histories=[],

                user_name=session.get(
                    "full_name",
                    "Patient"
                )
            )

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # PATIENT DOCUMENTS PAGE
    # =====================================================

    @app.route("/patient/documents")
    def patient_documents():

        if not patient_logged_in():
            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        return render_template(
            "patient_documents.html"
        )


    # =====================================================
    # PHYSICIAN REVIEW PAGE
    # =====================================================

    @app.route("/physician-review")
    def physician_review():

        if not patient_logged_in():

            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        patient_id = get_logged_in_patient_id()

        connection = None
        cursor = None

        history = None
        patient = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            # =================================================
            # LOAD PATIENT DETAILS
            # =================================================

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
                (
                    patient_id,
                )
            )

            patient = cursor.fetchone()

            # =================================================
            # LOAD LATEST CLINICAL INTAKE
            # =================================================

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
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (
                    patient_id,
                )
            )

            history = cursor.fetchone()

            # =================================================
            # REVIEW STATUS
            # =================================================

            if history:

                review_status = (
                    "Case submitted for physician review"
                )

                has_case = True

            else:

                review_status = (
                    "Review status not available yet"
                )

                has_case = False

            # =================================================
            # DEBUG
            # =================================================

            print(
                "PHYSICIAN REVIEW:",
                {
                    "patient_id": patient_id,
                    "history_id": (
                        history.get("id")
                        if history
                        else None
                    ),
                    "has_case": has_case
                }
            )

            # =================================================
            # RENDER PHYSICIAN REVIEW
            # =================================================

            return render_template(
                "physician_review.html",

                # Patient information
                patient=patient,

                patient_name=(
                    patient.get("full_name")
                    if patient
                    else session.get(
                        "full_name",
                        "Patient"
                    )
                ),

                patient_id=patient_id,

                # Main history object
                history=history,

                case_history=history,

                latest_history=history,

                # Review information
                review_status=review_status,

                physician_review=None,

                has_case=has_case,

                # Individual fields
                main_problem=(
                    history.get("main_problem")
                    if history
                    else None
                ),

                duration=(
                    history.get("duration")
                    if history
                    else None
                ),

                symptoms=(
                    history.get("symptoms")
                    if history
                    else None
                ),

                medical_history=(
                    history.get("medical_history")
                    if history
                    else None
                ),

                medicines=(
                    history.get("medicines")
                    if history
                    else None
                ),

                allergies=(
                    history.get("allergies")
                    if history
                    else None
                ),

                summary=(
                    history.get("summary")
                    if history
                    else None
                ),

                created_at=(
                    history.get("created_at")
                    if history
                    else None
                )
            )

        except Exception as error:

            print(
                "PHYSICIAN REVIEW PAGE ERROR:",
                error
            )

            return render_template(
                "physician_review.html",

                patient=None,

                patient_name=session.get(
                    "full_name",
                    "Patient"
                ),

                patient_id=patient_id,

                history=None,

                case_history=None,

                latest_history=None,

                review_status=(
                    "Review status not available yet"
                ),

                physician_review=None,

                has_case=False,

                main_problem=None,
                duration=None,
                symptoms=None,
                medical_history=None,
                medicines=None,
                allergies=None,
                summary=None,
                created_at=None
            )

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # UPLOAD DOCUMENT
    # =====================================================

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

        patient_id = get_logged_in_patient_id()

        uploaded_file = request.files.get(
            "document"
        )

        if uploaded_file is None:
            uploaded_file = request.files.get(
                "file"
            )

        if uploaded_file is None:
            return redirect(
                url_for("patient_documents")
            )

        if not uploaded_file.filename:
            return redirect(
                url_for("patient_documents")
            )

        original_filename = secure_filename(
            uploaded_file.filename
        )

        if not original_filename:
            return redirect(
                url_for("patient_documents")
            )

        if not allowed_document(
            original_filename
        ):
            return redirect(
                url_for("patient_documents")
            )

        extension = original_filename.rsplit(
            ".",
            1
        )[1].lower()

        unique_filename = (
            str(uuid.uuid4())
            + "."
            + extension
        )

        upload_folder = app.config.get(
            "UPLOAD_FOLDER"
        )

        if not upload_folder:

            upload_folder = os.path.join(
                app.root_path,
                "uploads"
            )

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        file_path = os.path.join(
            upload_folder,
            unique_filename
        )

        connection = None
        cursor = None

        try:

            # =================================================
            # SAVE FILE
            # =================================================

            uploaded_file.save(
                file_path
            )

            # =================================================
            # SAVE DATABASE RECORD
            # =================================================

            connection = get_db_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO patient_documents
                (
                    patient_id,
                    file_name,
                    file_path,
                    file_type
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    patient_id,
                    original_filename,
                    unique_filename,
                    extension
                )
            )

            connection.commit()

            print(
                "DOCUMENT UPLOADED:",
                original_filename,
                "patient_id=",
                patient_id
            )

            return redirect(
                url_for(
                    "patient_documents"
                )
            )

        except Exception as error:

            print(
                "DOCUMENT UPLOAD ERROR:",
                error
            )

            if os.path.exists(
                file_path
            ):

                try:

                    os.remove(
                        file_path
                    )

                except Exception:
                    pass

            if connection:

                try:

                    connection.rollback()

                except Exception:
                    pass

            return redirect(
                url_for(
                    "patient_documents"
                )
            )

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # VIEW PATIENT DOCUMENT
    # =====================================================

    @app.route(
        "/patient/document/<int:document_id>"
    )
    def view_patient_document(
        document_id
    ):

        if not patient_logged_in():
            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        patient_id = get_logged_in_patient_id()

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
                    patient_id,
                    file_name,
                    file_path,
                    file_type
                FROM patient_documents
                WHERE id = %s
                  AND patient_id = %s
                LIMIT 1
                """,
                (
                    document_id,
                    patient_id
                )
            )

            document = cursor.fetchone()

            if not document:

                return (
                    "Document not found.",
                    404
                )

            upload_folder = app.config.get(
                "UPLOAD_FOLDER"
            )

            if not upload_folder:

                upload_folder = os.path.join(
                    app.root_path,
                    "uploads"
                )

            stored_filename = os.path.basename(
                document["file_path"]
            )

            full_path = os.path.join(
                upload_folder,
                stored_filename
            )

            if not os.path.exists(
                full_path
            ):

                return (
                    "Document file not found.",
                    404
                )

            return send_from_directory(
                upload_folder,

                stored_filename,

                as_attachment=False,

                download_name=document[
                    "file_name"
                ]
            )

        except Exception as error:

            print(
                "VIEW DOCUMENT ERROR:",
                error
            )

            return (
                "Unable to open document.",
                500
            )

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # PATIENT DETAILS API
    # =====================================================

    @app.route(
        "/api/patient/details",
        methods=["GET"],
        endpoint="api_patient_details"
    )
    def patient_details_api():

        if not patient_logged_in():

            return jsonify({
                "success": False,
                "message": "Patient login required."
            }), 401

        patient_id = get_logged_in_patient_id()

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
                    full_name,
                    age,
                    gender,
                    phone,
                    abha_id
                FROM patients
                WHERE id = %s
                LIMIT 1
                """,
                (
                    patient_id,
                )
            )

            patient = cursor.fetchone()

            if not patient:

                return jsonify({
                    "success": False,
                    "message": "Patient not found."
                }), 404

            return jsonify({
                "success": True,
                "patient": patient
            })

        except Exception as error:

            print(
                "PATIENT DETAILS ERROR:",
                error
            )

            return jsonify({
                "success": False,
                "message": "Unable to load patient details.",
                "error": str(error)
            }), 500

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # PATIENT HISTORY API
    # =====================================================

    @app.route(
        "/api/patient/history",
        methods=["GET"],
        endpoint="api_patient_history"
    )
    def patient_history_api():

        if not patient_logged_in():

            return jsonify({
                "success": False,
                "message": "Patient login required."
            }), 401

        patient_id = get_logged_in_patient_id()

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
                ORDER BY created_at DESC, id DESC
                """,
                (
                    patient_id,
                )
            )

            histories = cursor.fetchall()

            return jsonify({
                "success": True,

                "history": histories,

                "histories": histories
            })

        except Exception as error:

            print(
                "PATIENT HISTORY ERROR:",
                error
            )

            return jsonify({
                "success": False,
                "message": "Unable to load patient history.",
                "error": str(error)
            }), 500

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # PATIENT CONVERSATION HISTORY API
    # =====================================================

    @app.route(
        "/api/patient/conversations",
        methods=["GET"],
        endpoint="api_patient_conversations"
    )
    def patient_conversations():

        if not patient_logged_in():

            return jsonify({
                "success": False,
                "message": "Patient login required."
            }), 401

        patient_id = get_logged_in_patient_id()

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
                    patient_id,
                    sender,
                    message,
                    session_id,
                    created_at
                FROM clinical_conversations
                WHERE patient_id = %s
                ORDER BY id ASC
                """,
                (
                    patient_id,
                )
            )

            conversations = cursor.fetchall()

            return jsonify({
                "success": True,

                "conversation": conversations,

                "conversations": conversations
            })

        except Exception as error:

            print(
                "PATIENT CONVERSATION ERROR:",
                error
            )

            return jsonify({
                "success": False,
                "message": "Unable to load conversations.",
                "error": str(error)
            }), 500

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # PATIENT DOCUMENTS API
    # =====================================================

    @app.route(
        "/api/patient/documents",
        methods=["GET"],
        endpoint="api_patient_documents"
    )
    def patient_documents_api():

        if not patient_logged_in():

            return jsonify({
                "success": False,
                "message": "Patient login required."
            }), 401

        patient_id = get_logged_in_patient_id()

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
                    patient_id,
                    file_name,
                    file_path,
                    file_type,
                    uploaded_at
                FROM patient_documents
                WHERE patient_id = %s
                ORDER BY uploaded_at DESC, id DESC
                """,
                (
                    patient_id,
                )
            )

            documents = cursor.fetchall()

            return jsonify({
                "success": True,
                "documents": documents
            })

        except Exception as error:

            print(
                "PATIENT DOCUMENTS ERROR:",
                error
            )

            return jsonify({
                "success": False,
                "message": "Unable to load documents.",
                "error": str(error)
            }), 500

        finally:

            safe_close(
                cursor,
                connection
            )