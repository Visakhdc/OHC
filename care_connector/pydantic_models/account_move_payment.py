from pydantic import BaseModel, Field, field_validator
from enum import Enum
from .res_partner import PartnerData

class JournalType(Enum):
    cash = 'cash'
    bank = 'bank'

class PaymentMode(Enum):
    send = 'send'
    receive = 'receive'

class AccountMovePaymentApiRequest(BaseModel):
    x_care_id: str
    journal_x_care_id: str | None = None
    amount: float = 0.0
    journal_input : JournalType
    payment_date : str
    payment_mode : PaymentMode
    partner_data: PartnerData