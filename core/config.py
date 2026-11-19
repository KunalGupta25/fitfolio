from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    database_url: str = "./fitfolio.db"
    tectonic_path: str = "tectonic"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    output_dir: str = "./latex/output"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
