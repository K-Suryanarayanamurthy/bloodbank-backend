from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "bloodbank_db"

    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440   # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email (Brevo)
    BREVO_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@bloodbank.com"
    FROM_NAME: str = "BloodBank"

    # OTP
    OTP_EXPIRE_MINUTES: int = 10

    class Config:
        env_file = ".env"

settings = Settings()
