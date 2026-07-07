from app.core.auth import keycloak
import json

try:
    print(dir(keycloak))
except Exception as e:
    print("Error:", e)
