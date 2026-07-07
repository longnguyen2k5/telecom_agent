from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth_dto import TokenResponse
from app.core.auth import keycloak

router = APIRouter()

@router.post("/")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        token = keycloak.user_login(
            username=form_data.username, 
            password=form_data.password
        )
        return TokenResponse(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            id_token=token.id_token
        )
        
    except Exception as e:
        print(f"Keycloak login error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng",
        )