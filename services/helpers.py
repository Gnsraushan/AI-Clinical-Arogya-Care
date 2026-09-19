from flask import session


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


ALLOWED_EXTENSIONS = {
    "pdf",
    "jpg",
    "jpeg",
    "png"
}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def check_red_flags(message):
    if not message:
        return False, None

    text = message.lower().strip()

    red_flag_patterns = [

        (
            [
                "severe chest pain",
                "chest pain",
                "chest pressure",
                "pressure in chest",
                "seene me dard",
                "seene mein dard",
                "सीने में दर्द",
                "सीने में बहुत दर्द",
                "seene me bahut dard"
            ],
            "Possible emergency symptom: chest pain or chest pressure."
        ),

        (
            [
                "can't breathe",
                "cannot breathe",
                "difficulty breathing",
                "severe difficulty breathing",
                "shortness of breath",
                "breathing problem",
                "breathing difficulty",
                "saans nahi aa rahi",
                "saans lene me dikkat",
                "saans lene mein dikkat",
                "बहुत सांस फूलना",
                "सांस लेने में बहुत दिक्कत"
            ],
            "Possible emergency symptom: severe breathing difficulty."
        ),

        (
            [
                "unconscious",
                "passed out",
                "fainted",
                "fainting",
                "lost consciousness",
                "behosh",
                "behosh ho gaya",
                "behosh ho gayi",
                "बेहोश",
                "बेहोशी"
            ],
            "Possible emergency symptom: loss of consciousness."
        ),

        (
            [
                "seizure",
                "seizures",
                "convulsion",
                "fits",
                "fit aa raha",
                "fit aa gaya",
                "daura",
                "daura pada",
                "दौरा",
                "दौरा पड़ा"
            ],
            "Possible emergency symptom: seizure or convulsion."
        ),

        (
            [
                "severe bleeding",
                "heavy bleeding",
                "bleeding heavily",
                "blood won't stop",
                "blood is not stopping",
                "bahut khoon",
                "khoon nahi ruk raha",
                "khoon bahut nikal raha",
                "खून नहीं रुक रहा",
                "बहुत ज्यादा खून"
            ],
            "Possible emergency symptom: severe or uncontrolled bleeding."
        ),

        (
            [
                "sudden weakness",
                "sudden paralysis",
                "one side weakness",
                "one side is weak",
                "face drooping",
                "difficulty speaking",
                "can't speak",
                "cannot speak",
                "bolne me dikkat",
                "bol nahi pa raha",
                "bol nahi paa raha",
                "ek taraf kamzori",
                "एक तरफ कमजोरी",
                "अचानक बोलने में दिक्कत",
                "चेहरा टेढ़ा"
            ],
            "Possible emergency symptom: sudden weakness, paralysis, or speech difficulty."
        ),

        (
            [
                "severe allergic reaction",
                "allergic reaction",
                "throat swelling",
                "face swelling",
                "tongue swelling",
                "difficulty swallowing",
                "gala suj gaya",
                "gala sooj gaya",
                "chehra suj gaya",
                "jeebh suj gayi",
                "निगलने में दिक्कत",
                "गला सूज गया"
            ],
            "Possible emergency symptom: severe allergic reaction or swelling."
        ),

        (
            [
                "want to kill myself",
                "kill myself",
                "suicide",
                "suicidal",
                "end my life",
                "marna chahta hoon",
                "marna chahti hoon",
                "khud ko maar",
                "khud ko marna",
                "suicide karna",
                "आत्महत्या",
                "खुद को मारना"
            ],
            "Immediate safety concern detected. Urgent human support is recommended."
        ),

        (
            [
                "very high fever and confusion",
                "high fever and unconscious",
                "fever with confusion",
                "fever and not responding",
                "bukhar ke saath behoshi",
                "bukhar aur behoshi",
                "tez bukhar aur confusion",
                "तेज बुखार और बेहोशी",
                "बुखार के साथ बेहोशी"
            ],
            "Possible emergency symptom: severe illness with fever and altered consciousness."
        )
    ]

    for patterns, reason in red_flag_patterns:
        for pattern in patterns:
            if pattern in text:
                return True, reason

    return False, None