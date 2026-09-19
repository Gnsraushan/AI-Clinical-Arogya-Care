from flask import render_template, request, jsonify, session

from services.database import get_db_connection, safe_close
from services.clinical_service import detect_red_flags


# =========================================================
# DOCTOR SESSION HELPERS
# =========================================================

def get_logged_in_doctor_id():
    """
    Doctor ID can come from either doctor_id or user_id.
    Keeps compatibility with existing login/session code.
    """
    doctor_id = session.get("doctor_id")

    if doctor_id is None:
        doctor_id = session.get("user_id")

    return doctor_id


def doctor_logged_in():
    """
    Check whether a valid doctor session exists.
    """

    return (
        session.get("logged_in") is True
        and session.get("role") == "doctor"
        and get_logged_in_doctor_id() is not None
    )


# =========================================================
# RED FLAG CALCULATION
# =========================================================

def calculate_patient_red_flags(conversations):

    red_flag_detected = False
    red_flag_reasons = []
    red_flag_categories = []

    for row in conversations:

        sender = str(
            row.get("sender") or ""
        ).lower().strip()

        # Only analyze patient's messages
        if sender != "patient":
            continue

        message = str(
            row.get("message") or ""
        ).strip()

        if not message:
            continue

        try:

            result = detect_red_flags(
                message
            )

        except Exception as error:

            print(
                "RED FLAG DETECTION ERROR:",
                error
            )

            continue

        if result.get("detected"):

            red_flag_detected = True

            reason = str(
                result.get("reason") or ""
            ).strip()

            category = str(
                result.get("category") or ""
            ).strip()

            if (
                reason
                and reason not in red_flag_reasons
            ):
                red_flag_reasons.append(
                    reason
                )

            if (
                category
                and category not in red_flag_categories
            ):
                red_flag_categories.append(
                    category
                )

    return {
        "detected": red_flag_detected,
        "reasons": red_flag_reasons,
        "categories": red_flag_categories
    }


# =========================================================
# REGISTER DOCTOR ROUTES
# =========================================================

