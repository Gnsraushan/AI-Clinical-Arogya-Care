import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is missing. Please check your .env file."
    )


client = Groq(
    api_key=GROQ_API_KEY
)


GROQ_MODEL = "openai/gpt-oss-120b"


# =========================================================
# AI CONVERSATION
# =========================================================

def generate_intake_reply(conversation_messages):

    system_prompt = """
You are ArogyaCare's clinical intake assistant.

Your ONLY job is to collect information from the patient
and prepare it for doctor review.

You are NOT a doctor.

NEVER:
- diagnose diseases
- prescribe medicines
- recommend treatment
- claim certainty
- invent patient information

RULES:

1. Ask ONE useful question at a time.

2. Use simple English, Hindi or Hinglish according to
   the patient's language.

3. Focus on the CURRENT complaint.

4. Collect:
   - current complaint
   - duration
   - current symptoms
   - severity when relevant
   - past medical history
   - previous surgeries
   - current medicines
   - allergies

5. Do not ask again for information the patient already gave.

6. Keep replies short.

7. If the patient reports a potentially serious symptom,
   advise seeking urgent medical attention.

8. A red flag is only a WARNING SIGNAL, not a diagnosis.

9. Keep CURRENT information separate from PAST history.

10. Never convert a past disease into a current disease.

11. Never invent symptoms, diseases, medicines, allergies,
    duration or test results.

12. When enough information has been collected, say that
    the information has been recorded for doctor review.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    if conversation_messages:
        for item in conversation_messages:

            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = item.get("content")

            if role not in ["user", "assistant"]:
                continue

            if not content:
                continue

            messages.append(
                {
                    "role": role,
                    "content": str(content).strip()
                }
            )

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=500
    )

    reply = (
        completion.choices[0].message.content or ""
    ).strip()

    if not reply:
        reply = (
            "Thank you. Please tell me a little more "
            "about your current problem."
        )

    return reply


# =========================================================
# STRUCTURED CLINICAL REPORT
# =========================================================

def generate_structured_history(
    conversation_text,
    red_flag_text="No potential red flags detected."
):

    system_prompt = """
You are ArogyaCare's clinical intake summarization assistant.

Convert the patient intake conversation into a concise,
factual, doctor-readable clinical intake report.

IMPORTANT:

- Do NOT diagnose.
- Do NOT prescribe treatment.
- Do NOT invent information.
- Use ONLY information explicitly stated by the patient.
- AI questions are NOT patient facts.
- Never infer a disease from symptoms.
- Never invent medicines.
- Never invent allergies.
- Never invent duration.
- Never invent test results.

CURRENT VS PAST:

CURRENT COMPLAINT:
Only the patient's current reason for seeking care.

CURRENT SYMPTOMS:
Only symptoms the patient currently reports.

DURATION:
Only duration explicitly reported for the current complaint.

PAST MEDICAL HISTORY:
Only previously reported diseases, surgeries or conditions.

If the patient says something happened in the past,
keep it in PAST MEDICAL HISTORY.

CURRENT MEDICATIONS:
Only medicines the patient says they currently take.

ALLERGIES:
Only allergies explicitly reported.

RED FLAGS:
Only warning signals detected by the system.

SUMMARY:
Short factual summary.

If information is missing write:
Not clearly stated.

Return EXACTLY:

CURRENT COMPLAINT:
CURRENT SYMPTOMS:
DURATION:
PAST MEDICAL HISTORY:
CURRENT MEDICATIONS:
ALLERGIES:
RED FLAGS:
SUMMARY:
"""

    user_prompt = (
        "PATIENT INTAKE:\n\n"
        + str(conversation_text)
        + "\n\n"
        + "SYSTEM RED-FLAG CHECK:\n\n"
        + str(red_flag_text)
        + "\n\n"
        + "Create the doctor-readable report.\n\n"
        + "Use only patient-provided facts.\n"
        + "Do not diagnose.\n"
        + "Do not invent information.\n"
        + "Keep current and past information separate."
    )

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.1,
        max_tokens=1000
    )

    history = (
        completion.choices[0].message.content or ""
    ).strip()

    if not history:
        raise ValueError(
            "AI returned an empty clinical history."
        )

    return history


# =========================================================
# PARSE HISTORY
# =========================================================

def parse_history_text(text):

    fields = {
        "main_problem": "Not clearly stated.",
        "duration": "Not clearly stated.",
        "symptoms": "Not clearly stated.",
        "medical_history": "Not clearly stated.",
        "medicines": "Not clearly stated.",
        "allergies": "Not clearly stated.",
        "red_flags": "Not clearly stated.",
        "summary": "Not clearly stated."
    }

    if not text:
        return fields

    field_map = {
        "CURRENT COMPLAINT": "main_problem",
        "CURRENT SYMPTOMS": "symptoms",
        "DURATION": "duration",
        "PAST MEDICAL HISTORY": "medical_history",
        "CURRENT MEDICATIONS": "medicines",
        "ALLERGIES": "allergies",
        "RED FLAGS": "red_flags",
        "SUMMARY": "summary"
    }

    current_field = None

    for raw_line in str(text).splitlines():

        line = raw_line.strip()

        if not line:
            continue

        upper_line = line.upper()

        matched = False

        for heading, key in field_map.items():

            prefix = heading + ":"

            if upper_line.startswith(prefix):

                current_field = key

                value = line[len(prefix):].strip()

                if value:
                    fields[key] = value

                matched = True
                break

        if matched:
            continue

        if current_field:

            existing = fields[current_field]

            if existing == "Not clearly stated.":
                fields[current_field] = line
            else:
                fields[current_field] += " " + line

    return fields


# =========================================================
# BUILD CONVERSATION TEXT
# =========================================================

def build_conversation_text(conversations):

    if not conversations:
        return ""

    lines = []

    for row in conversations:

        if not isinstance(row, dict):
            continue

        sender = str(
            row.get("sender") or ""
        ).lower().strip()

        message = row.get("message")

        if not message:
            continue

        message = str(message).strip()

        if not message:
            continue

        if sender == "patient":
            label = "PATIENT"
        elif sender in ["ai", "assistant"]:
            label = "AI ASSISTANT"
        else:
            label = "ASSISTANT"

        lines.append(
            label + ": " + message
        )

    return "\n".join(lines)


# =========================================================
# COMPLETE HISTORY
# =========================================================

def generate_complete_history(
    conversations,
    red_flag_text="No potential red flags detected."
):

    conversation_text = build_conversation_text(
        conversations
    )

    if not conversation_text:

        return {
            "main_problem": "Not clearly stated.",
            "duration": "Not clearly stated.",
            "symptoms": "Not clearly stated.",
            "medical_history": "Not clearly stated.",
            "medicines": "Not clearly stated.",
            "allergies": "Not clearly stated.",
            "red_flags": "Not clearly stated.",
            "summary": "Not clearly stated."
        }

    raw_history = generate_structured_history(
        conversation_text,
        red_flag_text
    )

    return parse_history_text(
        raw_history
    )

