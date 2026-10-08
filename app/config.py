from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_api_key: str
    deepseek_model: str = "deepseek-flash"
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")
  
settings = Settings()
