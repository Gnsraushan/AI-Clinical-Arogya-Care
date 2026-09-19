import os

from dotenv import load_dotenv
from groq import Groq


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is missing. Please check your .env file."
    )


# =========================================================
# GROQ CLIENT
# =========================================================

client = Groq(
    api_key=GROQ_API_KEY
)


# =========================================================
# MODEL
# =========================================================

GROQ_MODEL = "openai/gpt-oss-120b"


# =========================================================
# GENERAL AI CHAT
# =========================================================

def generate_intake_reply(conversation_messages):
    """
    Generate the next reply for the patient's
    clinical intake conversation.
    """

    system_prompt = """
You are ArogyaCare's clinical intake assistant.

Your job is ONLY to collect and organize patient information
for a doctor.

You are NOT a doctor.

You must NOT:
- diagnose diseases
- prescribe medicines
- recommend treatment
- replace a doctor
- claim certainty about a medical condition
- invent patient information

Rules:

1. Ask ONE relevant question at a time.

2. Use simple English, Hindi, or Hinglish depending
   on the patient's language.

3. Focus mainly on the patient's CURRENT problem.

4. Ask about:
   - current complaint
   - duration
   - current symptoms
   - severity when relevant
   - previous medical history
   - previous surgeries when relevant
   - current medicines
   - allergies

5. Do not repeatedly ask information that the patient
   has already clearly provided.

6. Keep responses short and easy to understand.

7. If the patient describes a potentially serious symptom,
   tell them that urgent medical attention may be required.

8. A red flag is a warning signal, NOT a diagnosis.

9. Clearly separate CURRENT information from PAST history.

10. If a patient says they had a disease in the past,
    do not treat it as a current disease unless the patient
    clearly says it is currently active or ongoing.

11. Never invent symptoms, diseases, medicines, allergies,
    duration, test results, or medical history.

12. When the intake is reasonably complete, tell the patient
    that the information has been recorded for doctor review.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    if conversation_messages:

        for message in conversation_messages:

            if not isinstance(message, dict):
                continue

            role = message.get("role")
            content = message.get("content")

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
        completion
        .choices[0]
        .message
        .content
        .strip()
    )

    if not reply:
        reply = (
            "Thank you. Please tell me a little "
            "more about your current problem."
        )

    return reply


# =========================================================
# STRUCTURED CLINICAL HISTORY
# =========================================================

def generate_structured_history(
    conversation_text,
    red_flag_text="No potential red flags detected."
):
    """
    Convert the patient's intake conversation into
    a structured doctor-readable clinical history.
    """

    system_prompt = """
You are ArogyaCare's clinical-intake summarization assistant.

Convert the patient's intake conversation into a concise,
factual, doctor-readable structured history.

IMPORTANT:

- Do NOT diagnose.
- Do NOT prescribe treatment.
- Do NOT invent symptoms.
- Do NOT invent diseases.
- Do NOT infer a disease from symptoms.
- Do NOT invent medicines.
- Do NOT invent allergies.
- Do NOT invent duration.
- Do NOT invent test results.
- Use ONLY information explicitly present in the
  patient conversation.
- AI questions are NOT patient facts.
- If information is not clearly stated, write:
  "Not clearly stated."

CURRENT VS PAST INFORMATION:

CURRENT COMPLAINT:
Only the patient's current reason for seeking care.

CURRENT SYMPTOMS:
Only symptoms the patient currently reports.

DURATION:
Only the duration explicitly stated for the
current complaint.

PAST MEDICAL HISTORY:
Previously known diseases, surgeries, conditions,
or relevant medical history explicitly reported
by the patient.

A past disease MUST remain in PAST MEDICAL HISTORY
unless the patient explicitly says it is currently
active or ongoing.

CURRENT MEDICATIONS:
Only medicines the patient explicitly says they
are currently taking.

ALLERGIES:
Only allergies explicitly reported by the patient.

RED FLAGS:
Only warning signals detected by the system.
Red flags are warning signals and NOT diagnoses.

SUMMARY:
A short factual summary using only explicitly
reported patient information.

Example:

Patient says:
"I had asthma when I was a child."

Correct:

PAST MEDICAL HISTORY:
Childhood history of asthma.

Incorrect:

CURRENT COMPLAINT:
Asthma.

Another example:

Patient says:
"I had diabetes five years ago but I no longer
take medicine."

Correct:

PAST MEDICAL HISTORY:
History of diabetes, reported as past.

CURRENT MEDICATIONS:
Not clearly stated.

Do NOT assume that a past disease is currently active.

Return EXACTLY these sections:

CURRENT COMPLAINT:
CURRENT SYMPTOMS:
DURATION:
PAST MEDICAL HISTORY:
CURRENT MEDICATIONS:
ALLERGIES:
RED FLAGS:
SUMMARY:

Keep the report concise, factual, and doctor-readable.
"""

    user_prompt = f"""
PATIENT INTAKE CONVERSATION:

{conversation_text}


SYSTEM RED-FLAG CHECK:

{red_flag_text}


Create the structured clinical intake using the
exact section format requested above.

Remember:

- Use only information explicitly provided by the patient.
- Keep current and past information separate.
- Do not diagnose.
- Do not invent information.
- Use "Not clearly stated." where necessary.
"""

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
        completion
        .choices[0]
        .message
        .content
        .strip()
    )

    if not history:
        raise ValueError(
            "AI returned an empty clinical history."
        )

    return history


# =========================================================
# TEXT CLEANING
# =========================================================

def clean_text(value):

    if value is None:
        return "Not clearly stated."

    value = str(value).strip()

    if not value:
        return "Not clearly stated."

    return value


# =========================================================
# PARSE STRUCTURED HISTORY
# =========================================================

def parse_history_text(text):
    """
    Convert the AI structured report into a dictionary.
    """

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
    """
    Convert database conversation rows into text
    for the history-generation AI.
    """

    if not conversations:
        return ""

    lines = []

    for row in conversations:

        if not isinstance(row, dict):
            continue

        sender = (
            row.get("sender") or ""
        ).lower().strip()

        message = clean_text(
            row.get("message")
        )

        if message == "Not clearly stated.":
            continue

        if sender == "patient":
            label = "PATIENT"

        elif sender in ["ai", "assistant"]:
            label = "AI ASSISTANT"

        else:
            label = "ASSISTANT"

        lines.append(
            f"{label}: {message}"
        )

    return "\n".join(lines)


# =========================================================
# COMPLETE HISTORY
# =========================================================

def generate_complete_history(
    conversations,
    red_flag_text="No potential red flags detected."
):
    """
    Generate and parse the complete structured
    clinical history.
    """

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

    history = parse_history_text(
        raw_history
    )

    return history