# =========================================================
# AROGYACARE OCR SERVICE
# =========================================================
#
# This module keeps OCR-related logic separate from Flask
# routes.
#
# Actual OCR processing can be connected later without
# changing the document upload routes.
# =========================================================


ALLOWED_OCR_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "pdf"
}


def is_ocr_supported(filename):
    """
    Check whether the uploaded document type can be
    considered for OCR processing.
    """

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_OCR_EXTENSIONS


def get_file_extension(filename):
    """
    Return the lowercase extension of a file.
    """

    if not filename or "." not in filename:
        return ""

    return filename.rsplit(
        ".",
        1
    )[1].lower()


def prepare_ocr_text(text):
    """
    Basic cleanup for OCR output.
    """

    if not text:
        return ""

    text = str(
        text
    ).strip()

    # Remove excessive blank spaces
    lines = []

    for line in text.splitlines():

        line = " ".join(
            line.split()
        )

        if line:
            lines.append(line)

    return "\n".join(
        lines
    )


def get_ocr_status(filename):
    """
    Return a simple OCR status for a document.
    """

    if not filename:

        return {
            "supported": False,
            "extension": "",
            "message": "No file provided."
        }

    extension = get_file_extension(
        filename
    )

    if extension in ALLOWED_OCR_EXTENSIONS:

        return {
            "supported": True,
            "extension": extension,
            "message": "Document is eligible for OCR."
        }

    return {
        "supported": False,
        "extension": extension,
        "message": "This document type is not supported for OCR."
    }