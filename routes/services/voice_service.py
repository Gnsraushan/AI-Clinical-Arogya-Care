# =========================================================
# AROGYACARE VOICE SERVICE
# =========================================================
#
# Voice recognition is handled by the browser using:
# SpeechRecognition / webkitSpeechRecognition
#
# This service contains backend-side helpers and
# configuration only.
# =========================================================


SUPPORTED_LANGUAGES = {
    "english": "en-IN",
    "hindi": "hi-IN",
    "hinglish": "en-IN"
}


def get_voice_language(language="english"):
    """
    Return the browser Speech Recognition language code.
    """

    if not language:
        language = "english"

    language = str(
        language
    ).lower().strip()

    return SUPPORTED_LANGUAGES.get(
        language,
        "en-IN"
    )


def get_supported_voice_languages():
    """
    Return supported voice languages.
    """

    return SUPPORTED_LANGUAGES.copy()


def normalize_voice_text(text):
    """
    Basic cleanup for speech-to-text output.
    """

    if not text:
        return ""

    text = str(text).strip()

    # Remove unnecessary repeated spaces
    text = " ".join(
        text.split()
    )

    return text