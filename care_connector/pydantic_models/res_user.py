from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from .res_partner import PartnerData

class UserType(str, Enum):
    portal = "portal"
    internal = "internal"

class UserData(BaseModel):
    name: str
    login: str
    password: str
    email: EmailStr
    user_type: UserType
    partner_data: PartnerData
