import asyncio
from app.core.auth import keycloak

async def main():
    try:
        # According to fastapi-keycloak docs, the method is usually user_login
        token = await keycloak.user_login(username="long_nguyen", password="12345678")
        print(token)
    except Exception as e:
        print("Error with user_login:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
