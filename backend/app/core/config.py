from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "LawyerIR SEO OS"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/lawyerir_seo"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    LAWYERIR_SITE_URL: str = "https://lawyerir.com"
    OPENAI_API_KEY: str = ""
    SECRET_KEY: str = "change-me-in-production"

    class Config:
        env_file = ".env"


settings = Settings()
