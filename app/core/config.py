# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # → Tell Pydantic where to find your .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # MongoDB
    mongo_uri: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080

    # mail.ru SMTP
    mail_host: str
    mail_port: int
    mail_username: str
    mail_password: str

    # llama ai model
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"


# create your single shared settings instance
settings = Settings()
