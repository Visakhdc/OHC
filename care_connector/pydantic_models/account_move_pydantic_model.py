from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from enum import Enum
from datetime import date


class PartnerType(Enum):
    person = 'person'
    company = 'company'

class PartnerData(BaseModel):
    name: str
    x_care_id: str = Field(..., description="Partner unique care ID")
    email: str
    phone: str
    state: str
    partner_type: PartnerType = Field(..., description="Check company or person")

class Product_data(BaseModel):
    product_name : str
    x_care_id: str = Field(..., description="Product unique care ID")
    cost:float = 0.0
    mrp:float = 0.0
    category: str

class InvoiceItem(BaseModel):
    product_data:  Product_data = Field(..., description="Product details including product_name, x_care_id,cost,mrp,tax and category")
    quantity: float = 1.0
    sale_price: float = 0.0
    tax: Optional[float] = 0.0
    x_care_id: str = Field(..., description="account move line unique care ID")

class Bill_Type(Enum):
    vendor = 'vendor'
    customer = 'customer'


class AccountMoveApiRequest(BaseModel):
    x_care_id: str = Field(..., description="account move unique care ID")
    bill_type: Bill_Type = Field(..., description="Check customer invoice or vendor bill")
    invoice_date: str = Field(..., description="Invoice creation date (format: YYYY-MM-DD)")
    due_date : str = Field(..., description="Invoice due date (format: YYYY-MM-DD)")
    partner_data: PartnerData = Field(..., description="Partner details including name, email, and phone")
    invoice_items: List[InvoiceItem] = Field(..., description="Account Move Line details including product details, quantity, sale price, sale tax, and x_care_id")
    reason: str = Field(..., description="Return reason")


class Journal_Type(Enum):
    cash = 'cash'
    bank = 'bank'

class AccountMovePaymentApiRequest(BaseModel):
    x_care_id: str = Field(..., description="account move unique care ID")
    amount: float = 0.0
    journal_input : Journal_Type = Field(..., description="Payment mode Cash/Bank")
    payment_date : str = Field(..., description="Payment date (format: YYYY-MM-DD)")