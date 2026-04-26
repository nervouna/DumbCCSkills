from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "", "case_sensitive": False}

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"


settings = Settings()
