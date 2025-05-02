from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path 
from fastapi.templating import Jinja2Templates

from src.core.config.models import (
    RunConfig, 
    Current_ApiPrefix,
    Mode, 
    DatabaseConfig, 
    RedisSettings, 
    )


base_dir = Path(__file__).parent.parent.parent
frontend_root = base_dir / 'frontend' / 'templates'
templates = Jinja2Templates(directory=frontend_root)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        env_prefix='FAST__',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    run: RunConfig = RunConfig()  # Keep defaults as fallback
    prefix: Current_ApiPrefix = Current_ApiPrefix()
    mode: Mode = Mode()
    db: DatabaseConfig
    redis_settings: RedisSettings = RedisSettings()
    #elastic:ElasticSearch = ElasticSearch()
    #email:Email_Settings = Email_Settings()


settings = Settings()
if settings.mode.mode not in ('DEV', 'TEST'):
    raise Exception('mode should be DEV or TEST')