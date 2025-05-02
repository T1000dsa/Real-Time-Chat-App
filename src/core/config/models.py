from pydantic import BaseModel, field_validator

class RunConfig(BaseModel):
    """
    host:str default - 127.0.0.1
    port:int default - 8000
    """
    host:str = '127.0.0.1'
    port:int = 8000

class ApiPrefix_V1(BaseModel):
    """
    prefix:str default - /auth
    """
    prefix:str='/auth'

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

class CurrentDB(BaseModel):
    database:str = 'postgres'

class DatabaseConfig(BaseModel): 
    echo: bool = True
    echo_pool: bool = False
    pool_size: int = 5
    max_overflow: int = 10

    name: str
    user: str
    password: str
    host: str = 'localhost'
    port: int = 5432

    database:CurrentDB = CurrentDB()

    @property
    def give_url(self):
        current_db = self.database.database.lower() 

        if current_db == 'postgres':
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
        if current_db == 'mysql':
            return f"mysql+asyncmy://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        
        if current_db == 'mongodb':
            return f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        
        if current_db == 'mariadb':
            return f"mariadb+asyncmy://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        
        # Default case if database type is not recognized
        raise ValueError(f"Unsupported database type: {current_db}")