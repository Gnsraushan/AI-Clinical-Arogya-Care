# =========================================================
# AROGYACARE - CLINICAL SERVICE
# STEP 2
# Red Flag Detection + Reason
# =========================================================

import re


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(text):
    """
    Normalize patient text for safer keyword matching.
    """

    if not text:
        return ""

    text = str(text).lower().strip()

    # Normalize common apostrophes
    text = text.replace("’", "'")

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text


# =========================================================
# RED FLAG RULES
# =========================================================

RED_FLAG_RULES = [

    {
        "category": "Chest Pain",
        "patterns": [
            "severe chest pain",
            "chest pressure",
            "pressure in chest",
            "crushing chest pain",
            "chest pain",
            "seene me dard",
            "seene mein dard",
            "seene me bahut dard",
            "seene mein bahut dard",
            "सीने में दर्द",
            "सीने में बहुत दर्द",
            "सीने में दबाव"
        ],
        "reason": "Severe chest pain or chest pressure."
    },

    {
        "category": "Breathing Difficulty",
        "patterns": [
            "can't breathe",
            "cannot breathe",
            "difficulty breathing",
            "severe difficulty breathing",
            "shortness of breath",
            "breathing problem",
            "breathing difficulty",
            "not able to breathe",
            "saans nahi aa rahi",
            "saans lene me dikkat",
            "saans lene mein dikkat",
            "saans lene me bahut dikkat",
            "saans lene mein bahut dikkat",
            "बहुत सांस फूलना",
            "सांस लेने में दिक्कत",
            "सांस लेने में बहुत दिक्कत"
        ],
        "reason": "Severe breathing difficulty or inability to breathe normally."
    },

    {
        "category": "Loss of Consciousness",
        "patterns": [
            "unconscious",
            "passed out",
            "fainted",
            "fainting",
            "lost consciousness",
            "behosh",
            "behosh ho gaya",
            "behosh ho gayi",
            "hosh nahi hai",
            "बेहोश",
            "बेहोशी",
            "होश नहीं है"
        ],
        "reason": "Loss of consciousness or fainting."
    },

    {
        "category": "Seizure",
        "patterns": [
            "seizure",
            "seizures",
            "convulsion",
            "convulsions",
            "fits",
            "fit aa raha",
            "fit aa raha hai",
            "fit aa gaya",
            "fit pad raha",
            "daura",
            "daura pada",
            "daura pada hai",
            "दौरा",
            "दौरा पड़ा",
            "दौरा पड़ रहा है"
        ],
        "reason": "Seizure, convulsion, or seizure-like episode."
    },

    {
        "category": "Severe Bleeding",
        "patterns": [
            "severe bleeding",
            "heavy bleeding",
            "bleeding heavily",
            "blood won't stop",
            "blood is not stopping",
            "uncontrolled bleeding",
            "bahut khoon",
            "bahut zyada khoon",
            "khoon nahi ruk raha",
            "khoon bahut nikal raha",
            "खून नहीं रुक रहा",
            "बहुत ज्यादा खून",
            "बहुत खून निकल रहा है"
        ],
        "reason": "Severe or uncontrolled bleeding."
    },

    {
        "category": "Stroke-like Warning Signs",
        "patterns": [
            "sudden weakness",
            "sudden paralysis",
            "one side weakness",
            "one side is weak",
            "face drooping",
            "difficulty speaking",
            "can't speak",
            "cannot speak",
            "speech difficulty",
            "bolne me dikkat",
            "bolne mein dikkat",
            "bol nahi pa raha",
            "bol nahi paa raha",
            "ek taraf kamzori",
            "ek side kamzor",
            "अचानक कमजोरी",
            "एक तरफ कमजोरी",
            "चेहरा टेढ़ा",
            "बोलने में दिक्कत"
        ],
        "reason": "Sudden weakness, facial drooping, or speech difficulty."
    },

    {
        "category": "Severe Allergic Reaction",
        "patterns": [
            "severe allergic reaction",
            "allergic reaction",
            "throat swelling",
            "face swelling",
            "tongue swelling",
            "difficulty swallowing",
            "gala suj gaya",
            "gala sooj gaya",
            "chehra suj gaya",
            "chehra sooj gaya",
            "jeebh suj gayi",
            "निगलने में दिक्कत",
            "गला सूज गया",
            "चेहरा सूज गया",
            "जीभ सूज गई"
        ],
        "reason": "Possible severe allergic reaction with swelling or swallowing difficulty."
    },

    {
        "category": "Immediate Safety Concern",
        "patterns": [
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
        "reason": "Immediate safety concern requiring urgent human support."
    },

    {
        "category": "Severe Fever With Altered Consciousness",
        "patterns": [
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
        "reason": "Severe illness with fever and altered consciousness."
    }
]


# =========================================================
# RED FLAG DETECTION
# =========================================================

def detect_red_flags(text):
    """
    Returns structured red-flag information.

    Example:

    {
        "detected": True,
        "reason": "Severe chest pain or chest pressure.",
        "category": "Chest Pain"
    }
    """

    normalized = normalize_text(text)

    if not normalized:
        return {
            "detected": False,
            "reason": None,
            "category": None
        }

    for rule in RED_FLAG_RULES:

        for pattern in rule["patterns"]:

            pattern_normalized = normalize_text(pattern)

            if pattern_normalized in normalized:

                return {
                    "detected": True,
                    "reason": rule["reason"],
                    "category": rule["category"]
                }

    return {
        "detected": False,
        "reason": None,
        "category": None
    }


# =========================================================
# SIMPLE COMPATIBILITY FUNCTION
# =========================================================

def check_red_flags(text):
    """
    Backward-compatible function.

    Existing code can continue using:

        flag, reason = check_red_flags(message)

    """

    result = detect_red_flags(text)

    return (
        result["detected"],
        result["reason"]
    )


# =========================================================
# USER-FACING WARNING
# =========================================================

def get_red_flag_warning(text):
    """
    Creates a clear warning for patient/doctor UI.
    """

    result = detect_red_flags(text)

    if not result["detected"]:
        return None

    return {
        "title": "RED FLAG DETECTED",
        "reason": result["reason"],
        "category": result["category"],
        "action": (
            "Please seek urgent medical attention. "
            "This is an emergency warning, not a diagnosis."
        )
    }