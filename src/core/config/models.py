from pydantic import BaseModel, field_validator, SecretStr, EmailStr


class RunConfig(BaseModel):
    """
    host:str default - 0.0.0.0
    port:int default - 8000
    """
    host:str = '0.0.0.0'
    port:int = 8000
    title:str = 'real-time chat proj'

class ApiPrefix_V1(BaseModel):
    """
    prefix:str default - /v1
    """
    prefix:str='/v1'

class Current_ApiPrefix(BaseModel):
    api_data:ApiPrefix_V1 = ApiPrefix_V1()

class Mode(BaseModel):
    """
    mode:str default - DEV
    """
    mode:str = 'DEV'
    
    @field_validator('mode')
    def validate_mode(cls, v):
        if v not in ('DEV', 'TEST', 'PROD'):
            raise ValueError("Mode must be DEV, TEST or PROD")
        return v
    
class RedisSettings(BaseModel):
    host:str = 'localhost'
    port:int = 6379
    db:int = 0
    cache_time:int = 1
    cache_time_auth:int = 1
    cache_auth_attempts:int = 5

class CurrentDB(BaseModel):
    database:str = 'postgres'

class DatabaseConfig(BaseModel): 
    echo: bool = True
    echo_pool: bool = False
    pool_size: int = 5
    max_overflow: int = 10

    name: str
    user: str
    password: SecretStr
    host: str = 'localhost'
    port: int = 5432

    database:CurrentDB = CurrentDB()

    @property
    def give_url(self):
        current_db = self.database.database.lower() 
        decoded_pass = self.password.get_secret_value()

        if current_db == 'postgres':
            return f"postgresql+asyncpg://{self.user}:{decoded_pass}@{self.host}:{self.port}/{self.name}"
    
        if current_db == 'mysql':
            return f"mysql+asyncmy://{self.user}:{decoded_pass}@{self.host}:{self.port}/{self.name}"
        
        if current_db == 'mongodb':
            return f"mongodb://{self.user}:{decoded_pass}@{self.host}:{self.port}/{self.name}"
        
        if current_db == 'mariadb':
            return f"mariadb+asyncmy://{self.user}:{decoded_pass}@{self.host}:{self.port}/{self.name}"
        
        # Default case if database type is not recognized
        raise ValueError(f"Unsupported database type: {current_db}")
    

class Email_Settings(BaseModel):
    # Email Configuration
    EMAIL_ENABLED: bool = False
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: SecretStr = ""
    EMAIL_PASSWORD: SecretStr
    EMAIL_FROM: SecretStr = ""
    EMAIL_USE_TLS: bool = True
    EMAIL_TIMEOUT: int = 10


class JwtConfig(BaseModel):
    key:SecretStr = 'base_key'
    algorithm:str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES:int = 15
    REFRESH_TOKEN_EXPIRE_DAYS:int = 7