from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()


def verify_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    return _password_hash.verify_and_update(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return _password_hash.hash(password)
