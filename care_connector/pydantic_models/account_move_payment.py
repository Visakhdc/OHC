from pydantic import BaseModel, Field, field_validator
from enum import Enum
from .res_partner import PartnerData

class JournalType(Enum):
    cash = 'cash'
    bank = 'bank'

class PartnerType(Enum):
    vendor = 'vendor'
    customer = 'customer'

class AccountMovePaymentApiRequest(BaseModel):
    x_care_id: str
    journal_x_care_id: str
    amount: float = 0.0
    journal_input : JournalType
    payment_date : str
    partner_type : PartnerType
    partner_data: PartnerData