from app.core.security import hash_password, verify_password


def test_password_hash_round_trip() -> None:
    hashed = hash_password("correct-horse-battery")
    assert verify_password("correct-horse-battery", hashed)
    assert not verify_password("wrong", hashed)

