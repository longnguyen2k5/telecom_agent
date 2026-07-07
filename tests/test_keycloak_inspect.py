from app.core.auth import keycloak
import json

try:
    token = keycloak.user_login(username="long_nguyen", password="12345678")
    print(dir(token))
    print("access_token:", getattr(token, "access_token", None))
    print("token_type:", getattr(token, "token_type", None))
    try:
        print("dict:", token.dict())
    except:
        pass
    try:
        print("model_dump:", token.model_dump())
    except:
        pass
except Exception as e:
    print("Error:", e)
