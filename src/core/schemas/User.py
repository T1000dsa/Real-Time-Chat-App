from pydantic import BaseModel, field_validator, model_validator
from typing import Optional

class UserSchema(BaseModel):
    username:str
    password:str
    password_again:str
    is_active:bool

    public_name:Optional[str]
    mail:Optional[str]
    bio:Optional[str]

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.password_again:
            raise ValueError("Passwords do not match")
        return self