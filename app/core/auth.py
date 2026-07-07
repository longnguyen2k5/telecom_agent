from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_keycloak import FastAPIKeycloak
from app.core.config import settings


keycloak = FastAPIKeycloak(
    server_url=settings.keycloak_url,
    client_id=settings.client_id,
    client_secret=settings.client_secret,
    admin_client_id=settings.admin_client_id,
    admin_client_secret=settings.admin_client_secret,
    realm=settings.realm_name,
    callback_uri=settings.keycloak_url,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        user_data = keycloak._decode_token(token)
        if not user_data:
            raise Exception()
        # Thêm id từ sub claim cho các API dùng user["id"]
        user_data["id"] = user_data.get("sub")
        return user_data
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
