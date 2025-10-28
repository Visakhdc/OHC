from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
from .res_partner import PartnerData
from .product_product import ProductData


class InvoiceItem(BaseModel):
    product_data:  ProductData
    quantity: float = 1.0
    sale_price: float = 0.0
    tax: Optional[float] = 0.0
    x_care_id: str
    agent_id: Optional[str] = None


class BillType(Enum):
    vendor = 'vendor'
    customer = 'customer'


class AccountMoveApiRequest(BaseModel):
    x_care_id: str
    bill_type: BillType
    invoice_date: str
    due_date : str
    partner_data: PartnerData
    invoice_items: List[InvoiceItem]
    reason: Optional[str] = None

    @field_validator('x_care_id', 'partner_data', 'invoice_items')
    @classmethod
    def check_not_empty(cls, field_value):
        if not field_value:
            raise ValueError('Field cannot be empty')
        return field_value

