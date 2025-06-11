from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path 
from fastapi.templating import Jinja2Templates
import os

from src.core.config.models import (
    RunConfig, 
    Current_ApiPrefix,
    Mode, 
    DatabaseConfig, 
    RedisSettings, 
    Email_Settings,
    JwtConfig
    )


"""base_dir = Path(__file__).parent.parent.parent
frontend_root = base_dir / 'frontend' / 'templates'
static_root = base_dir / 'frontend' / 'static'
templates = Jinja2Templates(directory=frontend_root)

media_root = base_dir / 'media'
default_picture_none =  '/media/Not_exist.png'
max_file_size = 10 * 1024**2 # 10 mb

os.makedirs(frontend_root, exist_ok=True)
os.makedirs(static_root, exist_ok=True)
os.makedirs(media_root, exist_ok=True)"""

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        env_prefix='FAST__',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # Run config
    run: RunConfig
    prefix: Current_ApiPrefix = Current_ApiPrefix()
    mode: Mode

    # Services
    db: DatabaseConfig
    jwt:JwtConfig
    redis: RedisSettings
    email:Email_Settings

    # API
    #...

    #elastic:ElasticSearch = ElasticSearch()

    def is_prod(self):
        if self.mode.mode == 'PROD':
            return True
        return False
    
    def create_directories(self):
        """Ensure required directories exist"""
        directories = [
            self.frontend_root,
            self.static_root,
            self.media_root
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    @property
    def base_dir(self) -> Path:
        return Path(__file__).parent.parent.parent
    
    @property
    def frontend_root(self) -> Path:
        return self.base_dir / 'frontend' / 'templates'
    
    @property
    def static_root(self) -> Path:
        return self.base_dir / 'frontend' / 'static'
    
    @property
    def media_root(self) -> Path:
        return self.base_dir / 'media'
    
    @property
    def default_picture_none(self) -> Path:
        return 'Not_exist.png'

settings = Settings()

frontend_root = settings.frontend_root
static_root = settings.static_root
templates = Jinja2Templates(directory=frontend_root)

media_root = settings.media_root
default_picture_none = settings.default_picture_none
max_file_size = 10 * 1024**2 # 10 mb

main_prefix = settings.prefix.api_data.prefix


if settings.mode.mode not in ('DEV', 'TEST'):
    raise Exception('mode should be DEV or TEST')