from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    app_name: str = "RAG Enterprise Lab"
    log_level: str = "INFO"

    database_url: str = ""
    r2_endpoint: str = ""
    r2_bucket: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""

    identity_mode: str = "mock"
    oidc_issuer: str = ""
    oidc_audience: str = ""

    claude_api_key: str = ""

    jev_enabled: bool = False
    jev_api_key: str = ""
    jev_base_url: str = ""

    local_corpus_allowed: bool = False
    max_local_sample_mb: int = 100

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
