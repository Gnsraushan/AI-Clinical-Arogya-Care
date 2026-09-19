from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from mysql.connector import Error

from services.database import (
    get_db_connection,
    safe_close
)


def register_auth_routes(app):

    # =========================================================
    # HOME / INDEX
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


    @app.route("/index.html")
    def index():

        return redirect(
            url_for("home")
        )


    # =========================================================
    # LOGOUT
    # =========================================================

    @app.route("/logout")
    def logout():

        session.clear()

        return redirect(
            url_for(
                "login_page"
            )
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

        if role not in [
            "patient",
            "doctor"
        ]:
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

        if role not in [
            "patient",
            "doctor"
        ]:
            role = "patient"

        return render_template(
            "register.html",
            role=role
        )


    # =========================================================
    # REGISTER USER
    # =========================================================

    @app.route(
        "/register",
        methods=["POST"]
    )
    def register_user():

        role = request.form.get(
            "role",
            "patient"
        ).lower()

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            # =================================================
            # PATIENT REGISTRATION
            # =================================================

            if role == "patient":

                full_name = request.form.get(
                    "fullName",
                    ""
                ).strip()

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

                patient_id = request.form.get(
                    "patientId",
                    ""
                ).strip()

                password = request.form.get(
                    "password",
                    ""
                )

                if not all([
                    full_name,
                    age,
                    gender,
                    phone,
                    patient_id,
                    password
                ]):

                    return render_template(
                        "register.html",
                        role="patient",
                        error=(
                            "Please fill all required fields."
                        )
                    )


                # ---------------------------------------------
                # DUPLICATE PHONE
                # ---------------------------------------------

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

                    return render_template(
                        "register.html",
                        role="patient",
                        error=(
                            "Phone number is already registered."
                        )
                    )


                # ---------------------------------------------
                # DUPLICATE ABHA ID
                # ---------------------------------------------

                cursor.execute(
                    """
                    SELECT id
                    FROM patients
                    WHERE abha_id = %s
                    LIMIT 1
                    """,
                    (patient_id,)
                )

                if cursor.fetchone():

                    return render_template(
                        "register.html",
                        role="patient",
                        error=(
                            "ABHA / Patient ID is already registered."
                        )
                    )


                password_hash = generate_password_hash(
                    password
                )


                # ---------------------------------------------
                # INSERT PATIENT
                # ---------------------------------------------

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
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        full_name,
                        age,
                        gender,
                        phone,
                        patient_id,
                        password_hash
                    )
                )

                connection.commit()

                return redirect(
                    url_for(
                        "login_page",
                        role="patient",
                        registered="1"
                    )
                )


            # =================================================
            # DOCTOR / STAFF REGISTRATION
            # =================================================

            elif role == "doctor":

                full_name = request.form.get(
                    "fullName",
                    ""
                ).strip()

                email = request.form.get(
                    "email",
                    ""
                ).strip()

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

                password = request.form.get(
                    "password",
                    ""
                )


                if not all([
                    full_name,
                    email,
                    staff_role,
                    department,
                    hospital,
                    password
                ]):

                    return render_template(
                        "register.html",
                        role="doctor",
                        error=(
                            "Please fill all required fields."
                        )
                    )


                # ---------------------------------------------
                # DUPLICATE EMAIL
                # ---------------------------------------------

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

                    return render_template(
                        "register.html",
                        role="doctor",
                        error=(
                            "Email is already registered."
                        )
                    )


                password_hash = generate_password_hash(
                    password
                )


                # ---------------------------------------------
                # INSERT DOCTOR
                # ---------------------------------------------

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
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
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
                        role="doctor",
                        registered="1"
                    )
                )


            # =================================================
            # INVALID ROLE
            # =================================================

            else:

                return render_template(
                    "register.html",
                    role="patient",
                    error="Invalid registration role."
                )


        except Error as e:

            print(
                "REGISTRATION DATABASE ERROR:",
                e
            )

            return render_template(
                "register.html",
                role=role,
                error=(
                    "Registration failed. "
                    "Please try again."
                )
            )


        except Exception as e:

            print(
                "REGISTRATION UNEXPECTED ERROR:",
                e
            )

            return render_template(
                "register.html",
                role=role,
                error=(
                    "Something went wrong. "
                    "Please try again."
                )
            )


        finally:

            safe_close(
                cursor=cursor,
                connection=connection
            )


    # =========================================================
    # LOGIN USER
    # =========================================================

    @app.route(
        "/login",
        methods=["POST"]
    )
    def login_user():

        role = request.form.get(
            "role",
            "patient"
        ).lower()

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

                identifier = (
                    request.form.get(
                        "patientIdentifier"
                    )
                    or request.form.get(
                        "email"
                    )
                    or ""
                ).strip()

                password = request.form.get(
                    "password",
                    ""
                )


                if not identifier or not password:

                    return render_template(
                        "login.html",
                        role="patient",
                        error=(
                            "Please enter your login details."
                        )
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

                patient = cursor.fetchone()


                if not patient:

                    return render_template(
                        "login.html",
                        role="patient",
                        error=(
                            "Invalid phone / ABHA ID "
                            "or password."
                        )
                    )


                if not check_password_hash(
                    patient["password_hash"],
                    password
                ):

                    return render_template(
                        "login.html",
                        role="patient",
                        error=(
                            "Invalid phone / ABHA ID "
                            "or password."
                        )
                    )


                # ---------------------------------------------
                # PATIENT SESSION
                # ---------------------------------------------

                session.clear()

                session["logged_in"] = True
                session["role"] = "patient"

                session["user_id"] = patient["id"]
                session["patient_id"] = patient["id"]

                session["full_name"] = patient["full_name"]
                session["phone"] = patient["phone"]
                session["abha_id"] = patient["abha_id"]


                return redirect(
                    url_for(
                        "patient_dashboard"
                    )
                )


            # =================================================
            # DOCTOR LOGIN
            # =================================================

            elif role == "doctor":

                identifier = (
                    request.form.get(
                        "email"
                    )
                    or request.form.get(
                        "patientIdentifier"
                    )
                    or ""
                ).strip()

                password = request.form.get(
                    "password",
                    ""
                )


                if not identifier or not password:

                    return render_template(
                        "login.html",
                        role="doctor",
                        error=(
                            "Please enter your login details."
                        )
                    )


                cursor.execute(
                    """
                    SELECT *
                    FROM staff
                    WHERE email = %s
                    LIMIT 1
                    """,
                    (identifier,)
                )

                doctor = cursor.fetchone()


                if not doctor:

                    return render_template(
                        "login.html",
                        role="doctor",
                        error=(
                            "Invalid email or password."
                        )
                    )


                if not check_password_hash(
                    doctor["password_hash"],
                    password
                ):

                    return render_template(
                        "login.html",
                        role="doctor",
                        error=(
                            "Invalid email or password."
                        )
                    )


                # ---------------------------------------------
                # DOCTOR SESSION
                # ---------------------------------------------

                session.clear()

                session["logged_in"] = True
                session["role"] = "doctor"

                session["user_id"] = doctor["id"]
                session["doctor_id"] = doctor["id"]

                session["full_name"] = doctor["full_name"]
                session["email"] = doctor["email"]
                session["staff_role"] = doctor["staff_role"]
                session["department"] = doctor["department"]
                session["hospital"] = doctor["hospital"]


                return redirect(
    url_for(
        "doctor_dashboard"
    )
)


            # =================================================
            # INVALID LOGIN ROLE
            # =================================================

            else:

                return render_template(
                    "login.html",
                    role="patient",
                    error="Invalid login role."
                )


        except Error as e:

            print(
                "LOGIN DATABASE ERROR:",
                e
            )

            return render_template(
                "login.html",
                role=role,
                error=(
                    "Unable to connect to the database."
                )
            )


        except Exception as e:

            print(
                "LOGIN UNEXPECTED ERROR:",
                e
            )

            return render_template(
                "login.html",
                role=role,
                error=(
                    "Something went wrong. "
                    "Please try again."
                )
            )


        finally:

            safe_close(
                cursor=cursor,
                connection=connection
            )