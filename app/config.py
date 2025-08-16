from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openhands_base_url: str = "http://34.40.104.64:3020"
    openhands_token: str | None = None
    database_url: str = "sqlite:///./runner.db"
    poll_min_seconds: int = 3
    poll_max_seconds: int = 20
    github_webhook_secret: str | None = None
    exposed_base_url: str | None = None
    log_level: str = "INFO"
    
    class Config:
        env_prefix = ""
        case_sensitive = False
        env_file = ".env"

settings = Settings()