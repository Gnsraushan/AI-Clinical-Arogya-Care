from flask import (
    render_template,
    request,
    jsonify,
    session
)

from services.database import (
    get_db_connection,
    safe_close
)

from services.clinical_service import (
    detect_red_flags
)

from services.ai_service import (
    generate_intake_reply,
    generate_complete_history
)


# =========================================================
# PATIENT ID HELPER
# =========================================================

def get_logged_in_patient_id():
    """
    New patient login flow uses user_id.
    Older AI flow used patient_id.

    user_id is preferred, patient_id is kept as fallback
    for compatibility.
    """

    patient_id = session.get("user_id")

    if patient_id is None:
        patient_id = session.get("patient_id")

    return patient_id


# =========================================================
# PATIENT LOGIN CHECK
# =========================================================

def patient_logged_in():

    return (
        session.get("logged_in") is True
        and session.get("role") == "patient"
        and get_logged_in_patient_id() is not None
    )


# =========================================================
# GET OR CREATE CURRENT INTAKE SESSION
# =========================================================

def get_current_session_id(
    connection,
    cursor,
    patient_id
):

    current_session_id = session.get(
        "intake_session_id"
    )

    if current_session_id:

        cursor.execute(
            """
            SELECT
                id
            FROM intake_sessions
            WHERE id = %s
              AND patient_id = %s
            LIMIT 1
            """,
            (
                current_session_id,
                patient_id
            )
        )

        existing = cursor.fetchone()

        if existing:
            return existing["id"]

    cursor.execute(
        """
        INSERT INTO intake_sessions
        (
            patient_id
        )
        VALUES
        (
            %s
        )
        """,
        (
            patient_id,
        )
    )

    connection.commit()

    new_session_id = cursor.lastrowid

    session["intake_session_id"] = new_session_id

    return new_session_id


# =========================================================
# LOAD CURRENT CONVERSATION
# =========================================================

def load_current_conversation(
    cursor,
    patient_id,
    session_id
):

    cursor.execute(
        """
        SELECT
            id,
            patient_id,
            message,
            sender,
            created_at,
            session_id
        FROM clinical_conversations
        WHERE patient_id = %s
          AND session_id = %s
        ORDER BY id ASC
        """,
        (
            patient_id,
            session_id
        )
    )

    return cursor.fetchall()


# =========================================================
# RED FLAG CALCULATION
# =========================================================

def calculate_red_flags(rows):

    red_flag_detected = False

    red_flag_reasons = []

    red_flag_categories = []

    for row in rows:

        sender = str(
            row.get("sender") or ""
        ).lower().strip()

        if sender != "patient":
            continue

        message = str(
            row.get("message") or ""
        ).strip()

        if not message:
            continue

        result = detect_red_flags(
            message
        )

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

    if red_flag_detected:

        red_flag_text = (
            "Potential red flag detected. "
            "Reason: "
            + "; ".join(red_flag_reasons)
        )

    else:

        red_flag_text = (
            "No potential red flags detected."
        )

    return (
        red_flag_detected,
        red_flag_reasons,
        red_flag_categories,
        red_flag_text
    )


# =========================================================
# SAVE PATIENT HISTORY
# =========================================================

