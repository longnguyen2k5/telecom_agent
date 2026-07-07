from app.core.auth import keycloak

try:
    token = keycloak.user_login(username="long_nguyen", password="12345678")
    print("Token object:", type(token))
    print("Token content:", token)
except Exception as e:
    print("Error:", e)
