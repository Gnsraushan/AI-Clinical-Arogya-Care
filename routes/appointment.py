from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from services.database import get_db_connection, safe_close
from services.helpers import patient_logged_in, doctor_logged_in


# =========================================================
# REGISTER APPOINTMENT ROUTES
# =========================================================

def register_appointment_routes(app):

    # =====================================================
    # FIND DOCTOR PAGE
    # =====================================================

    @app.route("/find-doctor")
    def find_doctor():

        if not patient_logged_in():
            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        return render_template(
            "find_doctor.html"
        )


    # =====================================================
    # PATIENT APPOINTMENTS PAGE
    # =====================================================

    @app.route("/appointments")
    def appointments():

        if not patient_logged_in():
            return redirect(
                url_for(
                    "login_page",
                    role="patient"
                )
            )

        return render_template(
            "appointments.html"
        )


    # =====================================================
    # GET AVAILABLE DOCTORS
    # =====================================================

    @app.route(
        "/api/appointments/doctors",
        methods=["GET"]
    )
    def appointment_doctors():

        if not patient_logged_in():
            return jsonify({
                "success": False,
                "error": "Unauthorized"
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
                    full_name,
                    email,
                    staff_role,
                    department,
                    hospital
                FROM staff
                ORDER BY full_name ASC
                """
            )

            doctors = cursor.fetchall()

            result = []

            for doctor in doctors:

                result.append({
                    "id": doctor["id"],
                    "full_name": doctor["full_name"],
                    "email": doctor["email"],
                    "staff_role": doctor["staff_role"],
                    "department": doctor["department"],
                    "hospital": doctor["hospital"]
                })

            return jsonify({
                "success": True,
                "doctors": result
            })

        except Exception as e:

            print(
                "APPOINTMENT DOCTORS ERROR:",
                e
            )

            return jsonify({
                "success": False,
                "error": "Unable to load doctors."
            }), 500

        finally:

            safe_close(
                cursor=cursor,
                connection=connection
            )


    # =====================================================
    # BOOK APPOINTMENT
    # =====================================================

    @app.route(
        "/api/appointments/book",
        methods=["POST"]
    )
    def book_appointment():

        if not patient_logged_in():
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 401

        data = request.get_json(
            silent=True
        ) or {}

        doctor_id = data.get(
            "doctor_id"
        )

        appointment_date = data.get(
            "appointment_date"
        )

        appointment_time = data.get(
            "appointment_time"
        )

        mode = str(
            data.get(
                "mode",
                ""
            )
        ).lower().strip()

        notes = str(
            data.get(
                "notes",
                ""
            )
        ).strip()

        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not doctor_id:
            return jsonify({
                "success": False,
                "error": "Please select a doctor."
            }), 400

        if not appointment_date:
            return jsonify({
                "success": False,
                "error": "Please select an appointment date."
            }), 400

        if not appointment_time:
            return jsonify({
                "success": False,
                "error": "Please select an appointment time."
            }), 400

        if mode not in (
            "online",
            "offline"
        ):
            return jsonify({
                "success": False,
                "error": "Invalid appointment mode."
            }), 400

        patient_id = session.get(
            "user_id"
        )

        if not patient_id:
            return jsonify({
                "success": False,
                "error": "Patient session not found."
            }), 401

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            # -------------------------------------------------
            # CHECK DOCTOR
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT
                    id,
                    full_name,
                    department,
                    hospital
                FROM staff
                WHERE id = %s
                LIMIT 1
                """,
                (doctor_id,)
            )

            doctor = cursor.fetchone()

            if not doctor:

                return jsonify({
                    "success": False,
                    "error": "Selected doctor was not found."
                }), 404

            # -------------------------------------------------
            # PREVENT DUPLICATE BOOKING
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT id
                FROM appointments
                WHERE patient_id = %s
                  AND doctor_id = %s
                  AND appointment_date = %s
                  AND appointment_time = %s
                  AND status IN (
                      'pending',
                      'confirmed'
                  )
                LIMIT 1
                """,
                (
                    patient_id,
                    doctor_id,
                    appointment_date,
                    appointment_time
                )
            )

            existing = cursor.fetchone()

            if existing:

                return jsonify({
                    "success": False,
                    "error": "You already have an appointment at this time."
                }), 409

            # -------------------------------------------------
            # CREATE APPOINTMENT
            # -------------------------------------------------

            cursor.execute(
                """
                INSERT INTO appointments
                (
                    patient_id,
                    doctor_id,
                    appointment_date,
                    appointment_time,
                    mode,
                    status,
                    notes
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'pending',
                    %s
                )
                """,
                (
                    patient_id,
                    doctor_id,
                    appointment_date,
                    appointment_time,
                    mode,
                    notes
                )
            )

            connection.commit()

            appointment_id = cursor.lastrowid

            return jsonify({
                "success": True,
                "message": "Appointment booked successfully.",
                "appointment_id": appointment_id,
                "mode": mode,
                "status": "pending"
            })

        except Exception as e:

            print(
                "BOOK APPOINTMENT ERROR:",
                e
            )

            if connection:
                try:
                    connection.rollback()
                except Exception:
                    pass

            return jsonify({
                "success": False,
                "error": "Unable to book appointment."
            }), 500

        finally:

            safe_close(
                cursor=cursor,
                connection=connection
            )


    # =====================================================
    # PATIENT APPOINTMENT LIST
    # =====================================================

    @app.route(
        "/api/appointments/my",
        methods=["GET"]
    )
    def patient_appointments():

        if not patient_logged_in():
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 401

        patient_id = session.get(
            "user_id"
        )

        if not patient_id:
            return jsonify({
                "success": False,
                "error": "Patient session not found."
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
                    a.id,
                    a.appointment_date,
                    a.appointment_time,
                    a.mode,
                    a.status,
                    a.notes,
                    a.created_at,
                    s.id AS doctor_id,
                    s.full_name AS doctor_name,
                    s.department,
                    s.hospital
                FROM appointments a
                JOIN staff s
                    ON a.doctor_id = s.id
                WHERE a.patient_id = %s
                ORDER BY
                    a.appointment_date DESC,
                    a.appointment_time DESC
                """,
                (patient_id,)
            )

            appointments_list = cursor.fetchall()

            return jsonify({
                "success": True,
                "appointments": appointments_list
            })

        except Exception as e:

            print(
                "PATIENT APPOINTMENTS ERROR:",
                e
            )

            return jsonify({
                "success": False,
                "error": "Unable to load appointments."
            }), 500

        finally:

            safe_close(
                cursor=cursor,
                connection=connection
            )


    # =====================================================
    # DOCTOR APPOINTMENTS PAGE
    # =====================================================

    @app.route(
        "/doctor/appointments"
    )
    def doctor_appointments():

        if not doctor_logged_in():
            return redirect(
                url_for(
                    "login_page",
                    role="doctor"
                )
            )

        return render_template(
            "doctor_appointments.html"
        )


    # =====================================================
    # DOCTOR APPOINTMENT LIST
    # =====================================================

    @app.route(
        "/api/doctor/appointments",
        methods=["GET"]
    )
    def doctor_appointment_list():

        if not doctor_logged_in():
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 401

        doctor_id = session.get(
            "user_id"
        )

        if not doctor_id:
            return jsonify({
                "success": False,
                "error": "Doctor session not found."
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
                    a.id,
                    a.appointment_date,
                    a.appointment_time,
                    a.mode,
                    a.status,
                    a.notes,
                    a.created_at,
                    p.id AS patient_id,
                    p.full_name AS patient_name,
                    p.age,
                    p.gender,
                    p.phone,
                    p.abha_id
                FROM appointments a
                JOIN patients p
                    ON a.patient_id = p.id
                WHERE a.doctor_id = %s
                ORDER BY
                    a.appointment_date ASC,
                    a.appointment_time ASC
                """,
                (doctor_id,)
            )

            appointments_list = cursor.fetchall()

            return jsonify({
                "success": True,
                "appointments": appointments_list
            })

        except Exception as e:

            print(
                "DOCTOR APPOINTMENTS ERROR:",
                e
            )

            return jsonify({
                "success": False,
                "error": "Unable to load doctor appointments."
            }), 500

        finally:

            safe_close(
                cursor=cursor,
                connection=connection
            )


    # =====================================================
    # DOCTOR UPDATE APPOINTMENT STATUS
    # =====================================================

    @app.route(
        "/api/doctor/appointments/<int:appointment_id>/status",
        methods=["POST"]
    )
    def update_appointment_status(
        appointment_id
    ):

        if not doctor_logged_in():
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 401

        data = request.get_json(
            silent=True
        ) or {}

        status = str(
            data.get(
                "status",
                ""
            )
        ).lower().strip()

        allowed_statuses = {
            "pending",
            "confirmed",
            "completed",
            "cancelled"
        }

        if status not in allowed_statuses:

            return jsonify({
                "success": False,
                "error": "Invalid appointment status."
            }), 400

        doctor_id = session.get(
            "user_id"
        )

        if not doctor_id:
            return jsonify({
                "success": False,
                "error": "Doctor session not found."
            }), 401

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE appointments
                SET status = %s
                WHERE id = %s
                  AND doctor_id = %s
                """,
                (
                    status,
                    appointment_id,
                    doctor_id
                )
            )

            connection.commit()

            if cursor.rowcount == 0:

                return jsonify({
                    "success": False,
                    "error": "Appointment not found."
                }), 404

            return jsonify({
                "success": True,
                "message": "Appointment status updated.",
                "status": status
            })

        except Exception as e:

            print(
                "UPDATE APPOINTMENT STATUS ERROR:",
                e
            )

            if connection:
                try:
                    connection.rollback()
                except Exception:
                    pass

            return jsonify({
                "success": False,
                "error": "Unable to update appointment."
            }), 500

        finally:

            safe_close(
                cursor=cursor,
                connection=connection
            )