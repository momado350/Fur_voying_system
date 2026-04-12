from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(pw: str) -> str:
    return generate_password_hash(pw)

def verify_password(hash_: str, pw: str) -> bool:
    return check_password_hash(hash_, pw)
