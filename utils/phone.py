import re

def normalize_phone(raw: str) -> str:
    """Normalize phone numbers to reduce duplicates.

    Rules:
    - Strip spaces/dashes/parentheses etc.
    - Keep digits.
    - If user enters 10 digits, assume US and prefix +1.
    - If user enters 11 digits starting with 1, prefix +.
    - If user enters a number with leading '+', keep '+' and digits only.
    """
    if not raw:
        return ""

    s = raw.strip()

    # keep digits and leading +
    s = re.sub(r"[^\d+]", "", s)

    if s.startswith("+"):
        # remove any extra '+' beyond the first
        s = "+" + re.sub(r"\D", "", s[1:])
        return s if s != "+" else ""

    digits = re.sub(r"\D", "", s)

    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits

    return "+" + digits if digits else ""