from pydantic import BaseModel, EmailStr, ConfigDict

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserResponse(BaseModel):
    user_id : str
    email : EmailStr
    name : str
    device_token: str | None = None
    notifications_enabled: bool = True

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    name : str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class MessageResponse(BaseModel):
    message: str


class DeviceTokenUpdate(BaseModel):
    device_token : str | None = None

class UserUpdate(BaseModel):
    name : str | None = None
    password : str | None = None
    notifications_enabled: bool | None = None
