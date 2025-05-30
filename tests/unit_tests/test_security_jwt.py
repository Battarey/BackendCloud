from app.core import security
from datetime import timedelta

def test_jwt_token_encode_decode():
    data = {"sub": "user_id"}
    token = security.create_access_token(data, expires_delta=timedelta(minutes=5))
    assert isinstance(token, str)
    # Decoding the token manually
    from jose import jwt
    decoded = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
    assert decoded["sub"] == "user_id"
