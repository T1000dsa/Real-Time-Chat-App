from pydantic import BaseModel, field_validator, model_validator
from typing import Optional


class UserBase(BaseModel):
    login:str
    password:str

class UserSchema(UserBase):
    password_again:str
    
    email:Optional[str] = None

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.password_again:
            raise ValueError("Passwords do not match")
        return self