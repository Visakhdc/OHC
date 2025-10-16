from pydantic import BaseModel
from enum import Enum


class PartnerType(Enum):
    person = 'person'
    company = 'company'

class PartnerData(BaseModel):
    name: str
    x_care_id: str
    email: str
    phone: str
    state: str
    partner_type: PartnerType