def save_patient_history(
    connection,
    cursor,
    patient_id,
    history
):

    history = history or {}

    main_problem = history.get(
        "main_problem"
    ) or "Not clearly stated."

    duration = history.get(
        "duration"
    ) or "Not clearly stated."

    symptoms = history.get(
        "symptoms"
    ) or "Not clearly stated."

    medical_history = history.get(
        "medical_history"
    ) or "Not clearly stated."

    medicines = history.get(
        "medicines"
    ) or "Not clearly stated."

    allergies = history.get(
        "allergies"
    ) or "Not clearly stated."

    summary = history.get(
        "summary"
    ) or "Not clearly stated."


    # =====================================================
    # CHECK LATEST HISTORY FOR THIS PATIENT
    # =====================================================

    cursor.execute(
        """
        SELECT
            id
        FROM patient_histories
        WHERE patient_id = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            patient_id,
        )
    )

    existing_history = cursor.fetchone()


    # =====================================================
    # UPDATE EXISTING HISTORY
    # =====================================================

    if existing_history:

        history_id = existing_history["id"]

        cursor.execute(
            """
            UPDATE patient_histories
            SET
                main_problem = %s,
                duration = %s,
                symptoms = %s,
                medical_history = %s,
                medicines = %s,
                allergies = %s,
                summary = %s
            WHERE id = %s
              AND patient_id = %s
            """,
            (
                main_problem,
                duration,
                symptoms,
                medical_history,
                medicines,
                allergies,
                summary,
                history_id,
                patient_id
            )
        )


    # =====================================================
    # CREATE NEW HISTORY
    # =====================================================

    else:

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
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
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

        history_id = cursor.lastrowid


    connection.commit()

    print(
        "PATIENT HISTORY SAVED:",
        "patient_id=",
        patient_id,
        "history_id=",
        history_id
    )

    return history_id


# =========================================================
# AI ROUTES
# =========================================================

def register_ai_routes(app):


    # =====================================================
    # AI CONVERSATION PAGE
    # =====================================================

    @app.route("/ai-conversation")
    def ai_conversation():

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

            current_session_id = get_current_session_id(
                connection,
                cursor,
                patient_id
            )

            conversations = load_current_conversation(
                cursor,
                patient_id,
                current_session_id
            )

            return render_template(
                "ai_conversation.html",
                conversations=conversations,
                allow_message_input=True,
                patient_id=patient_id,
                session_id=current_session_id
            )

        except Exception as error:

            print(
                "AI CONVERSATION PAGE ERROR:",
                error
            )

            return jsonify({
                "success": False,
                "message": "Unable to load AI conversation.",
                "error": str(error)
            }), 500

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # NEW CHAT SESSION
    # =====================================================

    @app.route(
        "/api/chat/new",
        methods=["POST"]
    )
    def new_chat_session():

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
                INSERT INTO intake_sessions
                (
                    patient_id
                )
                VALUES
                (
                    %s
                )
                """,
                (
                    patient_id,
                )
            )

            connection.commit()

            new_session_id = cursor.lastrowid

            session["intake_session_id"] = (
                new_session_id
            )

            return jsonify({
                "success": True,
                "session_id": new_session_id
            })

        except Exception as error:

            if connection:

                try:
                    connection.rollback()
                except Exception:
                    pass

            print(
                "NEW CHAT SESSION ERROR:",
                error
            )

            return jsonify({
                "success": False,
                "message": "Unable to start new conversation.",
                "error": str(error)
            }), 500

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # SEND AI MESSAGE
    # =====================================================

    @app.route(
        "/send-intake-message",
        methods=["POST"]
    )
    @app.route(
        "/api/chat",
        methods=["POST"]
    )
    def send_intake_message():

        if not patient_logged_in():

            return jsonify({
                "success": False,
                "message": "Patient login required."
            }), 401

        data = request.get_json(
            silent=True
        ) or {}

        message = str(
            data.get("message") or ""
        ).strip()

        if not message:

            return jsonify({
                "success": False,
                "message": "Message cannot be empty."
            }), 400

        patient_id = get_logged_in_patient_id()

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            # =================================================
            # CURRENT SESSION
            # =================================================

            current_session_id = get_current_session_id(
                connection,
                cursor,
                patient_id
            )


            # =================================================
            # SAVE PATIENT MESSAGE
            # =================================================

            cursor.execute(
                """
                INSERT INTO clinical_conversations
                (
                    patient_id,
                    message,
                    sender,
                    session_id
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
                    message,
                    "patient",
                    current_session_id
                )
            )

            connection.commit()


            # =================================================
            # LOAD CONVERSATION
            # =================================================

            rows = load_current_conversation(
                cursor,
                patient_id,
                current_session_id
            )

            conversation_messages = []

            for row in rows:

                sender = str(
                    row.get("sender") or ""
                ).lower().strip()

                if sender == "patient":
                    role = "user"
                else:
                    role = "assistant"

                content = str(
                    row.get("message") or ""
                ).strip()

                if content:

                    conversation_messages.append({
                        "role": role,
                        "content": content
                    })


            # =================================================
            # GENERATE AI REPLY
            # =================================================

            ai_reply = generate_intake_reply(
                conversation_messages
            )


            # =================================================
            # SAVE AI REPLY
            # =================================================

            cursor.execute(
                """
                INSERT INTO clinical_conversations
                (
                    patient_id,
                    message,
                    sender,
                    session_id
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
                    ai_reply,
                    "ai",
                    current_session_id
                )
            )

            connection.commit()


            # =================================================
            # LOAD COMPLETE CONVERSATION
            # =================================================

            complete_rows = load_current_conversation(
                cursor,
                patient_id,
                current_session_id
            )


            # =================================================
            # RED FLAGS
            # =================================================

            (
                red_flag_detected,
                red_flag_reasons,
                red_flag_categories,
                red_flag_text
            ) = calculate_red_flags(
                complete_rows
            )


            # =================================================
            # PREPARE AI HISTORY DATA
            # =================================================

            conversation_for_ai = []

            for row in complete_rows:

                conversation_for_ai.append({
                    "sender": row.get("sender"),
                    "message": row.get("message")
                })


            # =================================================
            # GENERATE COMPLETE CLINICAL HISTORY
            # =================================================

            history = generate_complete_history(
                conversation_for_ai,
                red_flag_text
            )


            # =================================================
            # SAVE CLINICAL HISTORY
            # =================================================

            history_id = save_patient_history(
                connection,
                cursor,
                patient_id,
                history
            )


            # =================================================
            # RESPONSE
            # =================================================

            return jsonify({
                "success": True,
                "reply": ai_reply,
                "session_id": current_session_id,
                "history_id": history_id,

                "red_flag": red_flag_detected,

                "red_flag_reason": "; ".join(
                    red_flag_reasons
                ),

                "red_flag_category": ", ".join(
                    red_flag_categories
                ),

                "red_flag_reasons": red_flag_reasons,

                "red_flag_categories": red_flag_categories,

                "history": history
            })


        except Exception as error:

            if connection:

                try:
                    connection.rollback()
                except Exception:
                    pass

            print(
                "AI CONVERSATION ERROR:",
                error
            )

            return jsonify({
                "success": False,
                "message": "Unable to process the message.",
                "error": str(error)
            }), 500

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # CURRENT CHAT HISTORY
    # =====================================================

    @app.route(
        "/api/chat/history"
    )
    def chat_history():

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

            current_session_id = get_current_session_id(
                connection,
                cursor,
                patient_id
            )

            rows = load_current_conversation(
                cursor,
                patient_id,
                current_session_id
            )

            return jsonify({
                "success": True,
                "session_id": current_session_id,
                "messages": rows
            })

        except Exception as error:

            print(
                "CHAT HISTORY ERROR:",
                error
            )

            return jsonify({
                "success": False,
                "message": "Unable to load chat history.",
                "error": str(error)
            }), 500

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # PREVIOUS CHAT SESSIONS
    # =====================================================

    @app.route(
        "/api/chat/sessions"
    )
    def chat_sessions():

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
                    s.id AS session_id,
                    s.created_at,
                    COUNT(c.id) AS message_count
                FROM intake_sessions s
                LEFT JOIN clinical_conversations c
                    ON c.session_id = s.id
                WHERE s.patient_id = %s
                GROUP BY
                    s.id,
                    s.created_at
                ORDER BY s.id DESC
                """,
                (
                    patient_id,
                )
            )

            rows = cursor.fetchall()

            return jsonify({
                "success": True,
                "sessions": rows
            })

        except Exception as error:

            print(
                "CHAT SESSIONS ERROR:",
                error
            )

            return jsonify({
                "success": False,
                "message": "Unable to load previous conversations.",
                "error": str(error)
            }), 500

        finally:

            safe_close(
                cursor,
                connection
            )


    # =====================================================
    # MANUAL HISTORY GENERATION
    # =====================================================

    @app.route(
        "/api/history/generate",
        methods=["POST"]
    )
    def generate_history():

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

            current_session_id = get_current_session_id(
                connection,
                cursor,
                patient_id
            )

            rows = load_current_conversation(
                cursor,
                patient_id,
                current_session_id
            )

            if not rows:

                return jsonify({
                    "success": False,
                    "message": "No conversation available."
                }), 400


            (
                red_flag_detected,
                red_flag_reasons,
                red_flag_categories,
                red_flag_text
            ) = calculate_red_flags(
                rows
            )


            conversation_data = []

            for row in rows:

                conversation_data.append({
                    "sender": row.get("sender"),
                    "message": row.get("message")
                })


            history = generate_complete_history(
                conversation_data,
                red_flag_text
            )


            history_id = save_patient_history(
                connection,
                cursor,
                patient_id,
                history
            )


            return jsonify({
                "success": True,
                "session_id": current_session_id,
                "history_id": history_id,
                "history": history,

                "red_flag": red_flag_detected,

                "red_flag_reason": "; ".join(
                    red_flag_reasons
                ),

                "red_flag_category": ", ".join(
                    red_flag_categories
                ),

                "red_flag_reasons": red_flag_reasons,

                "red_flag_categories": red_flag_categories
            })


        except Exception as error:

            if connection:

                try:
                    connection.rollback()
                except Exception:
                    pass

            print(
                "HISTORY GENERATION ERROR:",
                error
            )

            return jsonify({
                "success": False,
                "message": "Unable to generate history.",
                "error": str(error)
            }), 500

        finally:

            safe_close(
                cursor,
                connection
            )