def register_doctor_routes(app):

    # =====================================================
    # DOCTOR DASHBOARD
    # =====================================================

    @app.route("/dashboard")
    def doctor_dashboard():

        # -------------------------------------------------
        # DEBUG: SHOW CURRENT SESSION
        # -------------------------------------------------

        print(
            "DOCTOR SESSION:",
            dict(session)
        )

        # -------------------------------------------------
        # DOCTOR LOGIN CHECK
        # -------------------------------------------------

        if not doctor_logged_in():

            print(
                "DOCTOR DASHBOARD LOGIN CHECK FAILED:",
                {
                    "logged_in": session.get(
                        "logged_in"
                    ),
                    "role": session.get(
                        "role"
                    ),
                    "user_id": session.get(
                        "user_id"
                    ),
                    "doctor_id": session.get(
                        "doctor_id"
                    )
                }
            )

            return jsonify({
                "success": False,
                "message": "Doctor login required."
            }), 401

        # -------------------------------------------------
        # DOCTOR DASHBOARD
        # -------------------------------------------------

        return render_template(
            "doctor_dashboard.html",

            doctor_name=(
                session.get(
                    "full_name"
                )
                or "Doctor"
            ),

            doctor_email=(
                session.get(
                    "email"
                )
                or ""
            ),

            staff_role=(
                session.get(
                    "staff_role"
                )
                or "Clinical Staff"
            ),

            department=(
                session.get(
                    "department"
                )
                or ""
            ),

            hospital=(
                session.get(
                    "hospital"
                )
                or ""
            )
        )


    # =====================================================
    # SEARCH PATIENTS
    # =====================================================

    @app.route(
        "/api/doctor/patients/search",
        methods=["GET"]
    )
    def search_doctor_patients():

        if not doctor_logged_in():

            return jsonify({
                "success": False,
                "message": "Doctor login required."
            }), 401

        search = str(
            request.args.get("q") or ""
        ).strip()

        if not search:

            return jsonify({
                "success": True,
                "patients": [],
                "results": []
            })

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            # -------------------------------------------------
            # SEARCH PATIENT
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
                WHERE
                    full_name LIKE %s
                    OR phone LIKE %s
                    OR abha_id LIKE %s
                ORDER BY id DESC
                LIMIT 50
                """,
                (
                    "%" + search + "%",
                    "%" + search + "%",
                    "%" + search + "%"
                )
            )

            patients = cursor.fetchall()

            result = []

            for patient in patients:

                patient_id = patient["id"]

                # -------------------------------------------------
                # LATEST HISTORY
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
                    ORDER BY created_at DESC, id DESC
                    LIMIT 1
                    """,
                    (patient_id,)
                )

                history = cursor.fetchone()

                # -------------------------------------------------
                # CONVERSATIONS
                # -------------------------------------------------

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
                    ORDER BY id DESC
                    LIMIT 50
                    """,
                    (patient_id,)
                )

                conversations = cursor.fetchall()

                # -------------------------------------------------
                # RED FLAGS
                # -------------------------------------------------

                red_flags = (
                    calculate_patient_red_flags(
                        conversations
                    )
                )

                result.append({

                    "id": patient["id"],

                    "full_name": patient.get(
                        "full_name"
                    ),

                    "age": patient.get(
                        "age"
                    ),

                    "gender": patient.get(
                        "gender"
                    ),

                    "phone": patient.get(
                        "phone"
                    ),

                    "abha_id": patient.get(
                        "abha_id"
                    ),

                    "history": history,

                    "latest_history": history,

                    "red_flag": red_flags[
                        "detected"
                    ],

                    "red_flags": red_flags[
                        "reasons"
                    ],

                    "red_flag_reasons": red_flags[
                        "reasons"
                    ],

                    "red_flag_categories": red_flags[
                        "categories"
                    ]
                })

            return jsonify({

                "success": True,

                "patients": result,

                "results": result
            })

        except Exception as error:

            print(
                "DOCTOR PATIENT SEARCH ERROR:",
                error
            )

            return jsonify({

                "success": False,

                "message": (
                    "Unable to search patients."
                ),

                "error": str(error)

            }), 500

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # GET COMPLETE PATIENT CASE
    # =====================================================

    @app.route(
        "/api/doctor/patient/<int:patient_id>",
        methods=["GET"]
    )
    def doctor_patient_case(
        patient_id
    ):

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
            # PATIENT DETAILS
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
            # LATEST HISTORY
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
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (patient_id,)
            )

            history = cursor.fetchone()

            # -------------------------------------------------
            # ALL CONVERSATIONS
            # -------------------------------------------------

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
                (patient_id,)
            )

            conversations = cursor.fetchall()

            # -------------------------------------------------
            # RED FLAGS
            # -------------------------------------------------

            red_flags = (
                calculate_patient_red_flags(
                    conversations
                )
            )

            # -------------------------------------------------
            # DOCUMENTS
            # -------------------------------------------------

            documents = []

            try:

                cursor.execute(
                    """
                    SELECT *
                    FROM patient_documents
                    WHERE patient_id = %s
                    ORDER BY id DESC
                    """,
                    (patient_id,)
                )

                documents = cursor.fetchall()

            except Exception as document_error:

                print(
                    "PATIENT DOCUMENT QUERY WARNING:",
                    document_error
                )

                documents = []

            # -------------------------------------------------
            # ADD RED FLAGS TO HISTORY
            # -------------------------------------------------

            if history:

                history["red_flag"] = (
                    red_flags["detected"]
                )

                history["red_flags"] = (
                    red_flags["reasons"]
                )

                history["red_flag_reasons"] = (
                    red_flags["reasons"]
                )

                history["red_flag_categories"] = (
                    red_flags["categories"]
                )

            # -------------------------------------------------
            # RESPONSE
            # -------------------------------------------------

            return jsonify({

                "success": True,

                "patient": patient,

                "history": history,

                "latest_history": history,

                "conversation": conversations,

                "conversations": conversations,

                "documents": documents,

                "red_flag": red_flags[
                    "detected"
                ],

                "red_flags": red_flags[
                    "reasons"
                ],

                "red_flag_reason": (
                    "; ".join(
                        red_flags["reasons"]
                    )
                ),

                "red_flag_reasons": red_flags[
                    "reasons"
                ],

                "red_flag_category": (
                    ", ".join(
                        red_flags["categories"]
                    )
                ),

                "red_flag_categories": red_flags[
                    "categories"
                ]
            })

        except Exception as error:

            if connection:

                try:
                    connection.rollback()
                except Exception:
                    pass

            print(
                "DOCTOR PATIENT DETAILS ERROR:",
                error
            )

            return jsonify({

                "success": False,

                "message": (
                    "Unable to load patient case."
                ),

                "error": str(error)

            }), 500

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # VERIFY PATIENT CASE
    # =====================================================

    @app.route(
        "/api/doctor/patient/<int:patient_id>/verify",
        methods=["POST"]
    )
    def verify_patient_case(
        patient_id
    ):

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

                "message": (
                    "Patient case verified."
                )
            })

        except Exception as error:

            print(
                "VERIFY CASE ERROR:",
                error
            )

            return jsonify({

                "success": False,

                "message": (
                    "Unable to verify patient case."
                ),

                "error": str(error)

            }), 500

        finally:

            safe_close(
                cursor,
                connection
            )