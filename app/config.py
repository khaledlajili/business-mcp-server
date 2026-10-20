from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://northstar:northstar@localhost:5433/northstar"
    internal_api_token: str = "dev-internal-token"
    mcp_read_token: str = "dev-read-token"
    mcp_write_token: str = "dev-write-token"
    demo_api_key: str = "demo-key-change-me"
    mcp_public_url: str = "http://127.0.0.1:8000/mcp"
    port: int = 8000
    environment: str = "development"


settings = Settings()
