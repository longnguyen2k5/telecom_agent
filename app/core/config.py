from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    
    keycloak_url: str = "http://localhost:8080"
    realm_name: str = "TelecomAgent"
    client_id: str
    client_secret: str
    admin_client_id: str
    admin_client_secret: str
    pass_local_test: str
    keycloak_callback_url: str = "http://localhost:5173/callback"
    @field_validator("keycloak_url")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")
settings = Settings()