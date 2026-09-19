# =========================================================
# AROGYACARE - AI ROUTES
# STEP 4
# Conversation + Structured History
# =========================================================

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from services.database import (
    get_db_connection,
    safe_close
)

from services.helpers import (
    patient_logged_in
)

from services.clinical_service import (
    detect_red_flags
)

from services.ai_service import (
    generate_intake_reply,
    generate_complete_history
)


# =========================================================
# REGISTER AI ROUTES
# =========================================================

def register_ai_routes(app):

    # =====================================================
    # AI CONVERSATION PAGE
    # =====================================================

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

            patient_id = session.get("user_id")

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            # ---------------------------------------------
            # PATIENT
            # ---------------------------------------------

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

                session.clear()

                return redirect(
                    url_for(
                        "login_page",
                        role="patient"
                    )
                )

            # ---------------------------------------------
            # CONVERSATION
            # ---------------------------------------------

            cursor.execute(
                """
                SELECT
                    id,
                    patient_id,
                    sender,
                    message,
                    created_at
                FROM clinical_conversations
                WHERE patient_id = %s
                ORDER BY created_at ASC
                """,
                (patient_id,)
            )

            conversations = cursor.fetchall()

            # ---------------------------------------------
            # LATEST STRUCTURED HISTORY
            # ---------------------------------------------

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
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (patient_id,)
            )

            latest_history = cursor.fetchone()

            # ---------------------------------------------
            # RED FLAG CHECK
            # ---------------------------------------------

            red_flag_reason = None
            red_flag_category = None

            for row in conversations:

                if row.get("sender") != "patient":
                    continue

                result = detect_red_flags(
                    row.get("message", "")
                )

                if result["detected"]:

                    red_flag_reason = result["reason"]
                    red_flag_category = result["category"]

                    break

            return render_template(
                "ai_conversation.html",

                patient=patient,

                conversations=conversations,

                latest_history=latest_history,

                patient_history=latest_history,

                history=latest_history,

                summary=(
                    latest_history["summary"]
                    if latest_history
                    else None
                ),

                red_flag_reason=red_flag_reason,

                red_flags=(
                    red_flag_reason
                    if red_flag_reason
                    else None
                ),

                red_flag_category=red_flag_category,

                allow_message_input=True,

                case_status="active",

                intake_status="active",

                user_name=session.get(
                    "full_name",
                    "Patient"
                )
            )

        except Exception as e:

            print(
                "AI CONVERSATION PAGE ERROR:",
                e
            )

            return (
                "Unable to load AI conversation.",
                500
            )

        finally:

            safe_close(
                cursor=cursor,
                connection=connection
            )


    # =====================================================
    # PROCESS AI MESSAGE
    # =====================================================

    def process_ai_message(message):

        if not patient_logged_in():

            return {
                "success": False,
                "error": "Unauthorized"
            }

        message = (
            message or ""
        ).strip()

        if not message:

            return {
                "success": False,
                "error": "Message cannot be empty."
            }

        patient_id = session.get(
            "user_id"
        )

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            # ---------------------------------------------
            # RED FLAG CHECK
            # ---------------------------------------------

            red_flag_result = detect_red_flags(
                message
            )

            red_flag_detected = (
                red_flag_result["detected"]
            )

            red_flag_reason = (
                red_flag_result["reason"]
            )

            red_flag_category = (
                red_flag_result["category"]
            )

            # ---------------------------------------------
            # SAVE PATIENT MESSAGE
            # ---------------------------------------------

            cursor.execute(
                """
                INSERT INTO clinical_conversations
                (
                    patient_id,
                    sender,
                    message
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    patient_id,
                    "patient",
                    message
                )
            )

            connection.commit()

            # ---------------------------------------------
            # LOAD CURRENT CONVERSATION
            # ---------------------------------------------

            cursor.execute(
                """
                SELECT
                    sender,
                    message
                FROM clinical_conversations
                WHERE patient_id = %s
                ORDER BY created_at ASC
                LIMIT 100
                """,
                (patient_id,)
            )

            previous_messages = (
                cursor.fetchall()
            )

            # ---------------------------------------------
            # PREPARE AI MESSAGES
            # ---------------------------------------------

            ai_messages = []

            for row in previous_messages:

                sender = (
                    row.get("sender")
                    or ""
                ).lower()

                content = (
                    row.get("message")
                    or ""
                ).strip()

                if not content:
                    continue

                if sender == "patient":

                    ai_messages.append(
                        {
                            "role": "user",
                            "content": content
                        }
                    )

                elif sender in [
                    "ai",
                    "assistant"
                ]:

                    ai_messages.append(
                        {
                            "role": "assistant",
                            "content": content
                        }
                    )

            # ---------------------------------------------
            # GENERATE AI REPLY
            # ---------------------------------------------

            ai_reply = generate_intake_reply(
                ai_messages
            )

            # ---------------------------------------------
            # SAVE AI REPLY
            # ---------------------------------------------

            cursor.execute(
                """
                INSERT INTO clinical_conversations
                (
                    patient_id,
                    sender,
                    message
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    patient_id,
                    "ai",
                    ai_reply
                )
            )

            connection.commit()

            # ---------------------------------------------
            # LOAD COMPLETE CONVERSATION
            # ---------------------------------------------

            cursor.execute(
                """
                SELECT
                    sender,
                    message,
                    created_at
                FROM clinical_conversations
                WHERE patient_id = %s
                ORDER BY created_at ASC
                """,
                (patient_id,)
            )

            all_conversations = (
                cursor.fetchall()
            )

            # ---------------------------------------------
            # COLLECT ALL RED FLAGS
            # ---------------------------------------------

            red_flag_reasons = []

            for row in all_conversations:

                if row.get("sender") != "patient":
                    continue

                result = detect_red_flags(
                    row.get("message", "")
                )

                if result["detected"]:

                    reason = result["reason"]

                    if reason not in red_flag_reasons:

                        red_flag_reasons.append(
                            reason
                        )

            if red_flag_reasons:

                red_flag_text = "\n".join(
                    f"- {reason}"
                    for reason in red_flag_reasons
                )

            else:

                red_flag_text = (
                    "No potential red flags detected."
                )

            # ---------------------------------------------
            # AUTOMATIC STRUCTURED REPORT
            # ---------------------------------------------

            history = generate_complete_history(
                all_conversations,
                red_flag_text
            )

            # ---------------------------------------------
            # SAVE STRUCTURED HISTORY
            # ---------------------------------------------

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

                    history.get(
                        "main_problem",
                        "Not clearly stated."
                    ),

                    history.get(
                        "duration",
                        "Not clearly stated."
                    ),

                    history.get(
                        "symptoms",
                        "Not clearly stated."
                    ),

                    history.get(
                        "medical_history",
                        "Not clearly stated."
                    ),

                    history.get(
                        "medicines",
                        "Not clearly stated."
                    ),

                    history.get(
                        "allergies",
                        "Not clearly stated."
                    ),

                    history.get(
                        "summary",
                        "Not clearly stated."
                    )
                )
            )

            connection.commit()

            history["red_flags"] = (
                "\n".join(red_flag_reasons)
                if red_flag_reasons
                else "No potential red flags detected."
            )

            return {
                "success": True,

                "reply": ai_reply,

                "red_flag": red_flag_detected,

                "red_flag_reason": red_flag_reason,

                "red_flag_category": red_flag_category,

                "history": history
            }

        except Exception as e:

            print(
                "AI MESSAGE ERROR:",
                e
            )

            return {
                "success": False,
                "error": (
                    "AI service is temporarily unavailable."
                )
            }

        finally:

            safe_close(
                cursor=cursor,
                connection=connection
            )


    # =====================================================
    # FORM MESSAGE
    # =====================================================

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

        result = process_ai_message(
            message
        )

        if not result.get("success"):

            return redirect(
                url_for(
                    "ai_conversation"
                )
            )

        return redirect(
            url_for(
                "ai_conversation"
            )
        )


    # =====================================================
    # CHAT API
    # =====================================================

    @app.route(
        "/api/chat",
        methods=["POST"]
    )
    def chat_api():

        if not patient_logged_in():

            return jsonify(
                {
                    "success": False,
                    "error": "Unauthorized"
                }
            ), 401

        data = request.get_json(
            silent=True
        ) or {}

        message = data.get(
            "message",
            ""
        )

        result = process_ai_message(
            message
        )

        if not result.get("success"):

            return jsonify(
                result
            ), 400

        return jsonify(
            result
        )


    # =====================================================
    # CHAT HISTORY API
    # =====================================================

    @app.route(
        "/api/chat/history",
        methods=["GET"]
    )
    def chat_history_api():

        if not patient_logged_in():

            return jsonify(
                {
                    "success": False,
                    "error": "Unauthorized"
                }
            ), 401

        patient_id = session.get(
            "user_id"
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
                    patient_id,
                    sender,
                    message,
                    created_at
                FROM clinical_conversations
                WHERE patient_id = %s
                ORDER BY created_at ASC
                """,
                (patient_id,)
            )

            conversations = (
                cursor.fetchall()
            )

            return jsonify(
                {
                    "success": True,
                    "conversations": conversations
                }
            )

        except Exception as e:

            print(
                "CHAT HISTORY ERROR:",
                e
            )

            return jsonify(
                {
                    "success": False,
                    "error": (
                        "Unable to load chat history."
                    )
                }
            ), 500

        finally:

            safe_close(
                cursor=cursor,
                connection=connection
            )


    # =====================================================
    # MANUAL REPORT API
    # =====================================================

    @app.route(
        "/api/history/generate",
        methods=["POST"]
    )
    def generate_history():

        if not patient_logged_in():

            return jsonify(
                {
                    "success": False,
                    "error": "Unauthorized"
                }
            ), 401

        patient_id = session.get(
            "user_id"
        )

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            # ---------------------------------------------
            # LOAD CONVERSATION
            # ---------------------------------------------

            cursor.execute(
                """
                SELECT
                    sender,
                    message,
                    created_at
                FROM clinical_conversations
                WHERE patient_id = %s
                ORDER BY created_at ASC
                """,
                (patient_id,)
            )

            conversations = (
                cursor.fetchall()
            )

            if not conversations:

                return jsonify(
                    {
                        "success": False,
                        "error": (
                            "No conversation found."
                        )
                    }
                ), 400

            # ---------------------------------------------
            # RED FLAGS
            # ---------------------------------------------

            red_flag_reasons = []

            for row in conversations:

                if row.get("sender") != "patient":
                    continue

                result = detect_red_flags(
                    row.get("message", "")
                )

                if result["detected"]:

                    reason = result["reason"]

                    if reason not in red_flag_reasons:

                        red_flag_reasons.append(
                            reason
                        )

            red_flag_text = (
                "\n".join(
                    f"- {reason}"
                    for reason in red_flag_reasons
                )
                if red_flag_reasons
                else
                "No potential red flags detected."
            )

            # ---------------------------------------------
            # GENERATE REPORT
            # ---------------------------------------------

            history = generate_complete_history(
                conversations,
                red_flag_text
            )

            # ---------------------------------------------
            # SAVE REPORT
            # ---------------------------------------------

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

                    history.get(
                        "main_problem",
                        "Not clearly stated."
                    ),

                    history.get(
                        "duration",
                        "Not clearly stated."
                    ),

                    history.get(
                        "symptoms",
                        "Not clearly stated."
                    ),

                    history.get(
                        "medical_history",
                        "Not clearly stated."
                    ),

                    history.get(
                        "medicines",
                        "Not clearly stated."
                    ),

                    history.get(
                        "allergies",
                        "Not clearly stated."
                    ),

                    history.get(
                        "summary",
                        "Not clearly stated."
                    )
                )
            )

            connection.commit()

            history["red_flags"] = (
                "\n".join(red_flag_reasons)
                if red_flag_reasons
                else "No potential red flags detected."
            )

            return jsonify(
                {
                    "success": True,
                    "history": history
                }
            )

        except Exception as e:

            print(
                "HISTORY GENERATION ERROR:",
                e
            )

            return jsonify(
                {
                    "success": False,
                    "error": (
                        "Unable to generate clinical history."
                    )
                }
            ), 500

        finally:

            safe_close(
                cursor=cursor,
                connection=connection
            )