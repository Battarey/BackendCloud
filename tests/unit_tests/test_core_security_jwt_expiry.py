import pytest
from app.core import security
from datetime import timedelta
import time

def test_jwt_token_expiry():
    data = {"sub": "user_id"}
    token = security.create_access_token(data, expires_delta=timedelta(seconds=1))
    from jose import jwt, ExpiredSignatureError
    # Let's decode right away
    decoded = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
    assert decoded["sub"] == "user_id"
    # Waiting for the deadline to expire
    time.sleep(2)
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
