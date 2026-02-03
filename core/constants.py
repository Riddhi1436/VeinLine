from __future__ import annotations


class BloodGroup:
    """
    Canonical blood group values used across the platform.
    Stored as short strings for portability.
    """

    O_POS = "O+"
    O_NEG = "O-"
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"

    CHOICES = (
        (O_POS, "O+"),
        (O_NEG, "O-"),
        (A_POS, "A+"),
        (A_NEG, "A-"),
        (B_POS, "B+"),
        (B_NEG, "B-"),
        (AB_POS, "AB+"),
        (AB_NEG, "AB-"),
    )


# Supported regions: Delhi NCR and Uttar Pradesh (used for sample data and UI hints)
DELHI_NCR_CITIES = [
    "Delhi", "Noida", "Gurugram", "Faridabad", "Ghaziabad", "Greater Noida",
]
UTTAR_PRADESH_CITIES = [
    "Lucknow", "Kanpur", "Agra", "Varanasi", "Prayagraj", "Meerut",
]
SUPPORTED_CITIES = DELHI_NCR_CITIES + UTTAR_PRADESH_CITIES


